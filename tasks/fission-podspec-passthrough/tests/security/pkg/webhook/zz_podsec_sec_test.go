package webhook

// Hidden security tests: a tenant who may create or update Environment and
// Function objects must not get pod-level privileges through them. These
// drive the validating admission webhooks the API server calls.

import (
	"context"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"github.com/go-logr/logr"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	v1 "github.com/fission/fission/pkg/apis/core/v1"
)

func zzSecBool(b bool) *bool { return &b }

func zzSecEnvHook() *Environment {
	w := &Environment{}
	w.Logger = logr.Discard()
	w.Validator = w
	return w
}

func zzSecFnHook() *Function {
	w := &Function{}
	w.Logger = logr.Discard()
	w.Validator = w
	return w
}

// zzSecEnv is an ordinary tenant Environment that admission accepts today.
func zzSecEnv() *v1.Environment {
	return &v1.Environment{
		ObjectMeta: metav1.ObjectMeta{Name: "py", Namespace: "tenant-a"},
		Spec: v1.EnvironmentSpec{
			Version: 2,
			Runtime: v1.Runtime{Image: "fission/python-env:latest"},
			Builder: v1.Builder{Image: "fission/python-builder:latest", Command: "build"},
		},
	}
}

// zzSecFn is an ordinary container-executor Function that admission accepts today.
func zzSecFn() *v1.Function {
	grace := int64(30)
	return &v1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: "hello", Namespace: "tenant-a"},
		Spec: v1.FunctionSpec{
			InvokeStrategy: v1.InvokeStrategy{
				StrategyType: v1.StrategyTypeExecution,
				ExecutionStrategy: v1.ExecutionStrategy{
					ExecutorType: v1.ExecutorTypeContainer,
					MinScale:     1,
					MaxScale:     2,
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
		},
	}
}

func zzSecSidecar(sc *apiv1.SecurityContext) apiv1.Container {
	return apiv1.Container{Name: "helper", Image: "busybox:1.36", Command: []string{"sleep", "3600"}, SecurityContext: sc}
}

func zzSecEnvRejected(t *testing.T, env *v1.Environment) {
	t.Helper()
	if _, err := zzSecEnvHook().ValidateCreate(context.Background(), env); err == nil {
		t.Fatalf("Environment admitted on create; it must be refused")
	}
}

func zzSecFnRejected(t *testing.T, fn *v1.Function) {
	t.Helper()
	if _, err := zzSecFnHook().ValidateCreate(context.Background(), fn); err == nil {
		t.Fatalf("Function admitted on create; it must be refused")
	}
	old := zzSecFn()
	if _, err := zzSecFnHook().ValidateUpdate(context.Background(), old, fn); err == nil {
		t.Fatalf("Function admitted on update; it must be refused")
	}
}

// The reported case and its siblings: host namespaces in the runtime pod spec.
func TestSecZZEnvRuntimePodSpecHostNamespaces(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"hostNetwork": func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"hostPID":     func(p *apiv1.PodSpec) { p.HostPID = true },
		"hostIPC":     func(p *apiv1.PodSpec) { p.HostIPC = true },
	}
	for name, set := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.PodSpec = &apiv1.PodSpec{}
			set(env.Spec.Runtime.PodSpec)
			zzSecEnvRejected(t, env)
		})
	}
}

func TestSecZZEnvRuntimePodSpecServiceAccount(t *testing.T) {
	t.Run("serviceAccountName", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Runtime.PodSpec = &apiv1.PodSpec{ServiceAccountName: "zz-tenant-picked-sa"}
		zzSecEnvRejected(t, env)
	})
	t.Run("serviceAccount", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Runtime.PodSpec = &apiv1.PodSpec{DeprecatedServiceAccount: "zz-tenant-picked-sa"}
		zzSecEnvRejected(t, env)
	})
}

func TestSecZZEnvRuntimePodSpecHostPathVolume(t *testing.T) {
	env := zzSecEnv()
	env.Spec.Runtime.PodSpec = &apiv1.PodSpec{
		Volumes: []apiv1.Volume{
			{Name: "settings", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
				LocalObjectReference: apiv1.LocalObjectReference{Name: "py-settings"}}}},
			{Name: "zz-node-dir", VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}},
		},
	}
	zzSecEnvRejected(t, env)
}

func TestSecZZEnvRuntimePodSpecContainerPrivileges(t *testing.T) {
	t.Run("privileged_container", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Runtime.PodSpec = &apiv1.PodSpec{Containers: []apiv1.Container{
			zzSecSidecar(&apiv1.SecurityContext{Privileged: zzSecBool(true)})}}
		zzSecEnvRejected(t, env)
	})
	t.Run("init_container_privilege_escalation", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Runtime.PodSpec = &apiv1.PodSpec{InitContainers: []apiv1.Container{
			zzSecSidecar(&apiv1.SecurityContext{AllowPrivilegeEscalation: zzSecBool(true)})}}
		zzSecEnvRejected(t, env)
	})
	t.Run("init_container_privileged", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Runtime.PodSpec = &apiv1.PodSpec{InitContainers: []apiv1.Container{
			zzSecSidecar(&apiv1.SecurityContext{Privileged: zzSecBool(true)})}}
		zzSecEnvRejected(t, env)
	})
}

func TestSecZZEnvRuntimePodSpecAddedCapability(t *testing.T) {
	env := zzSecEnv()
	env.Spec.Runtime.PodSpec = &apiv1.PodSpec{Containers: []apiv1.Container{
		zzSecSidecar(&apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
			Add: []apiv1.Capability{"NET_BIND_SERVICE", "SYS_ADMIN"}}})}}
	zzSecEnvRejected(t, env)
}

// Other capabilities with administrative or cross-process power, ALL (which
// grants every capability), and spellings the container runtime accepts.
var zzSecAdminCapVariants = map[string]apiv1.Capability{
	"ALL":                    "ALL",
	"NET_ADMIN":              "NET_ADMIN",
	"SYS_PTRACE":             "SYS_PTRACE",
	"SYS_MODULE":             "SYS_MODULE",
	"lowercase_cap_prefixed": "cap_sys_admin",
	"lowercase_all":          "all",
}

func zzSecCapSC(c apiv1.Capability) *apiv1.SecurityContext {
	return &apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"NET_BIND_SERVICE", c}}}
}

func TestSecZZEnvAddedCapabilityVariants(t *testing.T) {
	for name, c := range zzSecAdminCapVariants {
		t.Run("runtime_podspec_"+name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.PodSpec = &apiv1.PodSpec{Containers: []apiv1.Container{zzSecSidecar(zzSecCapSC(c))}}
			zzSecEnvRejected(t, env)
		})
		t.Run("runtime_container_"+name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.Container = &apiv1.Container{Name: "py", SecurityContext: zzSecCapSC(c)}
			zzSecEnvRejected(t, env)
		})
	}
	t.Run("builder_container_ALL", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.Container = &apiv1.Container{Name: "builder", SecurityContext: zzSecCapSC("ALL")}
		zzSecEnvRejected(t, env)
	})
	t.Run("builder_podspec_init_SYS_PTRACE", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.PodSpec = &apiv1.PodSpec{InitContainers: []apiv1.Container{zzSecSidecar(zzSecCapSC("SYS_PTRACE"))}}
		zzSecEnvRejected(t, env)
	})
}

func TestSecZZEnvBuilderPodSpec(t *testing.T) {
	t.Run("hostNetwork", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.PodSpec = &apiv1.PodSpec{HostNetwork: true}
		zzSecEnvRejected(t, env)
	})
	t.Run("hostIPC", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.PodSpec = &apiv1.PodSpec{HostIPC: true}
		zzSecEnvRejected(t, env)
	})
	t.Run("serviceAccountName", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.PodSpec = &apiv1.PodSpec{ServiceAccountName: "zz-tenant-picked-sa"}
		zzSecEnvRejected(t, env)
	})
	t.Run("privileged_init_container", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.PodSpec = &apiv1.PodSpec{InitContainers: []apiv1.Container{
			zzSecSidecar(&apiv1.SecurityContext{Privileged: zzSecBool(true)})}}
		zzSecEnvRejected(t, env)
	})
	t.Run("hostPath", func(t *testing.T) {
		env := zzSecEnv()
		env.Spec.Builder.PodSpec = &apiv1.PodSpec{Volumes: []apiv1.Volume{
			{Name: "zz-node-dir", VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}}}}
		zzSecEnvRejected(t, env)
	})
}

// The single-container customisation of the runtime and builder containers
// lands on the same pods as the pod spec does.
func TestSecZZEnvRuntimeContainerPrivileges(t *testing.T) {
	cases := map[string]*apiv1.SecurityContext{
		"privileged":               {Privileged: zzSecBool(true)},
		"allowPrivilegeEscalation": {AllowPrivilegeEscalation: zzSecBool(true)},
		"added_capability":         {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"NET_BIND_SERVICE", "SYS_ADMIN"}}},
	}
	for name, sc := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.Container = &apiv1.Container{Name: "py", SecurityContext: sc}
			zzSecEnvRejected(t, env)
		})
	}
}

func TestSecZZEnvBuilderContainerPrivileges(t *testing.T) {
	cases := map[string]*apiv1.SecurityContext{
		"privileged":               {Privileged: zzSecBool(true)},
		"allowPrivilegeEscalation": {AllowPrivilegeEscalation: zzSecBool(true)},
		"added_capability":         {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"SYS_ADMIN"}}},
	}
	for name, sc := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Builder.Container = &apiv1.Container{Name: "builder", SecurityContext: sc}
			zzSecEnvRejected(t, env)
		})
	}
}

// A clean Environment later updated (or patched) to carry the same settings.
func TestSecZZEnvUpdate(t *testing.T) {
	t.Run("update_is_validated", func(t *testing.T) {
		old := zzSecEnv()
		upd := zzSecEnv()
		upd.Spec.Runtime.PodSpec = &apiv1.PodSpec{HostPID: true}
		if _, err := zzSecEnvHook().ValidateUpdate(context.Background(), old, upd); err == nil {
			t.Fatalf("Environment update admitted; it must be refused")
		}
	})
	t.Run("installed_webhook_receives_updates", func(t *testing.T) {
		// The Helm chart registers the validating webhook with the API
		// server; updates of environments must be sent to it.
		root := zzSecRepoRoot(t)
		raw, err := os.ReadFile(filepath.Join(root, "charts", "fission-all", "templates", "webhook-server", "webhooks.yaml"))
		if err != nil {
			t.Fatalf("read chart: %v", err)
		}
		ops := zzSecWebhookOperations(string(raw), "/validate-fission-io-v1-environment")
		if ops == nil {
			t.Fatalf("environment validating webhook not found in the chart")
		}
		if !ops["UPDATE"] && !ops["*"] {
			t.Fatalf("environment validating webhook is not called on UPDATE (operations: %v)", ops)
		}
	})
}

func TestSecZZFunctionPodSpec(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"hostNetwork":        func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"hostPID":            func(p *apiv1.PodSpec) { p.HostPID = true },
		"hostIPC":            func(p *apiv1.PodSpec) { p.HostIPC = true },
		"serviceAccountName": func(p *apiv1.PodSpec) { p.ServiceAccountName = "zz-tenant-picked-sa" },
		"serviceAccount":     func(p *apiv1.PodSpec) { p.DeprecatedServiceAccount = "zz-tenant-picked-sa" },
		"init_container_privilege_escalation": func(p *apiv1.PodSpec) {
			p.InitContainers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{AllowPrivilegeEscalation: zzSecBool(true)})}
		},
		"hostPath": func(p *apiv1.PodSpec) {
			p.Volumes = append(p.Volumes, apiv1.Volume{Name: "zz-node-dir",
				VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}})
		},
		"privileged": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Privileged: zzSecBool(true)}
		},
		"added_capability": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"SYS_ADMIN"}}}
		},
	}
	for name, c := range zzSecAdminCapVariants {
		c := c
		cases["added_capability_"+name] = func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = zzSecCapSC(c)
		}
	}
	for name, set := range cases {
		t.Run(name, func(t *testing.T) {
			fn := zzSecFn()
			set(fn.Spec.PodSpec)
			zzSecFnRejected(t, fn)
		})
	}
}

func zzSecRepoRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatalf("go.mod not found")
		}
		dir = parent
	}
}

// zzSecWebhookOperations returns the operations listed in the rules of the
// webhook entry whose clientConfig path is the given one (nil if absent).
// The chart is a Helm template, so it is read as text, entry by entry.
func zzSecWebhookOperations(chart, path string) map[string]bool {
	entries := regexp.MustCompile(`(?m)^- `).Split(chart, -1)
	for _, e := range entries {
		if !strings.Contains(e, "path: "+path) && !strings.Contains(e, "path: \""+path+"\"") {
			continue
		}
		ops := map[string]bool{}
		in := false
		for _, line := range strings.Split(e, "\n") {
			s := strings.TrimSpace(line)
			if strings.HasPrefix(s, "operations:") {
				in = true
				rest := strings.TrimSpace(strings.TrimPrefix(s, "operations:"))
				if strings.HasPrefix(rest, "[") {
					for _, op := range strings.Split(strings.Trim(rest, "[]"), ",") {
						ops[strings.Trim(strings.TrimSpace(op), `"'`)] = true
					}
					in = false
				}
				continue
			}
			if in {
				if strings.HasPrefix(s, "- ") {
					ops[strings.Trim(strings.TrimSpace(strings.TrimPrefix(s, "- ")), `"'`)] = true
					continue
				}
				in = false
			}
		}
		return ops
	}
	return nil
}
