package controller

// Injected security/functional tests (template-referencing restriction bypass).
// When the controller is configured so that workflows MUST reference a
// WorkflowTemplate (Strict/Secure mode), a submitted workflow must not be able
// to set pod-level security fields that would override the referenced
// template's protections. Legitimate referencing workflows must still run, and
// the pre-existing podSpecPatch protection must be preserved.

import (
	"testing"

	apiv1 "k8s.io/api/core/v1"

	"github.com/argoproj/argo-workflows/v4/config"
	wfv1 "github.com/argoproj/argo-workflows/v4/pkg/apis/workflow/v1alpha1"
	"github.com/argoproj/argo-workflows/v4/util/logging"
)

func zzRefWf(t *testing.T) *wfv1.Workflow {
	t.Helper()
	return wfv1.MustUnmarshalWorkflow("@testdata/workflow-template-ref.yaml")
}

func zzRefWfTmpl(t *testing.T) *wfv1.WorkflowTemplate {
	t.Helper()
	return wfv1.MustUnmarshalWorkflowTemplate("@testdata/workflow-template-submittable.yaml")
}

// zzOperateSecure runs the given (mutated) referencing workflow under Secure
// template-referencing restriction and returns the resulting workflow phase.
func zzOperateSecure(t *testing.T, mutate func(wf *wfv1.Workflow)) wfv1.WorkflowPhase {
	t.Helper()
	wf := zzRefWf(t)
	mutate(wf)
	ctx := logging.TestContext(t.Context())
	cancel, controller := newController(ctx, wf, zzRefWfTmpl(t))
	defer cancel()
	controller.Config.WorkflowRestrictions = &config.WorkflowRestrictions{
		TemplateReferencing: config.TemplateReferencingSecure,
	}
	woc := newWorkflowOperationCtx(ctx, wf, controller)
	woc.operate(ctx)
	return woc.wf.Status.Phase
}

func TestSecZZRefModeRejectsHostNetwork(t *testing.T) {
	hostNet := true
	phase := zzOperateSecure(t, func(wf *wfv1.Workflow) { wf.Spec.HostNetwork = &hostNet })
	if phase != wfv1.WorkflowError {
		t.Fatalf("workflow overriding hostNetwork was not rejected: phase=%s", phase)
	}
}

func TestSecZZRefModeRejectsServiceAccount(t *testing.T) {
	phase := zzOperateSecure(t, func(wf *wfv1.Workflow) { wf.Spec.ServiceAccountName = "privileged-sa" })
	if phase != wfv1.WorkflowError {
		t.Fatalf("workflow overriding serviceAccountName was not rejected: phase=%s", phase)
	}
}

func TestSecZZRefModeRejectsSecurityContext(t *testing.T) {
	runAsRoot := int64(0)
	phase := zzOperateSecure(t, func(wf *wfv1.Workflow) {
		wf.Spec.SecurityContext = &apiv1.PodSecurityContext{RunAsUser: &runAsRoot}
	})
	if phase != wfv1.WorkflowError {
		t.Fatalf("workflow overriding securityContext was not rejected: phase=%s", phase)
	}
}

// The same pod security context can be set for every template of the referencing workflow
// through its template defaults; that is still a pod-level override and must be rejected too
// (2026-10-16 repair).
func TestSecZZRefModeRejectsTemplateDefaultsSecurityContext(t *testing.T) {
	runAsRoot := int64(0)
	phase := zzOperateSecure(t, func(wf *wfv1.Workflow) {
		wf.Spec.TemplateDefaults = &wfv1.Template{
			SecurityContext: &apiv1.PodSecurityContext{RunAsUser: &runAsRoot},
		}
	})
	if phase != wfv1.WorkflowError {
		t.Fatalf("workflow overriding the pod securityContext via templateDefaults was not rejected: phase=%s", phase)
	}
}

// Functional: a legitimate referencing workflow that overrides nothing must run.
func TestFuncZZRefModeLegitWorkflowRuns(t *testing.T) {
	phase := zzOperateSecure(t, func(wf *wfv1.Workflow) {})
	if phase != wfv1.WorkflowRunning {
		t.Fatalf("legitimate referencing workflow did not run: phase=%s", phase)
	}
}

// Functional: the pre-existing podSpecPatch protection must still hold.
func TestFuncZZRefModePodSpecPatchStillRejected(t *testing.T) {
	wf := zzRefWf(t)
	wf.Spec.PodSpecPatch = `{"containers":[{"name":"main","securityContext":{"privileged":true}}]}`
	ctx := logging.TestContext(t.Context())
	cancel, controller := newController(ctx, wf, zzRefWfTmpl(t))
	defer cancel()
	controller.Config.WorkflowRestrictions = &config.WorkflowRestrictions{
		TemplateReferencing: config.TemplateReferencingStrict,
	}
	woc := newWorkflowOperationCtx(ctx, wf, controller)
	woc.operate(ctx)
	if woc.wf.Status.Phase != wfv1.WorkflowError {
		t.Fatalf("podSpecPatch was not rejected under restriction: phase=%s", woc.wf.Status.Phase)
	}
}
