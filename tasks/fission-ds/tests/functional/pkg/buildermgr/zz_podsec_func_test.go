package buildermgr

// Hidden functional tests: tenant builder customisation and the operator's
// builder pod-spec patch keep reaching the builder deployment.

import (
	"context"
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	apiv1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	k8sfake "k8s.io/client-go/kubernetes/fake"

	fv1 "github.com/fission/fission/pkg/apis/core/v1"
	fetcherConfig "github.com/fission/fission/pkg/fetcher/config"
	"github.com/fission/fission/pkg/utils"
	"github.com/fission/fission/pkg/utils/loggerfactory"
)

func zzFnBool(b bool) *bool  { return &b }
func zzFnInt(i int64) *int64 { return &i }

func zzFnWatcher(t *testing.T, patch *apiv1.PodSpec) (*environmentWatcher, *k8sfake.Clientset) {
	t.Helper()
	cfg, err := fetcherConfig.MakeFetcherConfig("/packages")
	if err != nil {
		t.Fatal(err)
	}
	client := k8sfake.NewSimpleClientset()
	return &environmentWatcher{
		logger:           loggerfactory.GetLogger(),
		kubernetesClient: client,
		nsResolver:       utils.DefaultNSResolver(),
		fetcherConfig:    cfg,
		cache:            map[types.UID]*builderInfo{},
		podSpecPatch:     patch,
	}, client
}

func zzFnEnv() *fv1.Environment {
	return &fv1.Environment{
		ObjectMeta: metav1.ObjectMeta{Name: "py", Namespace: "tenant-a", ResourceVersion: "7"},
		Spec: fv1.EnvironmentSpec{
			Version: 2,
			Runtime: fv1.Runtime{Image: "fission/python-env:latest"},
			Builder: fv1.Builder{Image: "fission/python-builder:latest"},
		},
	}
}

func zzFnCreated(t *testing.T, client *k8sfake.Clientset) *appsv1.Deployment {
	t.Helper()
	list, err := client.AppsV1().Deployments("tenant-a").List(context.Background(), metav1.ListOptions{})
	if err != nil {
		t.Fatal(err)
	}
	if len(list.Items) != 1 {
		t.Fatalf("expected one builder deployment, got %d", len(list.Items))
	}
	return &list.Items[0]
}

func TestFuncZZBuilderTenantCustomisation(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Builder.Container = &apiv1.Container{
		Env: []apiv1.EnvVar{{Name: "PIP_INDEX_URL", Value: "https://pypi.internal.example/simple"}},
		Resources: apiv1.ResourceRequirements{Limits: apiv1.ResourceList{
			apiv1.ResourceMemory: resource.MustParse("512Mi")}},
		SecurityContext: &apiv1.SecurityContext{
			RunAsNonRoot:             zzFnBool(true),
			AllowPrivilegeEscalation: zzFnBool(false),
			Capabilities:             &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"CHOWN"}},
		},
	}
	env.Spec.Builder.PodSpec = &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{RunAsNonRoot: zzFnBool(true), FSGroup: zzFnInt(10001)},
		NodeSelector:    map[string]string{"pool": "builders"},
		Volumes: []apiv1.Volume{{Name: "pip-conf", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
			LocalObjectReference: apiv1.LocalObjectReference{Name: "pip-conf"}}}}},
	}
	envw, client := zzFnWatcher(t, nil)
	if _, err := envw.createBuilderDeployment(context.Background(), env, "tenant-a"); err != nil {
		t.Fatalf("createBuilderDeployment: %v", err)
	}
	ps := &zzFnCreated(t, client).Spec.Template.Spec
	if ps.ServiceAccountName != "fission-builder" {
		t.Errorf("builder pods should run as the platform's builder account, got %q", ps.ServiceAccountName)
	}
	if ps.SecurityContext == nil || ps.SecurityContext.FSGroup == nil || *ps.SecurityContext.FSGroup != 10001 {
		t.Errorf("pod security context not applied: %+v", ps.SecurityContext)
	}
	if ps.NodeSelector["pool"] != "builders" {
		t.Errorf("node selector not applied: %v", ps.NodeSelector)
	}
	vol := false
	for _, v := range ps.Volumes {
		vol = vol || (v.Name == "pip-conf" && v.ConfigMap != nil)
	}
	if !vol {
		t.Errorf("configMap volume not applied")
	}
	var b *apiv1.Container
	for i := range ps.Containers {
		if ps.Containers[i].Name == "builder" {
			b = &ps.Containers[i]
		}
	}
	if b == nil {
		t.Fatalf("builder container missing")
	}
	envOK := false
	for _, e := range b.Env {
		envOK = envOK || e.Name == "PIP_INDEX_URL"
	}
	if !envOK {
		t.Errorf("builder env not applied: %v", b.Env)
	}
	if q := b.Resources.Limits[apiv1.ResourceMemory]; q.String() != "512Mi" {
		t.Errorf("builder memory limit not applied: %v", b.Resources.Limits)
	}
	sc := b.SecurityContext
	if sc == nil || sc.RunAsNonRoot == nil || !*sc.RunAsNonRoot || sc.Capabilities == nil || len(sc.Capabilities.Add) != 1 || sc.Capabilities.Add[0] != "CHOWN" {
		t.Errorf("builder container security context not applied: %+v", sc)
	}
}

func TestFuncZZBuilderOperatorPatch(t *testing.T) {
	patch := &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{
			RunAsNonRoot: zzFnBool(true), RunAsUser: zzFnInt(10001), RunAsGroup: zzFnInt(10001), FSGroup: zzFnInt(10001),
		},
		Tolerations: []apiv1.Toleration{{Key: "fission", Operator: apiv1.TolerationOpExists}},
	}
	envw, client := zzFnWatcher(t, patch)
	if _, err := envw.createBuilderDeployment(context.Background(), zzFnEnv(), "tenant-a"); err != nil {
		t.Fatalf("createBuilderDeployment: %v", err)
	}
	ps := &zzFnCreated(t, client).Spec.Template.Spec
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsUser == nil || *ps.SecurityContext.RunAsUser != 10001 ||
		ps.SecurityContext.RunAsGroup == nil || *ps.SecurityContext.RunAsGroup != 10001 {
		t.Errorf("operator pod security context not applied: %+v", ps.SecurityContext)
	}
	if len(ps.Tolerations) == 0 {
		t.Errorf("operator toleration not applied")
	}
}

const zzFnOverlay = `
nodeSelector:
  pool: builders
runtimeClassName: gvisor
containers:
- name: builder
  securityContext:
    privileged: false
    allowPrivilegeEscalation: false
    capabilities:
      drop: [ALL]
      add: [CHOWN]
- name: helper
  image: busybox:1.36
  command: ["sleep", "3600"]
  securityContext:
    privileged: false
`

func TestFuncZZBuilderNamespacePodOverrides(t *testing.T) {
	envw, client := zzFnWatcher(t, nil)
	if _, err := client.CoreV1().ConfigMaps("tenant-a").Create(context.Background(), &apiv1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: "fission-pod-overrides", Namespace: "tenant-a"},
		Data:       map[string]string{"podspec": zzFnOverlay},
	}, metav1.CreateOptions{}); err != nil {
		t.Fatal(err)
	}
	if _, err := envw.createBuilderDeployment(context.Background(), zzFnEnv(), "tenant-a"); err != nil {
		t.Fatalf("createBuilderDeployment: %v", err)
	}
	ps := &zzFnCreated(t, client).Spec.Template.Spec
	if ps.ServiceAccountName != "fission-builder" {
		t.Errorf("builder pods should keep the platform's builder account, got %q", ps.ServiceAccountName)
	}
	if ps.NodeSelector["pool"] != "builders" {
		t.Errorf("overlay node selector not applied: %v", ps.NodeSelector)
	}
	if ps.RuntimeClassName == nil || *ps.RuntimeClassName != "gvisor" {
		t.Errorf("overlay runtimeClassName not applied: %v", ps.RuntimeClassName)
	}
	var b, helper *apiv1.Container
	for i := range ps.Containers {
		switch ps.Containers[i].Name {
		case "builder":
			b = &ps.Containers[i]
		case "helper":
			helper = &ps.Containers[i]
		}
	}
	if b == nil {
		t.Fatalf("builder container missing")
	}
	if helper == nil {
		t.Fatalf("overlay helper container missing")
	}
	ok := false
	if b.SecurityContext != nil && b.SecurityContext.Capabilities != nil {
		for _, c := range b.SecurityContext.Capabilities.Add {
			ok = ok || c == "CHOWN"
		}
	}
	if !ok {
		t.Errorf("overlay CHOWN capability dropped from builder: %+v", b.SecurityContext)
	}
	if b.SecurityContext == nil || b.SecurityContext.Privileged == nil || *b.SecurityContext.Privileged {
		t.Errorf("explicit privileged=false not preserved: %+v", b.SecurityContext)
	}
}

func TestFuncZZBuilderLegacyVersionPodSpec(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Version = 1
	env.Spec.Builder.PodSpec = &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{RunAsNonRoot: zzFnBool(true), FSGroup: zzFnInt(10001)},
		NodeSelector:    map[string]string{"pool": "legacy-builders"},
		Volumes: []apiv1.Volume{{Name: "pip-conf", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
			LocalObjectReference: apiv1.LocalObjectReference{Name: "pip-conf"}}}}},
		Containers: []apiv1.Container{{
			Name: "helper", Image: "busybox:1.36", Command: []string{"true"},
			SecurityContext: &apiv1.SecurityContext{
				Privileged:   zzFnBool(false),
				Capabilities: &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"NET_BIND_SERVICE"}},
			},
		}},
	}
	envw, client := zzFnWatcher(t, nil)
	if _, err := envw.createBuilderDeployment(context.Background(), env, "tenant-a"); err != nil {
		t.Fatalf("createBuilderDeployment: %v", err)
	}
	ps := &zzFnCreated(t, client).Spec.Template.Spec
	if ps.ServiceAccountName != "fission-builder" {
		t.Errorf("builder pods should keep the platform's builder account, got %q", ps.ServiceAccountName)
	}
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsNonRoot == nil || !*ps.SecurityContext.RunAsNonRoot ||
		ps.SecurityContext.FSGroup == nil || *ps.SecurityContext.FSGroup != 10001 {
		t.Errorf("legacy pod security context not applied: %+v", ps.SecurityContext)
	}
	if ps.NodeSelector["pool"] != "legacy-builders" {
		t.Errorf("legacy node selector not applied: %v", ps.NodeSelector)
	}
	vol := false
	for _, v := range ps.Volumes {
		vol = vol || (v.Name == "pip-conf" && v.ConfigMap != nil)
	}
	if !vol {
		t.Errorf("legacy configMap volume not applied")
	}
	found := false
	for i := range ps.Containers {
		if ps.Containers[i].Name == "helper" {
			found = true
			sc := ps.Containers[i].SecurityContext
			if sc == nil || sc.Capabilities == nil {
				t.Fatalf("legacy helper capability missing")
			}
			ok := false
			for _, c := range sc.Capabilities.Add {
				ok = ok || c == "NET_BIND_SERVICE"
			}
			if !ok {
				t.Errorf("legacy helper capability dropped: %+v", sc)
			}
		}
	}
	if !found {
		t.Fatalf("legacy helper container missing")
	}
}
