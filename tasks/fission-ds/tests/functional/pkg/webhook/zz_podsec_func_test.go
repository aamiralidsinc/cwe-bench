package webhook

// Hidden functional tests: ordinary pod customisation of Environments and
// Functions keeps being admitted, on create and on update.

import (
	"context"
	"testing"

	"github.com/go-logr/logr"
	apiv1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	v1 "github.com/fission/fission/pkg/apis/core/v1"
)

func zzFnBool(b bool) *bool  { return &b }
func zzFnInt(i int64) *int64 { return &i }

func zzFnEnvHook() *Environment {
	w := &Environment{}
	w.Logger = logr.Discard()
	w.Validator = w
	return w
}

func zzFnFnHook() *Function {
	w := &Function{}
	w.Logger = logr.Discard()
	w.Validator = w
	return w
}

func zzFnEnv() *v1.Environment {
	return &v1.Environment{
		ObjectMeta: metav1.ObjectMeta{Name: "py", Namespace: "tenant-a"},
		Spec: v1.EnvironmentSpec{
			Version: 2,
			Runtime: v1.Runtime{Image: "fission/python-env:latest"},
			Builder: v1.Builder{Image: "fission/python-builder:latest", Command: "build"},
		},
	}
}

// zzFnHardenedSC is a container security context that tightens the defaults.
func zzFnHardenedSC() *apiv1.SecurityContext {
	return &apiv1.SecurityContext{
		Privileged:               zzFnBool(false),
		AllowPrivilegeEscalation: zzFnBool(false),
		ReadOnlyRootFilesystem:   zzFnBool(true),
		RunAsNonRoot:             zzFnBool(true),
		RunAsUser:                zzFnInt(10001),
		Capabilities: &apiv1.Capabilities{
			Drop: []apiv1.Capability{"ALL"},
			Add:  []apiv1.Capability{"NET_BIND_SERVICE", "CHOWN"},
		},
		SeccompProfile: &apiv1.SeccompProfile{Type: apiv1.SeccompProfileTypeRuntimeDefault},
	}
}

func zzFnCustomPodSpec() *apiv1.PodSpec {
	return &apiv1.PodSpec{
		SecurityContext: &apiv1.PodSecurityContext{
			RunAsNonRoot:   zzFnBool(true),
			RunAsUser:      zzFnInt(10001),
			RunAsGroup:     zzFnInt(10001),
			FSGroup:        zzFnInt(10001),
			SeccompProfile: &apiv1.SeccompProfile{Type: apiv1.SeccompProfileTypeRuntimeDefault},
		},
		NodeSelector: map[string]string{"pool": "functions"},
		Tolerations:  []apiv1.Toleration{{Key: "dedicated", Operator: apiv1.TolerationOpEqual, Value: "functions", Effect: apiv1.TaintEffectNoSchedule}},
		Volumes: []apiv1.Volume{
			{Name: "settings", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
				LocalObjectReference: apiv1.LocalObjectReference{Name: "py-settings"}}}},
			{Name: "scratch", VolumeSource: apiv1.VolumeSource{EmptyDir: &apiv1.EmptyDirVolumeSource{}}},
		},
		Containers: []apiv1.Container{{
			Name:            "helper",
			Image:           "busybox:1.36",
			Command:         []string{"sleep", "3600"},
			SecurityContext: zzFnHardenedSC(),
			Resources: apiv1.ResourceRequirements{Limits: apiv1.ResourceList{
				apiv1.ResourceCPU: resource.MustParse("200m"), apiv1.ResourceMemory: resource.MustParse("128Mi")}},
			VolumeMounts: []apiv1.VolumeMount{{Name: "settings", MountPath: "/etc/settings"}},
		}},
		InitContainers: []apiv1.Container{{
			Name:            "prepare",
			Image:           "busybox:1.36",
			Command:         []string{"true"},
			SecurityContext: zzFnHardenedSC(),
		}},
		AutomountServiceAccountToken: zzFnBool(false),
	}
}

func zzFnEnvAccepted(t *testing.T, env *v1.Environment) {
	t.Helper()
	if _, err := zzFnEnvHook().ValidateCreate(context.Background(), env); err != nil {
		t.Fatalf("Environment refused on create: %v", err)
	}
	if _, err := zzFnEnvHook().ValidateUpdate(context.Background(), zzFnEnv(), env); err != nil {
		t.Fatalf("Environment refused on update: %v", err)
	}
}

func TestFuncZZEnvPlainAccepted(t *testing.T) {
	zzFnEnvAccepted(t, zzFnEnv())
}

func TestFuncZZEnvRuntimePodSpecCustomisationAccepted(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.PodSpec = zzFnCustomPodSpec()
	zzFnEnvAccepted(t, env)
}

func TestFuncZZEnvBuilderPodSpecCustomisationAccepted(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Builder.PodSpec = zzFnCustomPodSpec()
	zzFnEnvAccepted(t, env)
}

func TestFuncZZEnvContainerCustomisationAccepted(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.Container = &apiv1.Container{
		Name:            "py",
		Env:             []apiv1.EnvVar{{Name: "LOG_LEVEL", Value: "debug"}},
		SecurityContext: zzFnHardenedSC(),
		Resources: apiv1.ResourceRequirements{Limits: apiv1.ResourceList{
			apiv1.ResourceMemory: resource.MustParse("256Mi")}},
	}
	env.Spec.Builder.Container = &apiv1.Container{
		Name:            "builder",
		Env:             []apiv1.EnvVar{{Name: "PIP_INDEX_URL", Value: "https://pypi.internal.example/simple"}},
		SecurityContext: zzFnHardenedSC(),
	}
	zzFnEnvAccepted(t, env)
}

func TestFuncZZFunctionContainerExecutorAccepted(t *testing.T) {
	grace := int64(30)
	ps := zzFnCustomPodSpec()
	ps.TerminationGracePeriodSeconds = &grace
	ps.Containers = append([]apiv1.Container{{
		Name:            "hello",
		Image:           "ghcr.io/tenant-a/hello:1.0",
		Ports:           []apiv1.ContainerPort{{Name: "http-env", ContainerPort: 8888}},
		SecurityContext: zzFnHardenedSC(),
	}}, ps.Containers...)
	fn := &v1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: "hello", Namespace: "tenant-a"},
		Spec: v1.FunctionSpec{
			InvokeStrategy: v1.InvokeStrategy{
				StrategyType: v1.StrategyTypeExecution,
				ExecutionStrategy: v1.ExecutionStrategy{
					ExecutorType: v1.ExecutorTypeContainer, MinScale: 1, MaxScale: 2,
				},
			},
			PodSpec: ps,
		},
	}
	if _, err := zzFnFnHook().ValidateCreate(context.Background(), fn); err != nil {
		t.Fatalf("Function refused on create: %v", err)
	}
	old := fn.DeepCopy()
	old.Spec.PodSpec.NodeSelector = nil
	if _, err := zzFnFnHook().ValidateUpdate(context.Background(), old, fn); err != nil {
		t.Fatalf("Function refused on update: %v", err)
	}
}

func zzFnSidecar() apiv1.Container {
	return apiv1.Container{
		Name:            "log-shipper",
		Image:           "busybox:1.36",
		Command:         []string{"sleep", "3600"},
		Resources:       apiv1.ResourceRequirements{Limits: apiv1.ResourceList{apiv1.ResourceCPU: resource.MustParse("100m")}},
		SecurityContext: zzFnHardenedSC(),
	}
}

func TestFuncZZFunctionSidecarsAccepted(t *testing.T) {
	grace := int64(30)
	fn := &v1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: "hello", Namespace: "tenant-a"},
		Spec: v1.FunctionSpec{
			InvokeStrategy: v1.InvokeStrategy{
				StrategyType: v1.StrategyTypeExecution,
				ExecutionStrategy: v1.ExecutionStrategy{
					ExecutorType: v1.ExecutorTypeContainer, MinScale: 1, MaxScale: 2,
				},
			},
			PodSpec: &apiv1.PodSpec{
				TerminationGracePeriodSeconds: &grace,
				Containers: []apiv1.Container{{
					Name:  "hello",
					Image: "ghcr.io/tenant-a/hello:1.0",
					Ports: []apiv1.ContainerPort{{Name: "http-env", ContainerPort: 8888}},
				}},
			},
			Sidecars: []apiv1.Container{zzFnSidecar()},
		},
	}
	if _, err := zzFnFnHook().ValidateCreate(context.Background(), fn); err != nil {
		t.Fatalf("Function with an ordinary sidecar refused on create: %v", err)
	}
	old := fn.DeepCopy()
	old.Spec.Sidecars[0].Image = "busybox:1.35"
	if _, err := zzFnFnHook().ValidateUpdate(context.Background(), old, fn); err != nil {
		t.Fatalf("Function with an ordinary sidecar refused on update: %v", err)
	}
}

const zzFnBenignPatch = `
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
    privileged: false
    allowPrivilegeEscalation: false
    capabilities:
      drop: [ALL]
      add: [NET_BIND_SERVICE]
`

func TestFuncZZEnvPodSpecPatchAccepted(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Runtime.PodSpecPatch = zzFnBenignPatch
	zzFnEnvAccepted(t, env)
}

func TestFuncZZAnnotatedEnvAccepted(t *testing.T) {
	env := zzFnEnv()
	env.Annotations = map[string]string{
		"fission.io/legacy-podspec": "true",
		"team":                      "payments",
	}
	env.Spec.Runtime.PodSpec = zzFnCustomPodSpec()
	zzFnEnvAccepted(t, env)
}

// A version-1 Environment is a supported object: ordinary pod customisation on
// it is still admitted, on create and on update.
func TestFuncZZEnvVersion1PodSpecAccepted(t *testing.T) {
	env := zzFnEnv()
	env.Spec.Version = 1
	env.Spec.Runtime.PodSpec = zzFnCustomPodSpec()
	zzFnEnvAccepted(t, env)
}
