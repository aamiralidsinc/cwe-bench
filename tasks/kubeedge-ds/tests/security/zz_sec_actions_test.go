package actions

import (
	"context"
	"encoding/json"
	"testing"

	klog "k8s.io/klog/v2"

	operationsv1alpha2 "github.com/kubeedge/api/apis/operations/v1alpha2"
	"github.com/kubeedge/kubeedge/edge/pkg/metamanager/dao/dbclient"
)

// A node upgrade job carries a version and an image. Neither value may be interpreted by a
// shell when the edge runs the upgrade.

func TestSec_UpgradeVersionIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)
	marker := zzMarker(t)

	zzRunAction(t, newNodeUpgradeJobRunner(),
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade),
		&operationsv1alpha2.NodeUpgradeJobSpec{
			Version: "v1.23.0; touch " + marker + " #",
		})

	zzAssertNoMarker(t, marker)
}

func TestSec_UpgradeImageIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)
	marker := zzMarker(t)

	zzRunAction(t, newNodeUpgradeJobRunner(),
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade),
		&operationsv1alpha2.NodeUpgradeJobSpec{
			Version: "v1.23.0",
			Image:   "registry.example.com/team/installation-package$(touch " + marker + ")",
		})

	zzAssertNoMarker(t, marker)
}

// The same upgrade action is reached after a confirmation, when the spec is read back from
// the node's own record of the job rather than from the request that is being checked now.

func TestSec_StoredUpgradeSpecIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	zzResetStoredUpgrade(t)
	marker := zzMarker(t)

	spec := &operationsv1alpha2.NodeUpgradeJobSpec{
		Version: "v1.23.0`touch " + marker + "`",
	}
	// A fix that refuses the value where it is stored has already blocked the attack.
	if err := dbclient.NewUpgrade().Save("job", "node", spec); err != nil {
		zzAssertNoMarker(t, marker)
		return
	}
	job, node, stored, err := dbclient.NewUpgrade().Get()
	if err != nil {
		zzAssertNoMarker(t, marker)
		return
	}
	if stored == nil {
		zzAssertNoMarker(t, marker)
		return
	}
	specData, err := json.Marshal(stored)
	if err != nil {
		t.Fatal(err)
	}

	newNodeUpgradeJobRunner().RunAction(context.Background(), job, node,
		string(operationsv1alpha2.NodeUpgradeJobActionUpgrade), specData)

	zzAssertNoMarker(t, marker)
}

// A config update job carries a map of settings; the keys and the values are equally
// supplied by the submitter.

func TestSec_ConfigUpdateValueIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	marker := zzMarker(t)

	zzRunAction(t, newConfigUpdateJobRunner(),
		string(operationsv1alpha2.ConfigUpdateJobActionUpdate),
		&operationsv1alpha2.ConfigUpdateJobSpec{
			UpdateFields: map[string]string{"log.level": "info; touch " + marker + " #"},
		})

	zzAssertNoMarker(t, marker)
}

func TestSec_ConfigUpdateKeyIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	marker := zzMarker(t)

	zzRunAction(t, newConfigUpdateJobRunner(),
		string(operationsv1alpha2.ConfigUpdateJobActionUpdate),
		&operationsv1alpha2.ConfigUpdateJobSpec{
			UpdateFields: map[string]string{"log.level$(touch " + marker + ")": "info"},
		})

	zzAssertNoMarker(t, marker)
}

// An image pull job carries a list of image references.

func TestSec_ImagePrePullImageIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"crictl"}, nil)
	marker := zzMarker(t)

	spec := &operationsv1alpha2.ImagePrePullJobSpec{
		ImagePrePullTemplate: operationsv1alpha2.ImagePrePullTemplate{
			Images: []string{"registry.example.com/team/pause`touch " + marker + "`"},
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
	h.checkItems(context.Background(), "job", "node", ser)

	zzAssertNoMarker(t, marker)
}
