package taskexecutor

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	cfgv1alpha2 "github.com/kubeedge/api/apis/componentconfig/edgecore/v1alpha2"
	"github.com/kubeedge/kubeedge/edge/cmd/edgecore/app/options"
	"github.com/kubeedge/kubeedge/edge/pkg/metamanager/dao"
)

// The suites drive the real task executor. The tools it invokes (keadm) are replaced by a
// recorder on PATH; the tests read, as data, the arguments the edge handed over.

const zzFakeToolScript = `#!/usr/bin/env python3
import json, os, sys, time
tool = os.path.basename(sys.argv[0])
rec = os.environ.get("ZZ_FAKE_RECORD_DIR")
if rec:
    with open(os.path.join(rec, tool + ".jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(sys.argv[1:]) + "\n")
if tool == "keadm" and os.environ.get("ZZ_FAKE_KEADM_SLEEP"):
    time.sleep(float(os.environ["ZZ_FAKE_KEADM_SLEEP"]))
print("fake-" + tool + "-ran " + os.environ.get("ZZ_FAKE_TOKEN", ""), flush=True)
`

func TestMain(m *testing.M) {
	dir, err := os.MkdirTemp("", "zz-executor-")
	if err != nil {
		panic(err)
	}
	options.NewEdgeCoreOptions()
	dao.Init(filepath.Join(dir, "edgecore.db"), &cfgv1alpha2.MetaManager{Enable: true})

	code := m.Run()
	os.RemoveAll(dir)
	os.Exit(code)
}

func zzToken(t *testing.T) string {
	t.Helper()
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		t.Fatal(err)
	}
	return hex.EncodeToString(b)
}

func zzInstallFakes(t *testing.T, tools []string, extraEnv map[string]string) string {
	t.Helper()
	dir := t.TempDir()
	script := filepath.Join(dir, "recorder")
	if err := os.WriteFile(script, []byte(zzFakeToolScript), 0o755); err != nil {
		t.Fatal(err)
	}
	for _, name := range tools {
		if err := os.Symlink("recorder", filepath.Join(dir, name)); err != nil {
			t.Fatal(err)
		}
	}
	records := filepath.Join(dir, "records")
	if err := os.Mkdir(records, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("ZZ_FAKE_RECORD_DIR", records)
	t.Setenv("ZZ_FAKE_TOKEN", "tok-"+zzToken(t))
	t.Setenv("PATH", dir+string(os.PathListSeparator)+os.Getenv("PATH"))
	for k, v := range extraEnv {
		t.Setenv(k, v)
	}
	return records
}

func zzReadInvocations(t *testing.T, records, tool string) [][]string {
	t.Helper()
	data, err := os.ReadFile(filepath.Join(records, tool+".jsonl"))
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		t.Fatal(err)
	}
	var out [][]string
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		if line == "" {
			continue
		}
		var args []string
		if err := json.Unmarshal([]byte(line), &args); err != nil {
			// A concurrent append can leave a partial last line; ignore it and re-read.
			continue
		}
		out = append(out, args)
	}
	return out
}

func zzWaitInvocation(t *testing.T, records, tool string, match func([]string) bool) []string {
	t.Helper()
	deadline := time.Now().Add(40 * time.Second)
	for time.Now().Before(deadline) {
		for _, args := range zzReadInvocations(t, records, tool) {
			if match(args) {
				return args
			}
		}
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatalf("no %s invocation matched within the deadline; saw %v", tool,
		zzReadInvocations(t, records, tool))
	return nil
}

// zzFlagValue returns the value following flag in args, or "".
func zzFlagValue(args []string, flag string) string {
	for i := 0; i+1 < len(args); i++ {
		if args[i] == flag {
			return args[i+1]
		}
	}
	return ""
}

func zzMarker(t *testing.T) string {
	t.Helper()
	return filepath.Join(t.TempDir(), "pwned")
}

func zzAssertNoMarker(t *testing.T, marker string) {
	t.Helper()
	if _, err := os.Stat(marker); err == nil {
		t.Fatalf("a value supplied by the job submitter was interpreted by the shell: %s exists", marker)
	} else if !os.IsNotExist(err) {
		t.Fatalf("stat %s: %v", marker, err)
	}
}
