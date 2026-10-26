package actions

import (
	"context"
	"encoding/json"
	"reflect"
	"sort"
	"strings"
	"testing"

	klog "k8s.io/klog/v2"

	operationsv1alpha2 "github.com/kubeedge/api/apis/operations/v1alpha2"
	"github.com/kubeedge/kubeedge/edge/pkg/metamanager/dao/dbclient"
)

func zzIsUpgrade(args []string) bool {
	return len(args) > 0 && args[0] == "upgrade"
}

// Ordinary upgrade jobs keep working and keep handing the tools the same arguments.

func TestFunc_UpgradePassesVersionAndImage(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)
	image := "registry.example.com:5000/team/installation-package:v1.23.0"

	zzRunAction(t, newNodeUpgradeJobRunner(),
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade),
		&operationsv1alpha2.NodeUpgradeJobSpec{Version: "v1.23.0", Image: image})

	got := zzWaitInvocation(t, records, "keadm", zzIsUpgrade)
	want := []string{"upgrade", "edge", "--force", "--toVersion", "v1.23.0", "--image", image}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("upgrade arguments = %v, want %v", got, want)
	}
}

func TestFunc_UpgradePrereleaseWithoutImage(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)

	zzRunAction(t, newNodeUpgradeJobRunner(),
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade),
		&operationsv1alpha2.NodeUpgradeJobSpec{Version: "v1.24.0-rc.1"})

	got := zzWaitInvocation(t, records, "keadm", zzIsUpgrade)
	want := []string{"upgrade", "edge", "--force", "--toVersion", "v1.24.0-rc.1"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("upgrade arguments = %v, want %v", got, want)
	}
}

func TestFunc_UpgradeDigestImage(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)
	image := "registry.example.com/kubeedge/installation-package@sha256:" + strings.Repeat("a", 64)

	zzRunAction(t, newNodeUpgradeJobRunner(),
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade),
		&operationsv1alpha2.NodeUpgradeJobSpec{Version: "v1.24.0", Image: image})

	got := zzWaitInvocation(t, records, "keadm", zzIsUpgrade)
	want := []string{"upgrade", "edge", "--force", "--toVersion", "v1.24.0", "--image", image}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("upgrade arguments = %v, want %v", got, want)
	}
}

// A legitimate job that went through confirmation is executed from the stored spec with the
// same arguments.

func TestFunc_StoredUpgradeSpecStillRuns(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)
	image := "registry.example.com/team/installation-package"

	spec := &operationsv1alpha2.NodeUpgradeJobSpec{Version: "v1.25.0", Image: image}
	if err := dbclient.NewUpgrade().Save("job", "node", spec); err != nil {
		t.Fatal(err)
	}
	job, node, stored, err := dbclient.NewUpgrade().Get()
	if err != nil {
		t.Fatal(err)
	}
	if stored == nil {
		t.Fatal("the stored upgrade spec was not returned")
	}
	specData, err := json.Marshal(stored)
	if err != nil {
		t.Fatal(err)
	}
	newNodeUpgradeJobRunner().RunAction(context.Background(), job, node,
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade), specData)

	got := zzWaitInvocation(t, records, "keadm", zzIsUpgrade)
	want := []string{"upgrade", "edge", "--force", "--toVersion", "v1.25.0", "--image", image}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("upgrade arguments = %v, want %v", got, want)
	}
}

func TestFunc_ConfigUpdatePassesAllPairs(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)

	zzRunAction(t, newConfigUpdateJobRunner(),
		string(operationsv1alpha2.ConfigUpdateJobActionUpdate),
		&operationsv1alpha2.ConfigUpdateJobSpec{
			UpdateFields: map[string]string{"log.level": "info", "modules.edged.enable": "true"},
		})

	got := zzWaitInvocation(t, records, "keadm", func(args []string) bool {
		return len(args) > 0 && args[0] == "config-update"
	})
	if len(got) != 3 || got[0] != "config-update" || got[1] != "--set" {
		t.Fatalf("config-update arguments = %v, want [config-update --set <pairs>]", got)
	}
	pairs := strings.Split(got[2], ",")
	sort.Strings(pairs)
	want := []string{"log.level=info", "modules.edged.enable=true"}
	if !reflect.DeepEqual(pairs, want) {
		t.Fatalf("config-update pairs = %v, want %v", pairs, want)
	}
}

// A pre-pull job still reports which of its images are already present.

func TestFunc_ImagePrePullProbesImages(t *testing.T) {
	records := zzInstallFakes(t, []string{"crictl"}, nil)
	img := "registry.example.com/team/pause:v1.0"

	spec := &operationsv1alpha2.ImagePrePullJobSpec{
		ImagePrePullTemplate: operationsv1alpha2.ImagePrePullTemplate{
			Images: []string{img},
		},
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	h := imagePrePullJobActionHandler{logger: klog.Background()}
	ser, err := h.getSpecSerializer(data)
	if err != nil {
		t.Fatal(err)
	}
	if resp := h.checkItems(context.Background(), "job", "node", ser); resp.Error() != nil {
		t.Fatalf("image pre-pull check reported %v", resp.Error())
	}

	got := zzWaitInvocation(t, records, "crictl", func(args []string) bool {
		return len(args) > 0 && args[0] == "inspecti"
	})
	want := []string{"inspecti", img}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("crictl arguments = %v, want %v", got, want)
	}
}
