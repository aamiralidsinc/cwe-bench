package taskexecutor

import (
	"testing"

	api "github.com/kubeedge/api/apis/fsm/v1alpha1"
	"github.com/kubeedge/kubeedge/common/types"
)

// The legacy task path builds the upgrade command from the request it receives. The request
// fields are still supplied by the job and must not be interpreted by a shell.

func TestSec_LegacyUpgradeVersionIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	marker := zzMarker(t)

	req := types.NodeUpgradeJobRequest{
		UpgradeID: "upgrade-1",
		HistoryID: "history-1",
		Version:   "v1.23.0; touch " + marker + " #",
		Image:     "kubeedge/installation-package",
	}
	if _, err := NewUpgradeExecutor().Do(types.NodeTaskRequest{
		TaskID: "task-1",
		Type:   TaskUpgrade,
		State:  string(api.UpgradingState),
		Item:   req,
	}); err != nil {
		t.Fatal(err)
	}

	zzAssertNoMarker(t, marker)
}

func TestSec_LegacyUpgradeImageIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	marker := zzMarker(t)

	req := types.NodeUpgradeJobRequest{
		UpgradeID: "upgrade-1",
		HistoryID: "history-1",
		Version:   "v1.23.0",
		Image:     "kubeedge/installation-package$(touch " + marker + ")",
	}
	if _, err := NewUpgradeExecutor().Do(types.NodeTaskRequest{
		TaskID: "task-1",
		Type:   TaskUpgrade,
		State:  string(api.UpgradingState),
		Item:   req,
	}); err != nil {
		t.Fatal(err)
	}

	zzAssertNoMarker(t, marker)
}

// Failure recovery runs from the same request.

func TestSec_RollbackVersionIsNotExecuted(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, nil)
	marker := zzMarker(t)

	req := types.NodeUpgradeJobRequest{
		UpgradeID: "upgrade-1",
		HistoryID: "history-1",
		Version:   "v1.23.0; touch " + marker + " #",
	}
	if _, err := NewUpgradeExecutor().Do(types.NodeTaskRequest{
		TaskID: "task-1",
		Type:   TaskUpgrade,
		State:  string(api.RollingBackState),
		Item:   req,
	}); err != nil {
		t.Fatal(err)
	}

	zzAssertNoMarker(t, marker)
}
