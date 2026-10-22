package container

// Hidden security tests: the deployment the container executor builds for a
// Function object already stored in the cluster must not carry pod-level
// privileges the tenant asked for in the function's pod spec. The executor
// may refuse the object or build a pod without them.

import (
	"context"
	"strings"
	"testing"

	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	k8sfake "k8s.io/client-go/kubernetes/fake"

	fv1 "github.com/fission/fission/pkg/apis/core/v1"
	"github.com/fission/fission/pkg/utils/loggerfactory"
)

const zzSecMarkerSA = "zz-tenant-picked-sa"

// zzSecAdminCaps are capabilities that grant administrative or cross-process
// power (ALL includes them all).
var zzSecAdminCaps = map[string]bool{"SYS_ADMIN": true, "NET_ADMIN": true, "SYS_PTRACE": true, "SYS_MODULE": true, "ALL": true}

func zzSecBool(b bool) *bool { return &b }

func zzSecFn() *fv1.Function {
	grace := int64(30)
	return &fv1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: "hello", Namespace: "tenant-a"},
		Spec: fv1.FunctionSpec{
			InvokeStrategy: fv1.InvokeStrategy{
				StrategyType: fv1.StrategyTypeExecution,
				ExecutionStrategy: fv1.ExecutionStrategy{
					ExecutorType: fv1.ExecutorTypeContainer,
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

func TestSecZZContainerExecutorStoredFunctionPodSpec(t *testing.T) {
	cases := map[string]func(*apiv1.PodSpec){
		"hostNetwork":        func(p *apiv1.PodSpec) { p.HostNetwork = true },
		"hostIPC":            func(p *apiv1.PodSpec) { p.HostIPC = true },
		"serviceAccountName": func(p *apiv1.PodSpec) { p.ServiceAccountName = zzSecMarkerSA },
		"serviceAccount":     func(p *apiv1.PodSpec) { p.DeprecatedServiceAccount = zzSecMarkerSA },
		"hostPath": func(p *apiv1.PodSpec) {
			p.Volumes = []apiv1.Volume{{Name: "zz-node-dir",
				VolumeSource: apiv1.VolumeSource{HostPath: &apiv1.HostPathVolumeSource{Path: "/var/zz-marker"}}}}
		},
		"privileged": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Privileged: zzSecBool(true)}
		},
		"added_capability": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"SYS_ADMIN"}}}
		},
		"added_capability_all": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"ALL"}}}
		},
		"added_capability_sys_module": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"SYS_MODULE"}}}
		},
		"added_capability_lowercase": func(p *apiv1.PodSpec) {
			p.Containers[0].SecurityContext = &apiv1.SecurityContext{Capabilities: &apiv1.Capabilities{
				Add: []apiv1.Capability{"sys_ptrace"}}}
		},
	}
	for name, set := range cases {
		t.Run(name, func(t *testing.T) {
			fn := zzSecFn()
			set(fn.Spec.PodSpec)
			cn := &Container{logger: loggerfactory.GetLogger(), kubernetesClient: k8sfake.NewSimpleClientset()}
			labels := map[string]string{"functionName": fn.Name}
			depl, err := cn.getDeploymentSpec(context.Background(), fn, nil, "hello-zz", fn.Namespace, labels, nil)
			if err != nil || depl == nil {
				return // refused
			}
			if bad := zzSecUnsafe(&depl.Spec.Template.Spec); len(bad) > 0 {
				t.Fatalf("function deployment carries tenant-requested privileges: %v", bad)
			}
		})
	}
}
