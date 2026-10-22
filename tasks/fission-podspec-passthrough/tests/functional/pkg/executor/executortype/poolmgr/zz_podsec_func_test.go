package poolmgr

// Hidden functional tests: tenant pod customisation and the operator's
// runtime pod-spec patch keep reaching the pool deployment.

import (
	"testing"

	apiv1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	fv1 "github.com/fission/fission/pkg/apis/core/v1"
	fetcherConfig "github.com/fission/fission/pkg/fetcher/config"
	"github.com/fission/fission/pkg/utils/loggerfactory"
)

func zzFnBool(b bool) *bool  { return &b }
func zzFnInt(i int64) *int64 { return &i }

func zzFnPool(t *testing.T, patch *apiv1.PodSpec) *GenericPool {
	t.Helper()
	cfg, err := fetcherConfig.MakeFetcherConfig("/userfunc")
	if err != nil {
		t.Fatal(err)
	}
	return &GenericPool{logger: loggerfactory.GetLogger(), fetcherConfig: cfg, podSpecPatch: patch}
}

func zzFnEnv() *fv1.Environment {
	return &fv1.Environment{
		ObjectMeta: metav1.ObjectMeta{Name: "py", Namespace: "tenant-a"},
		Spec: fv1.EnvironmentSpec{
			Version: 2,
			Runtime: fv1.Runtime{Image: "fission/python-env:latest"},
		},
	}
}

func zzFnContainer(ps *apiv1.PodSpec, name string) *apiv1.Container {
	for i := range ps.Containers {
		if ps.Containers[i].Name == name {
			return &ps.Containers[i]
		}
	}
	return nil
}

func zzFnHasCap(sc *apiv1.SecurityContext, c apiv1.Capability) bool {
	if sc == nil || sc.Capabilities == nil {
		return false
	}
	for _, x := range sc.Capabilities.Add {
		if x == c {
			return true
		}
	}
	return false
}

func TestFuncZZPoolTenantPodSpecCustomisation(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.PodSpec = &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{
			RunAsNonRoot: zzFnBool(true), RunAsUser: zzFnInt(10001), FSGroup: zzFnInt(10001),
			SeccompProfile: &apiv1.SeccompProfile{Type: apiv1.SeccompProfileTypeRuntimeDefault},
		},
		NodeSelector: map[string]string{"pool": "functions"},
		Tolerations:  []apiv1.Toleration{{Key: "dedicated", Operator: apiv1.TolerationOpEqual, Value: "functions", Effect: apiv1.TaintEffectNoSchedule}},
		Volumes: []apiv1.Volume{{Name: "settings", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
			LocalObjectReference: apiv1.LocalObjectReference{Name: "py-settings"}}}}},
		Containers: []apiv1.Container{{
			Name: "helper", Image: "busybox:1.36", Command: []string{"sleep", "3600"},
			SecurityContext: &apiv1.SecurityContext{
				AllowPrivilegeEscalation: zzFnBool(false),
				Capabilities:             &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"NET_BIND_SERVICE"}},
			},
			VolumeMounts: []apiv1.VolumeMount{{Name: "settings", MountPath: "/etc/settings"}},
		}},
	}
	spec, err := zzFnPool(t, nil).genDeploymentSpec(env)
	if err != nil {
		t.Fatalf("genDeploymentSpec: %v", err)
	}
	ps := &spec.Template.Spec
	if ps.ServiceAccountName != "fission-fetcher" {
		t.Errorf("pool pods should run as the platform's fetcher account, got %q", ps.ServiceAccountName)
	}
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsNonRoot == nil || !*ps.SecurityContext.RunAsNonRoot ||
		ps.SecurityContext.RunAsUser == nil || *ps.SecurityContext.RunAsUser != 10001 ||
		ps.SecurityContext.FSGroup == nil || *ps.SecurityContext.FSGroup != 10001 {
		t.Errorf("pod security context hardening not applied: %+v", ps.SecurityContext)
	}
	if ps.NodeSelector["pool"] != "functions" {
		t.Errorf("node selector not applied: %v", ps.NodeSelector)
	}
	found := false
	for _, tol := range ps.Tolerations {
		found = found || tol.Key == "dedicated"
	}
	if !found {
		t.Errorf("toleration not applied: %v", ps.Tolerations)
	}
	found = false
	for _, v := range ps.Volumes {
		found = found || (v.Name == "settings" && v.ConfigMap != nil)
	}
	if !found {
		t.Errorf("configMap volume not applied: %v", ps.Volumes)
	}
	h := zzFnContainer(ps, "helper")
	if h == nil {
		t.Fatalf("helper container missing")
	}
	if !zzFnHasCap(h.SecurityContext, "NET_BIND_SERVICE") {
		t.Errorf("NET_BIND_SERVICE capability dropped from helper: %+v", h.SecurityContext)
	}
	if zzFnContainer(ps, "py") == nil {
		t.Errorf("runtime container missing")
	}
}

func TestFuncZZPoolRuntimeContainerCustomisation(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.Container = &apiv1.Container{
		Env: []apiv1.EnvVar{{Name: "LOG_LEVEL", Value: "debug"}},
		Resources: apiv1.ResourceRequirements{Limits: apiv1.ResourceList{
			apiv1.ResourceMemory: resource.MustParse("256Mi")}},
		SecurityContext: &apiv1.SecurityContext{
			RunAsNonRoot:             zzFnBool(true),
			ReadOnlyRootFilesystem:   zzFnBool(true),
			AllowPrivilegeEscalation: zzFnBool(false),
			Capabilities:             &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"NET_BIND_SERVICE"}},
		},
	}
	spec, err := zzFnPool(t, nil).genDeploymentSpec(env)
	if err != nil {
		t.Fatalf("genDeploymentSpec: %v", err)
	}
	c := zzFnContainer(&spec.Template.Spec, "py")
	if c == nil {
		t.Fatalf("runtime container missing")
	}
	hasEnv := false
	for _, e := range c.Env {
		hasEnv = hasEnv || (e.Name == "LOG_LEVEL" && e.Value == "debug")
	}
	if !hasEnv {
		t.Errorf("runtime container env not applied: %v", c.Env)
	}
	if q := c.Resources.Limits[apiv1.ResourceMemory]; q.String() != "256Mi" {
		t.Errorf("memory limit not applied: %v", c.Resources.Limits)
	}
	sc := c.SecurityContext
	if sc == nil || sc.RunAsNonRoot == nil || !*sc.RunAsNonRoot || sc.ReadOnlyRootFilesystem == nil || !*sc.ReadOnlyRootFilesystem {
		t.Errorf("runtime container hardening not applied: %+v", sc)
	}
	if !zzFnHasCap(sc, "NET_BIND_SERVICE") {
		t.Errorf("NET_BIND_SERVICE capability dropped: %+v", sc)
	}
}

func TestFuncZZPoolOperatorPatch(t *testing.T) {
	patch := &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{
			RunAsNonRoot: zzFnBool(true), RunAsUser: zzFnInt(10001), RunAsGroup: zzFnInt(10001), FSGroup: zzFnInt(10001),
		},
		NodeSelector:      map[string]string{"node-role": "fission"},
		Tolerations:       []apiv1.Toleration{{Key: "fission", Operator: apiv1.TolerationOpExists}},
		PriorityClassName: "fission-functions",
	}
	spec, err := zzFnPool(t, patch).genDeploymentSpec(zzFnEnv())
	if err != nil {
		t.Fatalf("genDeploymentSpec: %v", err)
	}
	ps := &spec.Template.Spec
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsUser == nil || *ps.SecurityContext.RunAsUser != 10001 ||
		ps.SecurityContext.FSGroup == nil || *ps.SecurityContext.FSGroup != 10001 ||
		ps.SecurityContext.RunAsNonRoot == nil || !*ps.SecurityContext.RunAsNonRoot {
		t.Errorf("operator pod security context not applied: %+v", ps.SecurityContext)
	}
	if ps.NodeSelector["node-role"] != "fission" || ps.PriorityClassName != "fission-functions" {
		t.Errorf("operator scheduling settings not applied: %v %q", ps.NodeSelector, ps.PriorityClassName)
	}
	if len(ps.Tolerations) == 0 {
		t.Errorf("operator toleration not applied")
	}
}
