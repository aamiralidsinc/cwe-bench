package newdeploy

// Hidden security tests: the deployment the new-deploy executor builds for a
// function from an Environment object already stored in the cluster must not
// carry pod-level privileges the tenant asked for. The executor may refuse
// the object or build a pod without them.

import (
	"context"
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

func zzSecDeploy(t *testing.T) *NewDeploy {
	t.Helper()
	cfg, err := fetcherConfig.MakeFetcherConfig("/userfunc")
	if err != nil {
		t.Fatal(err)
	}
	return &NewDeploy{logger: loggerfactory.GetLogger(), kubernetesClient: k8sfake.NewSimpleClientset(), fetcherConfig: cfg}
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

func zzSecFn() *fv1.Function {
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

func zzSecNewDeployMustNotCarry(t *testing.T, env *fv1.Environment) {
	t.Helper()
	fn := zzSecFn()
	replicas := int32(1)
	depl, err := zzSecDeploy(t).getDeploymentSpec(context.Background(), fn, env, &replicas,
		"hello-zz", fn.Namespace, map[string]string{"functionName": fn.Name}, map[string]string{})
	if err != nil || depl == nil {
		return // refused: no deployment is built
	}
	if bad := zzSecUnsafe(&depl.Spec.Template.Spec); len(bad) > 0 {
		t.Fatalf("new-deploy deployment carries tenant-requested privileges: %v", bad)
	}
}

func TestSecZZNewDeployStoredRuntimePodSpec(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"hostNetwork":        func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"hostPID":            func(p *apiv1.PodSpec) { p.HostPID = true },
		"serviceAccountName": func(p *apiv1.PodSpec) { p.ServiceAccountName = zzSecMarkerSA },
		"hostPath": func(p *apiv1.PodSpec) {
			p.Volumes = []apiv1.Volume{{Name: "zz-node-dir",
				VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}}}
		},
		"privileged_container": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Privileged: zzSecBool(true)})}
		},
		"added_capability_all": func(p *apiv1.PodSpec) {
			p.Containers = []apiv1.Container{zzSecSidecar(&apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"NET_BIND_SERVICE", "ALL"}}})}
		},
	}
	for name, set := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.PodSpec = &apiv1.PodSpec{}
			set(env.Spec.Runtime.PodSpec)
			zzSecNewDeployMustNotCarry(t, env)
		})
	}
}

func TestSecZZNewDeployStoredRuntimeContainer(t *testing.T) {
	cases := map[string]*apiv1.SecurityContext{
		"privileged":               {Privileged: zzSecBool(true)},
		"allowPrivilegeEscalation": {AllowPrivilegeEscalation: zzSecBool(true)},
		"added_capability":         {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"NET_BIND_SERVICE", "SYS_ADMIN"}}},
		"added_capability_ptrace":  {Capabilities: &apiv1.Capabilities{Add: []apiv1.Capability{"cap_sys_ptrace"}}},
	}
	for name, sc := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.Container = &apiv1.Container{SecurityContext: sc}
			zzSecNewDeployMustNotCarry(t, env)
		})
	}
}

// The serialized runtime override is applied to the new-deploy pod after the
// typed pod spec; a stored Environment that carries one must not yield such
// a pod.
func TestSecZZNewDeployStoredRuntimePodSpecPatch(t *testing.T) {
	cases := map[string]string{
		"host_network":       "hostNetwork: true\n",
		"host_ipc":           "hostIPC: true\n",
		"service_account":    "serviceAccountName: zz-tenant-picked-sa\n",
		"host_path":          "volumes:\n- name: zz-node-dir\n  hostPath:\n    path: /var/zz-marker\n",
		"privileged":         "containers:\n- name: py\n  securityContext:\n    privileged: true\n",
		"added_capability":   "containers:\n- name: py\n  securityContext:\n    capabilities:\n      add: [NET_BIND_SERVICE, SYS_ADMIN]\n",
		"added_capability_all": "containers:\n- name: py\n  securityContext:\n    capabilities:\n      add: [ALL]\n",
	}
	for name, patch := range cases {
		t.Run(name, func(t *testing.T) {
			env := zzSecEnv()
			env.Spec.Runtime.PodSpecPatch = patch
			zzSecNewDeployMustNotCarry(t, env)
		})
	}
}

// The namespace's pod-spec overlay is merged into the new-deploy pod after the
// typed pod spec. A stored overlay that asks for pod-level privileges must not
// yield a deployment that carries them.
func TestSecZZNewDeployNamespacePodOverrides(t *testing.T) {
	cases := map[string]string{
		"host_network":    "hostNetwork: true\n",
		"host_pid":        "hostPID: true\n",
		"service_account": "serviceAccountName: zz-tenant-picked-sa\n",
		"host_path":       "volumes:\n- name: zz-node-dir\n  hostPath:\n    path: /var/zz-marker\n",
		"privileged":      "containers:\n- name: py\n  securityContext:\n    privileged: true\n",
		"capability_all":  "containers:\n- name: py\n  securityContext:\n    capabilities:\n      add: [NET_BIND_SERVICE, ALL]\n",
	}
	for name, overlay := range cases {
		t.Run(name, func(t *testing.T) {
			deploy := zzSecDeploy(t)
			deploy.kubernetesClient = k8sfake.NewSimpleClientset(&apiv1.ConfigMap{
				ObjectMeta: metav1.ObjectMeta{Name: "fission-pod-overrides", Namespace: "tenant-a"},
				Data:       map[string]string{"podspec": overlay},
			})
			zzSecNewDeployCannotBuild(t, deploy, zzSecEnv())
		})
	}
}

// Version-1 Environments keep the legacy pod-spec settings. A stored
// version-1 Environment that asks for pod-level privileges must not yield a
// deployment that carries them.
func TestSecZZNewDeployLegacyVersionRuntimePodSpec(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"host_network":    func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"host_ipc":        func(p *apiv1.PodSpec) { p.HostIPC = true },
		"service_account": func(p *apiv1.PodSpec) { p.ServiceAccountName = zzSecMarkerSA },
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
			zzSecNewDeployMustNotCarry(t, env)
		})
	}
}

// zzSecNewDeployCannotBuild builds a deployment with the given executor and
// asserts that it does not carry tenant-requested privileges.
func zzSecNewDeployCannotBuild(t *testing.T, deploy *NewDeploy, env *fv1.Environment) {
	t.Helper()
	fn := zzSecFn()
	replicas := int32(1)
	depl, err := deploy.getDeploymentSpec(context.Background(), fn, env, &replicas,
		"hello-zz", fn.Namespace, map[string]string{"functionName": fn.Name}, map[string]string{})
	if err != nil || depl == nil {
		return // refused: no deployment is built
	}
	if bad := zzSecUnsafe(&depl.Spec.Template.Spec); len(bad) > 0 {
		t.Fatalf("new-deploy deployment carries tenant-requested privileges: %v", bad)
	}
}
