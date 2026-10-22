package newdeploy

// Hidden functional tests: tenant pod customisation and the operator's
// runtime pod-spec patch keep reaching the new-deploy function deployment.

import (
	"context"
	"testing"

	apiv1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	k8sfake "k8s.io/client-go/kubernetes/fake"

	fv1 "github.com/fission/fission/pkg/apis/core/v1"
	fetcherConfig "github.com/fission/fission/pkg/fetcher/config"
	"github.com/fission/fission/pkg/utils/loggerfactory"
)

func zzFnBool(b bool) *bool  { return &b }
func zzFnInt(i int64) *int64 { return &i }

func zzFnDeploy(t *testing.T, patch *apiv1.PodSpec) *NewDeploy {
	t.Helper()
	cfg, err := fetcherConfig.MakeFetcherConfig("/userfunc")
	if err != nil {
		t.Fatal(err)
	}
	return &NewDeploy{logger: loggerfactory.GetLogger(), kubernetesClient: k8sfake.NewSimpleClientset(),
		fetcherConfig: cfg, podSpecPatch: patch}
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

func zzFnFn() *fv1.Function {
	return &fv1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: "hello", Namespace: "tenant-a"},
		Spec: fv1.FunctionSpec{
			Environment: fv1.EnvironmentReference{Name: "py", Namespace: "tenant-a"},
			Package: fv1.FunctionPackageRef{PackageRef: fv1.PackageRef{
				Namespace: "tenant-a", Name: "hello-pkg", ResourceVersion: "1"}},
			InvokeStrategy: fv1.InvokeStrategy{
				StrategyType: fv1.StrategyTypeExecution,
				ExecutionStrategy: fv1.ExecutionStrategy{
					ExecutorType: fv1.ExecutorTypeNewdeploy,
					MinScale:     1,
					MaxScale:     2,
				},
			},
		},
	}
}

func zzFnSpec(t *testing.T, nd *NewDeploy, env *fv1.Environment) *apiv1.PodSpec {
	t.Helper()
	fn := zzFnFn()
	replicas := int32(1)
	depl, err := nd.getDeploymentSpec(context.Background(), fn, env, &replicas,
		"hello-zz", fn.Namespace, map[string]string{"functionName": fn.Name}, map[string]string{})
	if err != nil {
		t.Fatalf("getDeploymentSpec: %v", err)
	}
	return &depl.Spec.Template.Spec
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

func TestFuncZZNewDeployTenantCustomisation(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.PodSpec = &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{
			RunAsNonRoot: zzFnBool(true), RunAsUser: zzFnInt(10001), FSGroup: zzFnInt(10001),
		},
		NodeSelector: map[string]string{"pool": "functions"},
		Tolerations:  []apiv1.Toleration{{Key: "dedicated", Operator: apiv1.TolerationOpEqual, Value: "functions", Effect: apiv1.TaintEffectNoSchedule}},
		Volumes:      []apiv1.Volume{{Name: "scratch", VolumeSource: apiv1.VolumeSource{EmptyDir: &apiv1.EmptyDirVolumeSource{}}}},
		Containers: []apiv1.Container{{
			Name: "helper", Image: "busybox:1.36", Command: []string{"sleep", "3600"},
			SecurityContext: &apiv1.SecurityContext{
				Privileged:               zzFnBool(false),
				AllowPrivilegeEscalation: zzFnBool(false),
				Capabilities:             &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"NET_BIND_SERVICE"}},
			},
			VolumeMounts: []apiv1.VolumeMount{{Name: "scratch", MountPath: "/scratch"}},
		}},
	}
	env.Spec.Runtime.Container = &apiv1.Container{
		Env: []apiv1.EnvVar{{Name: "LOG_LEVEL", Value: "debug"}},
		Resources: apiv1.ResourceRequirements{Limits: apiv1.ResourceList{
			apiv1.ResourceMemory: resource.MustParse("256Mi")}},
		SecurityContext: &apiv1.SecurityContext{
			RunAsNonRoot:           zzFnBool(true),
			ReadOnlyRootFilesystem: zzFnBool(true),
			Capabilities:           &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"CHOWN"}},
		},
	}
	ps := zzFnSpec(t, zzFnDeploy(t, nil), env)
	if ps.ServiceAccountName != fv1.FissionFetcherSA {
		t.Errorf("function pods should run as the platform's fetcher account, got %q", ps.ServiceAccountName)
	}
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsUser == nil || *ps.SecurityContext.RunAsUser != 10001 ||
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
		found = found || (v.Name == "scratch" && v.EmptyDir != nil)
	}
	if !found {
		t.Errorf("emptyDir volume not applied: %v", ps.Volumes)
	}
	h := zzFnContainer(ps, "helper")
	if h == nil {
		t.Fatalf("helper container missing")
	}
	if !zzFnHasCap(h.SecurityContext, "NET_BIND_SERVICE") {
		t.Errorf("NET_BIND_SERVICE capability dropped from helper: %+v", h.SecurityContext)
	}
	c := zzFnContainer(ps, "py")
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
	if !zzFnHasCap(sc, "CHOWN") {
		t.Errorf("CHOWN capability dropped: %+v", sc)
	}
}

func TestFuncZZNewDeployOperatorPatch(t *testing.T) {
	patch := &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{
			RunAsNonRoot: zzFnBool(true), RunAsUser: zzFnInt(10001), RunAsGroup: zzFnInt(10001), FSGroup: zzFnInt(10001),
		},
		NodeSelector:      map[string]string{"node-role": "fission"},
		Tolerations:       []apiv1.Toleration{{Key: "fission", Operator: apiv1.TolerationOpExists}},
		PriorityClassName: "fission-functions",
	}
	ps := zzFnSpec(t, zzFnDeploy(t, patch), zzFnEnv())
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

func TestFuncZZNewDeployRuntimePodSpecPatch(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.PodSpecPatch = `
nodeSelector:
  pool: functions
tolerations:
- key: dedicated
  operator: Equal
  value: functions
  effect: NoSchedule
containers:
- name: py
  resources:
    limits:
      memory: 256Mi
  securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      add: [CHOWN]
`
	ps := zzFnSpec(t, zzFnDeploy(t, nil), env)
	if ps.ServiceAccountName != fv1.FissionFetcherSA {
		t.Errorf("function pods should keep the platform's fetcher account, got %q", ps.ServiceAccountName)
	}
	if ps.NodeSelector["pool"] != "functions" {
		t.Errorf("runtime override node selector not applied: %v", ps.NodeSelector)
	}
	found := false
	for _, tol := range ps.Tolerations {
		found = found || tol.Key == "dedicated"
	}
	if !found {
		t.Errorf("runtime override toleration not applied: %v", ps.Tolerations)
	}
	c := zzFnContainer(ps, "py")
	if c == nil {
		t.Fatalf("runtime container missing")
	}
	if q := c.Resources.Limits[apiv1.ResourceMemory]; q.String() != "256Mi" {
		t.Errorf("runtime override memory limit not applied: %v", c.Resources.Limits)
	}
	if !zzFnHasCap(c.SecurityContext, "CHOWN") {
		t.Errorf("runtime override CHOWN dropped: %+v", c.SecurityContext)
	}
}

const zzFnOverlay = `
nodeSelector:
  pool: functions
runtimeClassName: gvisor
tolerations:
- key: dedicated
  operator: Equal
  value: functions
  effect: NoSchedule
containers:
- name: py
  resources:
    limits:
      memory: 256Mi
  securityContext:
    privileged: false
    allowPrivilegeEscalation: false
    capabilities:
      drop: [ALL]
      add: [NET_BIND_SERVICE]
- name: helper
  image: busybox:1.36
  command: ["sleep", "3600"]
  securityContext:
    privileged: false
    capabilities:
      add: [CHOWN]
`

func TestFuncZZNewDeployNamespacePodOverrides(t *testing.T) {
	nd := zzFnDeploy(t, nil)
	if _, err := nd.kubernetesClient.CoreV1().ConfigMaps("tenant-a").Create(context.Background(), &apiv1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: "fission-pod-overrides", Namespace: "tenant-a"},
		Data:       map[string]string{"podspec": zzFnOverlay},
	}, metav1.CreateOptions{}); err != nil {
		t.Fatal(err)
	}
	ps := zzFnSpec(t, nd, zzFnEnv())
	if ps.ServiceAccountName != "fission-fetcher" {
		t.Errorf("function pods should keep the platform's fetcher account, got %q", ps.ServiceAccountName)
	}
	if ps.NodeSelector["pool"] != "functions" {
		t.Errorf("overlay node selector not applied: %v", ps.NodeSelector)
	}
	if ps.RuntimeClassName == nil || *ps.RuntimeClassName != "gvisor" {
		t.Errorf("overlay runtimeClassName not applied: %v", ps.RuntimeClassName)
	}
	py := zzFnContainer(ps, "py")
	if py == nil {
		t.Fatalf("runtime container missing")
	}
	if !zzFnHasCap(py.SecurityContext, "NET_BIND_SERVICE") {
		t.Errorf("overlay NET_BIND_SERVICE dropped: %+v", py.SecurityContext)
	}
	if py.SecurityContext == nil || py.SecurityContext.Privileged == nil || *py.SecurityContext.Privileged {
		t.Errorf("explicit privileged=false not preserved: %+v", py.SecurityContext)
	}
	if zzFnContainer(ps, "helper") == nil {
		t.Fatalf("overlay helper container missing")
	}
}

func TestFuncZZNewDeployLegacyVersionPodSpec(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Version = 1
	env.Spec.Runtime.PodSpec = &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{RunAsNonRoot: zzFnBool(true), FSGroup: zzFnInt(10001)},
		NodeSelector:    map[string]string{"pool": "legacy"},
		Volumes: []apiv1.Volume{{Name: "settings", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
			LocalObjectReference: apiv1.LocalObjectReference{Name: "py-settings"}}}}},
		Containers: []apiv1.Container{{
			Name: "helper", Image: "busybox:1.36", Command: []string{"sleep", "3600"},
			SecurityContext: &apiv1.SecurityContext{
				Privileged:               zzFnBool(false),
				AllowPrivilegeEscalation: zzFnBool(false),
				Capabilities:             &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"NET_BIND_SERVICE"}},
			},
		}},
	}
	ps := zzFnSpec(t, zzFnDeploy(t, nil), env)
	if ps.ServiceAccountName != "fission-fetcher" {
		t.Errorf("function pods should keep the platform's fetcher account, got %q", ps.ServiceAccountName)
	}
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsNonRoot == nil || !*ps.SecurityContext.RunAsNonRoot ||
		ps.SecurityContext.FSGroup == nil || *ps.SecurityContext.FSGroup != 10001 {
		t.Errorf("legacy pod security context not applied: %+v", ps.SecurityContext)
	}
	if ps.NodeSelector["pool"] != "legacy" {
		t.Errorf("legacy node selector not applied: %v", ps.NodeSelector)
	}
	vol := false
	for _, v := range ps.Volumes {
		vol = vol || (v.Name == "settings" && v.ConfigMap != nil)
	}
	if !vol {
		t.Errorf("legacy configMap volume not applied")
	}
	h := zzFnContainer(ps, "helper")
	if h == nil {
		t.Fatalf("legacy helper container missing")
	}
	if !zzFnHasCap(h.SecurityContext, "NET_BIND_SERVICE") {
		t.Errorf("legacy helper capability dropped: %+v", h.SecurityContext)
	}
}
