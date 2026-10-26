package taskexecutor

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	api "github.com/kubeedge/api/apis/fsm/v1alpha1"
	"github.com/kubeedge/kubeedge/common/types"
)

func zzIsUpgrade(args []string) bool {
	return len(args) > 0 && args[0] == "upgrade"
}

func zzIsRollback(args []string) bool {
	return len(args) > 0 && args[0] == "rollback"
}

// An ordinary legacy upgrade still hands the tool the request values, detached from the agent,
// with the output in the same log file.

func TestFunc_LegacyUpgradeIsDetachedAndLogged(t *testing.T) {
	zzInstallFakes(t, []string{"keadm"}, map[string]string{"ZZ_FAKE_KEADM_SLEEP": "6"})
	token := os.Getenv("ZZ_FAKE_TOKEN")
	_ = os.Remove("/tmp/keadm.log")

	req := types.NodeUpgradeJobRequest{
		UpgradeID: "upgrade-1",
		HistoryID: "history-1",
		Version:   "v1.24.0",
		Image:     "registry.example.com/team/installation-package",
	}
	start := time.Now()
	if _, err := NewUpgradeExecutor().Do(types.NodeTaskRequest{
		TaskID: "task-1",
		Type:   TaskUpgrade,
		State:  string(api.UpgradingState),
		Item:   req,
	}); err != nil {
		t.Fatal(err)
	}
	if elapsed := time.Since(start); elapsed > 4*time.Second {
		t.Fatalf("the upgrade command was not started detached from the agent: Do blocked for %v", elapsed)
	}

	deadline := time.Now().Add(40 * time.Second)
	want := "fake-keadm-ran " + token
	for {
		data, err := os.ReadFile("/tmp/keadm.log")
		if err == nil && strings.Contains(string(data), want) {
			break
		}
		if time.Now().After(deadline) {
			t.Fatalf("the upgrade output did not reach /tmp/keadm.log (err %v, content %q)", err, string(data))
		}
		time.Sleep(50 * time.Millisecond)
	}
}

func TestFunc_LegacyUpgradeArguments(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)
	image := "registry.example.com:5000/team/installation-package:v1.24.0"

	req := types.NodeUpgradeJobRequest{
		UpgradeID: "upgrade-1",
		HistoryID: "history-1",
		Version:   "v1.24.0-rc.1",
		Image:     image,
	}
	if _, err := NewUpgradeExecutor().Do(types.NodeTaskRequest{
		TaskID: "task-1",
		Type:   TaskUpgrade,
		State:  string(api.UpgradingState),
		Item:   req,
	}); err != nil {
		t.Fatal(err)
	}

	args := zzWaitInvocation(t, records, "keadm", zzIsUpgrade)
	if len(args) < 2 || args[1] != "edge" {
		t.Fatalf("upgrade arguments = %v, want upgrade edge ...", args)
	}
	for flag, want := range map[string]string{
		"--upgradeID": "upgrade-1",
		"--historyID": "history-1",
		"--toVersion": "v1.24.0-rc.1",
		"--image":     image,
	} {
		if got := zzFlagValue(args, flag); got != want {
			t.Fatalf("%s = %q, want %q (arguments %v)", flag, got, want, args)
		}
	}
	for _, flag := range []string{"--fromVersion", "--config"} {
		if zzFlagValue(args, flag) == "" {
			t.Fatalf("%s is missing from the arguments %v", flag, args)
		}
	}
}

// Failure recovery still removes the files of the failed upgrade and still runs the rollback.

func TestFunc_RollbackCleansFailedUpgrade(t *testing.T) {
	records := zzInstallFakes(t, []string{"keadm"}, nil)

	dir := filepath.Join("/etc/kubeedge/upgrade", "v1.22.0")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatalf("prepare the failed upgrade directory: %v", err)
	}
	t.Cleanup(func() { os.RemoveAll(dir) })
	if err := os.WriteFile(filepath.Join(dir, "edgecore"), []byte("stale"), 0o644); err != nil {
		t.Fatal(err)
	}

	req := types.NodeUpgradeJobRequest{
		UpgradeID: "upgrade-1",
		HistoryID: "history-1",
		Version:   "v1.22.0",
	}
	if _, err := NewUpgradeExecutor().Do(types.NodeTaskRequest{
		TaskID: "task-1",
		Type:   TaskUpgrade,
		State:  string(api.RollingBackState),
		Item:   req,
	}); err != nil {
		t.Fatal(err)
	}

	deadline := time.Now().Add(15 * time.Second)
	for {
		_, err := os.Stat(dir)
		if os.IsNotExist(err) {
			break
		}
		if time.Now().After(deadline) {
			t.Fatalf("the failed upgrade directory %s was not removed (stat err %v)", dir, err)
		}
		time.Sleep(50 * time.Millisecond)
	}

	zzWaitInvocation(t, records, "keadm", zzIsRollback)
}
