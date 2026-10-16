package clusterworkflowtemplate

// Injected security/functional tests (ClusterWorkflowTemplate read authorization).
// Reading a cluster-scoped WorkflowTemplate through the API must be gated by a
// per-caller access-review, exactly like the namespaced variant.

import (
	"context"
	"testing"

	"github.com/go-jose/go-jose/v3/jwt"
	authorizationv1 "k8s.io/api/authorization/v1"
	"k8s.io/apimachinery/pkg/runtime"
	kubefake "k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"

	clusterwftmplpkg "github.com/argoproj/argo-workflows/v4/pkg/apiclient/clusterworkflowtemplate"
	"github.com/argoproj/argo-workflows/v4/pkg/apis/workflow/v1alpha1"
	wftFake "github.com/argoproj/argo-workflows/v4/pkg/client/clientset/versioned/fake"
	"github.com/argoproj/argo-workflows/v4/server/auth"
	"github.com/argoproj/argo-workflows/v4/server/auth/types"
	"github.com/argoproj/argo-workflows/v4/util/instanceid"
	"github.com/argoproj/argo-workflows/v4/util/logging"
)

const zzCwftJSON = `{
  "apiVersion": "argoproj.io/v1alpha1",
  "kind": "ClusterWorkflowTemplate",
  "metadata": {
    "name": "zz-cwftmpl",
    "labels": {"workflows.argoproj.io/controller-instanceid": "zz-instanceid"}
  },
  "spec": {"templates": [{"name": "main", "container": {"image": "argoproj/argosay:v2"}}]}
}`

func zzCwtServer(t *testing.T, allowed bool) (clusterwftmplpkg.ClusterWorkflowTemplateServiceServer, context.Context) {
	t.Helper()
	var cwft v1alpha1.ClusterWorkflowTemplate
	v1alpha1.MustUnmarshal(zzCwftJSON, &cwft)
	kube := kubefake.NewSimpleClientset()
	// Behave like real RBAC (2026-10-16 repair): `allowed` decides whether the caller may READ
	// (get/list/watch) clusterworkflowtemplates cluster-wide. Every other resource or verb is
	// permitted. The caller is also an administrator of some namespace (a wildcard Role there),
	// so a namespaced review of this cluster-scoped resource is granted by that Role, as real
	// RBAC does; only a cluster-scope review protects it. A wrong resource does not either.
	kube.PrependReactor("create", "selfsubjectaccessreviews", func(action k8stesting.Action) (bool, runtime.Object, error) {
		ok := true
		if ca, isCreate := action.(k8stesting.CreateAction); isCreate {
			if review, isReview := ca.GetObject().(*authorizationv1.SelfSubjectAccessReview); isReview {
				if ra := review.Spec.ResourceAttributes; ra != nil && ra.Resource == "clusterworkflowtemplates" && ra.Namespace == "" {
					switch ra.Verb {
					case "get", "list", "watch", "*":
						ok = allowed
					}
				}
			}
		}
		return true, &authorizationv1.SelfSubjectAccessReview{
			Status: authorizationv1.SubjectAccessReviewStatus{Allowed: ok},
		}, nil
	})
	wfClient := wftFake.NewSimpleClientset(&cwft)
	ctx := context.WithValue(logging.TestContext(t.Context()), auth.WfKey, wfClient)
	ctx = context.WithValue(ctx, auth.KubeKey, kube)
	ctx = context.WithValue(ctx, auth.ClaimsKey, &types.Claims{Claims: jwt.Claims{Subject: "attacker"}, Email: "attacker@evil.example"})
	return NewClusterWorkflowTemplateServer(instanceid.NewService("zz-instanceid"), nil, nil), ctx
}

func TestSecZZClusterWorkflowTemplateGetRequiresAuthz(t *testing.T) {
	server, ctx := zzCwtServer(t, false)
	tmpl, err := server.GetClusterWorkflowTemplate(ctx, &clusterwftmplpkg.ClusterWorkflowTemplateGetRequest{
		Name: "zz-cwftmpl",
	})
	// Any refusal counts (2026-10-16: no one exact code), as long as no template body is returned.
	if err == nil {
		t.Fatalf("unauthorised GetClusterWorkflowTemplate was not refused (template returned: %v)", tmpl != nil)
	}
	if tmpl != nil && len(tmpl.Spec.Templates) > 0 {
		t.Fatalf("unauthorised GetClusterWorkflowTemplate returned the template body alongside its error")
	}
}

func TestFuncZZClusterWorkflowTemplateGetAuthorised(t *testing.T) {
	server, ctx := zzCwtServer(t, true)
	tmpl, err := server.GetClusterWorkflowTemplate(ctx, &clusterwftmplpkg.ClusterWorkflowTemplateGetRequest{
		Name: "zz-cwftmpl",
	})
	if err != nil {
		t.Fatalf("authorised GetClusterWorkflowTemplate failed: %v", err)
	}
	if tmpl == nil || tmpl.Name != "zz-cwftmpl" {
		t.Fatalf("expected template zz-cwftmpl, got %v", tmpl)
	}
}
