package container

// Hidden functional test: a container-executor Function's pod spec keeps
// shaping the function deployment.

import (
	"context"
	"testing"

	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	k8sfake "k8s.io/client-go/kubernetes/fake"

	fv1 "github.com/fission/fission/pkg/apis/core/v1"
	"github.com/fission/fission/pkg/utils/loggerfactory"
)

func zzFnBool(b bool) *bool  { return &b }
func zzFnInt(i int64) *int64 { return &i }

func TestFuncZZContainerExecutorPodSpec(t *testing.T) {
	grace := int64(30)
	fn := &fv1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: "hello", Namespace: "tenant-a"},
		Spec: fv1.FunctionSpec{
			InvokeStrategy: fv1.InvokeStrategy{
				StrategyType: fv1.StrategyTypeExecution,
				ExecutionStrategy: fv1.ExecutionStrategy{
					ExecutorType: fv1.ExecutorTypeContainer, MinScale: 1, MaxScale: 2,
				},
			},
			PodSpec: &apiv1.PodSpec{
				TerminationGracePeriodSeconds: &grace,
				SecurityContext:               &apiv1.PodSecurityContext{RunAsNonRoot: zzFnBool(true), RunAsUser: zzFnInt(10001)},
				NodeSelector:                  map[string]string{"pool": "functions"},
				Volumes: []apiv1.Volume{{Name: "settings", VolumeSource: apiv1.VolumeSource{ConfigMap: &apiv1.ConfigMapVolumeSource{
					LocalObjectReference: apiv1.LocalObjectReference{Name: "hello-settings"}}}}},
				Containers: []apiv1.Container{{
					Name:  "hello",
					Image: "ghcr.io/tenant-a/hello:1.0",
					Ports: []apiv1.ContainerPort{{Name: "http-env", ContainerPort: 8888}},
					Env:   []apiv1.EnvVar{{Name: "GREETING", Value: "hi"}},
					SecurityContext: &apiv1.SecurityContext{
						AllowPrivilegeEscalation: zzFnBool(false),
						Capabilities:             &apiv1.Capabilities{Drop: []apiv1.Capability{"ALL"}, Add: []apiv1.Capability{"NET_BIND_SERVICE"}},
					},
					VolumeMounts: []apiv1.VolumeMount{{Name: "settings", MountPath: "/etc/settings"}},
				}},
			},
		},
	}
	cn := &Container{logger: loggerfactory.GetLogger(), kubernetesClient: k8sfake.NewSimpleClientset()}
	depl, err := cn.getDeploymentSpec(context.Background(), fn, nil, "hello-zz", fn.Namespace, map[string]string{"functionName": "hello"}, nil)
	if err != nil {
		t.Fatalf("getDeploymentSpec: %v", err)
	}
	ps := &depl.Spec.Template.Spec
	var c *apiv1.Container
	for i := range ps.Containers {
		if ps.Containers[i].Name == "hello" {
			c = &ps.Containers[i]
		}
	}
	if c == nil {
		t.Fatalf("function container missing")
	}
	if c.Image != "ghcr.io/tenant-a/hello:1.0" || len(c.Ports) == 0 {
		t.Errorf("function image/ports not applied: %q %v", c.Image, c.Ports)
	}
	greet := false
	for _, e := range c.Env {
		greet = greet || (e.Name == "GREETING" && e.Value == "hi")
	}
	if !greet {
		t.Errorf("function env not applied: %v", c.Env)
	}
	if c.SecurityContext == nil || c.SecurityContext.Capabilities == nil || len(c.SecurityContext.Capabilities.Add) != 1 ||
		c.SecurityContext.Capabilities.Add[0] != "NET_BIND_SERVICE" {
		t.Errorf("function container security context not applied: %+v", c.SecurityContext)
	}
	if ps.SecurityContext == nil || ps.SecurityContext.RunAsUser == nil || *ps.SecurityContext.RunAsUser != 10001 {
		t.Errorf("pod security context not applied: %+v", ps.SecurityContext)
	}
	if ps.NodeSelector["pool"] != "functions" {
		t.Errorf("node selector not applied: %v", ps.NodeSelector)
	}
	vol := false
	for _, v := range ps.Volumes {
		vol = vol || (v.Name == "settings" && v.ConfigMap != nil)
	}
	if !vol {
		t.Errorf("configMap volume not applied")
	}
}
