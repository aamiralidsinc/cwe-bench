package workflowtemplate

// Injected security/functional tests (WorkflowTemplate read authorization).
// Reading a namespaced WorkflowTemplate through the API must be gated by a
// per-caller access-review; an unauthorised caller must be refused, while an
// authorised caller must still receive the template.

import (
	"context"
	"testing"

	"github.com/go-jose/go-jose/v3/jwt"
	authorizationv1 "k8s.io/api/authorization/v1"
	"k8s.io/apimachinery/pkg/runtime"
	kubefake "k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"

	workflowtemplatepkg "github.com/argoproj/argo-workflows/v4/pkg/apiclient/workflowtemplate"
	"github.com/argoproj/argo-workflows/v4/pkg/apis/workflow/v1alpha1"
	wftFake "github.com/argoproj/argo-workflows/v4/pkg/client/clientset/versioned/fake"
	"github.com/argoproj/argo-workflows/v4/server/auth"
	"github.com/argoproj/argo-workflows/v4/server/auth/types"
	"github.com/argoproj/argo-workflows/v4/util/instanceid"
	"github.com/argoproj/argo-workflows/v4/util/logging"
)

const zzWftJSON = `{
  "apiVersion": "argoproj.io/v1alpha1",
  "kind": "WorkflowTemplate",
  "metadata": {
    "name": "zz-wftmpl",
    "namespace": "default",
    "labels": {"workflows.argoproj.io/controller-instanceid": "zz-instanceid"}
  },
  "spec": {"templates": [{"name": "main", "container": {"image": "argoproj/argosay:v2"}}]}
}`

func zzWtServer(t *testing.T, allowed bool) (workflowtemplatepkg.WorkflowTemplateServiceServer, context.Context) {
	t.Helper()
	var wft v1alpha1.WorkflowTemplate
	v1alpha1.MustUnmarshal(zzWftJSON, &wft)
	kube := kubefake.NewSimpleClientset()
	// Behave like real namespaced RBAC (2026-10-16 repair): `allowed` decides whether the caller
	// may READ (get/list/watch) workflowtemplates in the template's namespace "default". Every
	// other resource or verb there, and everything in other namespaces (e.g. the caller's own),
	// is permitted; the caller holds no cluster-wide (all-namespace) rights on workflowtemplates.
	// So a check on the wrong resource or namespace does not protect the template.
	kube.PrependReactor("create", "selfsubjectaccessreviews", func(action k8stesting.Action) (bool, runtime.Object, error) {
		ok := true
		if ca, isCreate := action.(k8stesting.CreateAction); isCreate {
			if review, isReview := ca.GetObject().(*authorizationv1.SelfSubjectAccessReview); isReview {
				if ra := review.Spec.ResourceAttributes; ra != nil && ra.Resource == "workflowtemplates" {
					switch ra.Namespace {
					case "default":
						switch ra.Verb {
						case "get", "list", "watch", "*":
							ok = allowed
						}
					case "":
						ok = false
					}
				}
			}
		}
		return true, &authorizationv1.SelfSubjectAccessReview{
			Status: authorizationv1.SubjectAccessReviewStatus{Allowed: ok},
		}, nil
	})
	wfClient := wftFake.NewSimpleClientset(&wft)
	ctx := context.WithValue(logging.TestContext(t.Context()), auth.WfKey, wfClient)
	ctx = context.WithValue(ctx, auth.KubeKey, kube)
	ctx = context.WithValue(ctx, auth.ClaimsKey, &types.Claims{Claims: jwt.Claims{Subject: "attacker"}, Email: "attacker@evil.example"})
	return NewWorkflowTemplateServer(instanceid.NewService("zz-instanceid"), nil, nil), ctx
}

func TestSecZZWorkflowTemplateGetRequiresAuthz(t *testing.T) {
	server, ctx := zzWtServer(t, false)
	tmpl, err := server.GetWorkflowTemplate(ctx, &workflowtemplatepkg.WorkflowTemplateGetRequest{
		Namespace: "default", Name: "zz-wftmpl",
	})
	// Any refusal counts (2026-10-16: no one exact code), as long as no template body is returned.
	if err == nil {
		t.Fatalf("unauthorised GetWorkflowTemplate was not refused (template returned: %v)", tmpl != nil)
	}
	if tmpl != nil && len(tmpl.Spec.Templates) > 0 {
		t.Fatalf("unauthorised GetWorkflowTemplate returned the template body alongside its error")
	}
}

func TestFuncZZWorkflowTemplateGetAuthorised(t *testing.T) {
	server, ctx := zzWtServer(t, true)
	tmpl, err := server.GetWorkflowTemplate(ctx, &workflowtemplatepkg.WorkflowTemplateGetRequest{
		Namespace: "default", Name: "zz-wftmpl",
	})
	if err != nil {
		t.Fatalf("authorised GetWorkflowTemplate failed: %v", err)
	}
	if tmpl == nil || tmpl.Name != "zz-wftmpl" {
		t.Fatalf("expected template zz-wftmpl, got %v", tmpl)
	}
}
