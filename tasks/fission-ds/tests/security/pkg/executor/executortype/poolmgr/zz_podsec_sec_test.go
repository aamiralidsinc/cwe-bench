package poolmgr

// Hidden security tests: the pool deployment the executor builds from an
// Environment object that is already stored in the cluster (for example one
// created before an upgrade) must not carry pod-level privileges the tenant
// asked for. The controller may refuse the object or build a pod without
// them; either way the privileges must not reach the pod.

import (
	"strings"
	"testing"

	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	k8sfake "k8s.io/client-go/kubernetes/fake"

	fv1 "github.com/fission/fission/pkg/apis/core/v1"
	fetcherConfig "github.com/fission/fission/pkg/fetcher/config"
	"github.com/fission/fission/pkg/utils/loggerfactory"
)

const zzSecMarkerSA = "zz-tenant-picked-sa"

// zzSecAdminCaps are capabilities that grant administrative or cross-process
// power (ALL includes them all).
var zzSecAdminCaps = map[string]bool{"SYS_ADMIN": true, "NET_ADMIN": true, "SYS_PTRACE": true, "SYS_MODULE": true, "ALL": true}

func zzSecBool(b bool) *bool { return &b }

func zzSecPool(t *testing.T) *GenericPool {
	t.Helper()
	cfg, err := fetcherConfig.MakeFetcherConfig("/userfunc")
	if err != nil {
		t.Fatal(err)
	}
	return &GenericPool{logger: loggerfactory.GetLogger(), fetcherConfig: cfg}
}

func zzSecEnv() *fv1.Environment {
	return &fv1.Environment{
		ObjectMeta: metav1.ObjectMeta{Name: "py", Namespace: "tenant-a"},
		Spec: fv1.EnvironmentSpec{
			Version: 2,
			Runtime: fv1.Runtime{Image: "fission/python-env:latest"},
		},
	}
}

func zzSecSidecar(sc *apiv1.SecurityContext) apiv1.Container {
	return apiv1.Container{Name: "helper", Image: "busybox:1.36", Command: []string{"sleep", "3600"}, SecurityContext: sc}
}

// zzSecUnsafe lists the tenant-requested privileges present in a pod spec.
func zzSecUnsafe(ps *apiv1.PodSpec) []string {
	var out []string
	if ps.HostNetwork {
		out = append(out, "hostNetwork")
	}
	if ps.HostPID {
		out = append(out, "hostPID")
	}
	if ps.HostIPC {
		out = append(out, "hostIPC")
	}
	// The pod runs as serviceAccountName; the deprecated alias applies
	// only when that is empty.
	effectiveSA := ps.ServiceAccountName
	if effectiveSA == "" {
		effectiveSA = ps.DeprecatedServiceAccount
	}
	if effectiveSA == zzSecMarkerSA {
		out = append(out, "tenant service account")
	}
	for _, v := range ps.Volumes {
		if v.HostPath != nil {
			out = append(out, "hostPath volume "+v.Name)
		}
	}
	check := func(kind string, cs []apiv1.Container) {
		for _, c := range cs {
			sc := c.SecurityContext
			if sc == nil {
				continue
			}
			if sc.Privileged != nil && *sc.Privileged {
				out = append(out, kind+" "+c.Name+" privileged")
			}
			if sc.AllowPrivilegeEscalation != nil && *sc.AllowPrivilegeEscalation {
				out = append(out, kind+" "+c.Name+" allowPrivilegeEscalation")
			}
			if sc.Capabilities != nil {
				for _, cp := range sc.Capabilities.Add {
					// The container runtime upper-cases names and adds CAP_.
					name := strings.TrimPrefix(strings.ToUpper(strings.TrimSpace(string(cp))), "CAP_")
					if zzSecAdminCaps[name] {
						out = append(out, kind+" "+c.Name+" "+name)
					}
				}
			}
		}
	}
	check("container", ps.Containers)
	check("initContainer", ps.InitContainers)
	return out
}

func zzSecPoolMustNotCarry(t *testing.T, env *fv1.Environment) {
	t.Helper()
	spec, err := zzSecPool(t).genDeploymentSpec(env)
	if err != nil {
		return // refused: no deployment is built
	}
	if spec == nil {
		return
	}
	if bad := zzSecUnsafe(&spec.Template.Spec); len(bad) > 0 {
		t.Fatalf("pool deployment carries tenant-requested privileges: %v", bad)
	}
}

func TestSecZZPoolStoredRuntimePodSpec(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"hostNetwork":        func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"hostPID":            func(p *apiv1.PodSpec) { p.HostPID = true },
		"hostIPC":            func(p *apiv1.PodSpec) { p.HostIPC = true },
		"serviceAccountName": func(p *apiv1.PodSpec) { p.ServiceAccountName = zzSecMarkerSA },
		"hostPath": func(p *apiv1.PodSpec) {
			p.Volumes = []apiv1.Volume{{Name: "zz-node-dir",
				VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}}}
		},
		"privileged_container": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Privileged: zzSecBool(true)})}
		},
		"init_container_privilege_escalation": func(p *apiv1.PodSpec) {
			p.InitContainers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{AllowPrivilegeEscalation: zzSecBool(true)})}
		},
		"added_capability": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"NET_BIND_SERVICE", "SYS_ADMIN"}}})}
		},
		"added_capability_all": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"ALL"}}})}
		},
		"added_capability_sys_ptrace": func(p *apiv1.PodSpec) {
			p.InitContainers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"SYS_PTRACE"}}})}
		},
	}
	for name, set := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.PodSpec = &apiv1.PodSpec{}
			set(env.Spec.Runtime.PodSpec)
			zzSecPoolMustNotCarry(t, env)
		})
	}
}

func TestSecZZPoolStoredRuntimeContainer(t *testing.T) {
	cases := map[string]*apiv1.SecurityContext{
		"privileged":                              {Privileged: zzSecBool(true)},
		"allowPrivilegeEscalation":                {AllowPrivilegeEscalation: zzSecBool(true)},
		"added_capability":                        {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"NET_BIND_SERVICE", "SYS_ADMIN"}}},
		"added_capability_all":                    {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"ALL"}}},
		"added_capability_net_admin":              {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"NET_ADMIN"}}},
		"added_capability_cap_prefixed_lowercase": {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"cap_sys_admin"}}},
	}
	for name, sc := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.Container = &apiv1.Container{SecurityContext: sc}
			zzSecPoolMustNotCarry(t, env)
		})
	}
}

// The serialized runtime override is applied to the pool pod after the typed
// pod spec; a stored Environment that carries one must not yield such a pod.
func TestSecZZPoolStoredRuntimePodSpecPatch(t *testing.T) {
	cases := map[string]string{
		"host_network":              "hostNetwork: true\n",
		"host_pid":                  "hostPID: true\n",
		"service_account":           "serviceAccountName: zz-tenant-picked-sa\n",
		"host_path":                 "volumes:\n- name: zz-node-dir\n  hostPath:\n    path: /var/zz-marker\n",
		"privileged":                "containers:\n- name: py\n  securityContext:\n    privileged: true\n",
		"allow_privilege_escalation": "containers:\n- name: py\n  securityContext:\n    allowPrivilegeEscalation: true\n",
		"added_capability":          "containers:\n- name: py\n  securityContext:\n    capabilities:\n      add: [NET_BIND_SERVICE, SYS_ADMIN]\n",
		"added_capability_all":      "{\"containers\": [{\"name\": \"py\", \"securityContext\": {\"capabilities\": {\"add\": [\"ALL\"]}}}]}\n",
	}
	for name, patch := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.PodSpecPatch = patch
			zzSecPoolMustNotCarry(t, env)
		})
	}
}

// The namespace's pod-spec overlay is merged into the pool pod after the typed
// pod spec. A stored overlay that asks for pod-level privileges must not yield
// a pool deployment that carries them.
func TestSecZZPoolNamespacePodOverrides(t *testing.T) {
	cases := map[string]string{
		"host_network":    "hostNetwork: true\n",
		"host_pid":        "hostPID: true\n",
		"host_ipc":        "hostIPC: true\n",
		"service_account": "serviceAccountName: zz-tenant-picked-sa\n",
		"host_path":       "volumes:\n- name: zz-node-dir\n  hostPath:\n    path: /var/zz-marker\n",
		"privileged":      "containers:\n- name: py\n  securityContext:\n    privileged: true\n",
		"capability_all":  "containers:\n- name: py\n  securityContext:\n    capabilities:\n      add: [NET_BIND_SERVICE, ALL]\n",
	}
	for name, overlay := range cases {
		t.Run(name, func(t *testing.T) {
			gp := zzSecPool(t)
			gp.kubernetesClient = zzSecOverridesClient(overlay)
			zzSecPoolCannotBuild(t, gp, zzSecEnv())
		})
	}
}

// Version-1 Environments keep the legacy pod-spec settings. A stored
// version-1 Environment that asks for pod-level privileges must not yield a
// pool deployment that carries them.
func TestSecZZPoolLegacyVersionRuntimePodSpec(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"host_network":        func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"host_pid":            func(p *apiv1.PodSpec) { p.HostPID = true },
		"service_account":     func(p *apiv1.PodSpec) { p.ServiceAccountName = zzSecMarkerSA },
		"host_path": func(p *apiv1.PodSpec) {
			p.Volumes = []apiv1.Volume{{Name: "zz-node-dir",
				VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}}}
		},
		"privileged_container": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Privileged: zzSecBool(true)})}
		},
		"capability_all": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"ALL"}}})}
		},
	}
	for name, set := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Version = 1
			env.Spec.Runtime.PodSpec = &apiv1.PodSpec{}
			set(env.Spec.Runtime.PodSpec)
			zzSecPoolMustNotCarry(t, env)
		})
	}
}

// zzSecOverridesClient seeds the platform client with a namespace pod-spec
// overlay.
func zzSecOverridesClient(overlay string) *k8sfake.Clientset {
	return k8sfake.NewSimpleClientset(&apiv1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: "fission-pod-overrides", Namespace: "tenant-a"},
		Data:       map[string]string{"podspec": overlay},
	})
}

// zzSecPoolCannotBuild builds a pool deployment with the given pool and
// asserts that it does not carry tenant-requested privileges.
func zzSecPoolCannotBuild(t *testing.T, gp *GenericPool, env *fv1.Environment) {
	t.Helper()
	spec, err := gp.genDeploymentSpec(env)
	if err != nil || spec == nil {
		return // refused: no deployment is built
	}
	if bad := zzSecUnsafe(&spec.Template.Spec); len(bad) > 0 {
		t.Fatalf("pool deployment carries tenant-requested privileges: %v", bad)
	}
}
