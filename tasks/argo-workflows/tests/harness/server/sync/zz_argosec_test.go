package sync

// Injected security/functional tests (sync-limit ConfigMap access control).
// The sync-limit API edits ConfigMaps in arbitrary namespaces. Every verb must
// be gated by a Kubernetes access-review for the caller; an unauthorised caller
// must be refused, while an authorised caller must still succeed.

import (
	"context"
	"testing"

	authorizationv1 "k8s.io/api/authorization/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes"
	kubefake "k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"

	syncpkg "github.com/argoproj/argo-workflows/v4/pkg/apiclient/sync"
	"github.com/argoproj/argo-workflows/v4/server/auth"
	"github.com/argoproj/argo-workflows/v4/util/logging"
)

const (
	zzNS     = "victim-ns"  // the namespace whose limits are targeted
	zzHomeNS = "argo"       // the server's own namespace, where the caller has full rights
	zzCM     = "my-sync-config"
	zzKey    = "my-lock"
)

var (
	zzAllCMVerbs  = []string{"get", "list", "watch", "create", "update", "patch", "delete", "deletecollection"}
	zzReadCMVerbs = []string{"get", "list", "watch"}
)

// zzSyncCtx builds a sync server backed by a fake kube client whose access reviews behave
// like real namespaced RBAC (2026-10-16 repair):
//   - in the server's own namespace the caller may do everything;
//   - in the target namespace the caller may do everything except on ConfigMaps, where only
//     the verbs in cmVerbs are granted;
//   - the caller holds no cluster-wide (all-namespace) rights on ConfigMaps.
//
// So a check on the wrong resource, the wrong verb class or the wrong namespace does not
// protect the limits. A ConfigMap with an existing limit is pre-seeded so that, on code that
// performs no check, read/update/delete visibly succeed.
func zzSyncCtx(t *testing.T, cmVerbs []string) (syncpkg.SyncServiceServer, context.Context, kubernetes.Interface) {
	t.Helper()
	kube := kubefake.NewSimpleClientset(&corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: zzCM, Namespace: zzNS},
		Data:       map[string]string{zzKey: "5"},
	})
	granted := map[string]bool{}
	for _, v := range cmVerbs {
		granted[v] = true
	}
	kube.PrependReactor("create", "selfsubjectaccessreviews", func(action k8stesting.Action) (bool, runtime.Object, error) {
		ok := true
		if ca, isCreate := action.(k8stesting.CreateAction); isCreate {
			if review, isReview := ca.GetObject().(*authorizationv1.SelfSubjectAccessReview); isReview {
				if ra := review.Spec.ResourceAttributes; ra != nil && ra.Resource == "configmaps" {
					switch ra.Namespace {
					case zzHomeNS:
						ok = true
					case zzNS:
						ok = granted[ra.Verb] || (ra.Verb == "*" && len(granted) == len(zzAllCMVerbs))
					default:
						ok = false
					}
				}
			}
		}
		return true, &authorizationv1.SelfSubjectAccessReview{
			Status: authorizationv1.SubjectAccessReviewStatus{Allowed: ok},
		}, nil
	})
	ctx := context.WithValue(logging.TestContext(t.Context()), auth.KubeKey, kube)
	return NewSyncServer(ctx, kube, zzHomeNS, nil), ctx, kube
}

// zzLimitData reads the stored limits directly from the fake cluster (not through the API).
func zzLimitData(t *testing.T, kube kubernetes.Interface, name string) (map[string]string, bool) {
	t.Helper()
	cm, err := kube.CoreV1().ConfigMaps(zzNS).Get(context.Background(), name, metav1.GetOptions{})
	if err != nil {
		return nil, false
	}
	return cm.Data, true
}

// A caller with no rights on ConfigMaps in the target namespace cannot read its limits.
func TestSecZZSyncGetRequiresAuthz(t *testing.T) {
	server, ctx, _ := zzSyncCtx(t, nil)
	resp, err := server.GetSyncLimit(ctx, &syncpkg.GetSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: zzCM, Key: zzKey,
	})
	if err == nil {
		t.Fatalf("unauthorised GetSyncLimit was not refused: resp=%v", resp)
	}
	if resp != nil && resp.Limit == 5 {
		t.Fatalf("unauthorised GetSyncLimit disclosed the limit alongside its error: %v", resp)
	}
}

// A caller who may only read ConfigMaps in the target namespace cannot create a limit there.
func TestSecZZSyncCreateRequiresAuthz(t *testing.T) {
	server, ctx, kube := zzSyncCtx(t, zzReadCMVerbs)
	_, err := server.CreateSyncLimit(ctx, &syncpkg.CreateSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: "brand-new-cm", Key: zzKey, Limit: 3,
	})
	if err == nil {
		t.Fatalf("CreateSyncLimit by a caller without write rights was not refused")
	}
	if _, exists := zzLimitData(t, kube, "brand-new-cm"); exists {
		t.Fatalf("refused CreateSyncLimit still created the ConfigMap")
	}
}

// A caller who may only read ConfigMaps in the target namespace cannot change a limit there.
func TestSecZZSyncUpdateRequiresAuthz(t *testing.T) {
	server, ctx, kube := zzSyncCtx(t, zzReadCMVerbs)
	_, err := server.UpdateSyncLimit(ctx, &syncpkg.UpdateSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: zzCM, Key: zzKey, Limit: 99,
	})
	if err == nil {
		t.Fatalf("UpdateSyncLimit by a caller without write rights was not refused")
	}
	if data, _ := zzLimitData(t, kube, zzCM); data[zzKey] != "5" {
		t.Fatalf("refused UpdateSyncLimit still changed the limit: %v", data)
	}
}

// A caller who may only read ConfigMaps in the target namespace cannot remove a limit there.
func TestSecZZSyncDeleteRequiresAuthz(t *testing.T) {
	server, ctx, kube := zzSyncCtx(t, zzReadCMVerbs)
	_, err := server.DeleteSyncLimit(ctx, &syncpkg.DeleteSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: zzCM, Key: zzKey,
	})
	if err == nil {
		t.Fatalf("DeleteSyncLimit by a caller without write rights was not refused")
	}
	if data, _ := zzLimitData(t, kube, zzCM); data[zzKey] != "5" {
		t.Fatalf("refused DeleteSyncLimit still removed the limit: %v", data)
	}
}

// Functional: a caller authorised on ConfigMaps in the target namespace (and nowhere
// cluster-wide) can create and read back a sync limit.
func TestFuncZZSyncAuthorisedRoundTrip(t *testing.T) {
	server, ctx, _ := zzSyncCtx(t, zzAllCMVerbs)
	if _, err := server.CreateSyncLimit(ctx, &syncpkg.CreateSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: "fresh-cm", Key: "k", Limit: 7,
	}); err != nil {
		t.Fatalf("authorised CreateSyncLimit failed: %v", err)
	}
	resp, err := server.GetSyncLimit(ctx, &syncpkg.GetSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: "fresh-cm", Key: "k",
	})
	if err != nil {
		t.Fatalf("authorised GetSyncLimit failed: %v", err)
	}
	if resp.Limit != 7 {
		t.Fatalf("expected limit 7, got %d", resp.Limit)
	}
}

// Functional: an authorised caller can read a pre-existing limit.
func TestFuncZZSyncAuthorisedGet(t *testing.T) {
	server, ctx, _ := zzSyncCtx(t, zzAllCMVerbs)
	resp, err := server.GetSyncLimit(ctx, &syncpkg.GetSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: zzCM, Key: zzKey,
	})
	if err != nil {
		t.Fatalf("authorised GetSyncLimit failed: %v", err)
	}
	if resp.Limit != 5 {
		t.Fatalf("expected limit 5, got %d", resp.Limit)
	}
}

// Functional: an authorised caller can update and then remove a pre-existing limit.
func TestFuncZZSyncAuthorisedUpdateDelete(t *testing.T) {
	server, ctx, kube := zzSyncCtx(t, zzAllCMVerbs)
	if _, err := server.UpdateSyncLimit(ctx, &syncpkg.UpdateSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: zzCM, Key: zzKey, Limit: 9,
	}); err != nil {
		t.Fatalf("authorised UpdateSyncLimit failed: %v", err)
	}
	if data, _ := zzLimitData(t, kube, zzCM); data[zzKey] != "9" {
		t.Fatalf("authorised UpdateSyncLimit did not store the new limit: %v", data)
	}
	if _, err := server.DeleteSyncLimit(ctx, &syncpkg.DeleteSyncLimitRequest{
		Type: syncpkg.SyncConfigType_CONFIGMAP, Namespace: zzNS, CmName: zzCM, Key: zzKey,
	}); err != nil {
		t.Fatalf("authorised DeleteSyncLimit failed: %v", err)
	}
	if data, _ := zzLimitData(t, kube, zzCM); data != nil {
		if _, still := data[zzKey]; still {
			t.Fatalf("authorised DeleteSyncLimit did not remove the limit: %v", data)
		}
	}
}
