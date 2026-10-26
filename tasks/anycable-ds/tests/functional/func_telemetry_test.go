package vtests

import (
	"context"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/anycable/anycable-go/config"
	"github.com/anycable/anycable-go/metrics"
	"github.com/anycable/anycable-go/telemetry"
)

// Legitimate telemetry keeps working when the deployment supplies its own token.

func TestFunc_SendsWithOperatorToken(t *testing.T) {
	s := newSink(t)

	caps := runServer(t, s, runOpts{
		env: []string{
			"ANYCABLE_TELEMETRY_TOKEN=operator-token",
			"ANYCABLE_SECRET=deployment-secret",
		},
	}, true)

	event, _ := bootEvent(t, caps)

	if event["event"] != "boot" {
		t.Fatalf("expected a boot event, got %v", event["event"])
	}

	if caps[0].auth != "operator-token" {
		t.Fatalf("expected the deployment token to authenticate the request, got %q", caps[0].auth)
	}

	if v, _ := event["version"].(string); v == "" {
		t.Fatalf("the boot event lost its version property: %v", event)
	}

	if v, _ := event["os"].(string); v == "" {
		t.Fatalf("the boot event lost its os property: %v", event)
	}

	if id, _ := event["distinct_id"].(string); id == "" {
		t.Fatalf("the boot event lost its distinct id: %v", event)
	}

	if v, ok := event["$ip"]; !ok || v != nil {
		t.Fatalf("the boot event must not carry an IP address, got %v", v)
	}

	if has, _ := event["has-secret"].(bool); !has {
		t.Fatalf("the configuration had a secret but the event reports has-secret=%v", event["has-secret"])
	}
}

func TestFunc_DisableEnvironmentStillSilences(t *testing.T) {
	s := newSink(t)

	caps := runServer(t, s, runOpts{
		env: []string{
			"ANYCABLE_TELEMETRY_TOKEN=operator-token",
			"ANYCABLE_DISABLE_TELEMETRY=true",
		},
	}, false)

	if len(caps) > 0 {
		t.Fatalf("the opt-out environment setting did not silence telemetry: %d request(s)", len(caps))
	}
}

func TestFunc_ConfigFileTokenEnablesTelemetry(t *testing.T) {
	dir := t.TempDir()
	cfg := filepath.Join(dir, "anycable.toml")

	body := "secret = \"deployment-secret\"\n\n[telemetry]\nenabled = true\ntoken = \"config-file-token\"\n"
	if err := os.WriteFile(cfg, []byte(body), 0o600); err != nil {
		t.Fatalf("writing the configuration file: %v", err)
	}

	s := newSink(t)

	caps := runServer(t, s, runOpts{args: []string{"--config-path=" + cfg}}, true)

	event, _ := bootEvent(t, caps)

	if caps[0].auth != "config-file-token" {
		t.Fatalf("expected the token from the configuration file to authenticate the request, got %q", caps[0].auth)
	}

	if has, _ := event["has-secret"].(bool); !has {
		t.Fatalf("the configuration had a secret but the event reports has-secret=%v", event["has-secret"])
	}
}

func TestFunc_ServerStartsAndServesHealth(t *testing.T) {
	bin := binaryPath(t)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("reserving a port: %v", err)
	}

	port := ln.Addr().(*net.TCPAddr).Port
	_ = ln.Close()

	cmd := newServerCommand(bin, []string{"--norpc", "--broadcast_adapter=http", fmt.Sprintf("--port=%d", port)},
		[]string{"ANYCABLE_DISABLE_TELEMETRY=true"})

	buf := &safeBuf{}
	cmd.Stdout = buf
	cmd.Stderr = buf

	if err := cmd.Start(); err != nil {
		t.Fatalf("starting the server failed: %v", err)
	}

	defer func() {
		_ = cmd.Process.Kill()
		_ = cmd.Wait()
	}()

	url := fmt.Sprintf("http://127.0.0.1:%d/health", port)
	client := &http.Client{Timeout: 2 * time.Second}
	deadline := time.Now().Add(30 * time.Second)

	for time.Now().Before(deadline) {
		res, err := client.Get(url)
		if err == nil {
			res.Body.Close()

			if res.StatusCode == http.StatusOK {
				return
			}
		}

		time.Sleep(50 * time.Millisecond)
	}

	t.Fatalf("the server did not serve its health endpoint; output:\n%s", buf.String())
}

func TestFunc_TrackerReportsDocumentedProperties(t *testing.T) {
	mconfig := metrics.NewConfig()

	m, err := metrics.NewFromConfig(&mconfig, slog.Default())
	if err != nil {
		t.Fatalf("initializing metrics: %v", err)
	}

	m.RegisterGauge("clients_num", "")
	m.RegisterGauge("mem_sys_bytes", "")
	m.GaugeSet("clients_num", 10)
	m.GaugeSet("mem_sys_bytes", 100)

	s := newSink(t)

	conf := config.NewConfig()
	conf.Secret = "deployment-secret"

	tconf := telemetry.NewConfig()
	tconf.Token = "operator-token"
	tconf.Endpoint = s.server.URL
	tconf.CustomProps["distro"] = "testo"

	tracker := telemetry.NewTracker(m, &conf, tconf)
	tracker.Collect()

	defer func() {
		_ = tracker.Shutdown(context.Background())
	}()

	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) && s.count() == 0 {
		time.Sleep(20 * time.Millisecond)
	}

	caps := s.snapshot()
	event, _ := bootEvent(t, caps)

	if event["event"] != "boot" {
		t.Fatalf("expected a boot event, got %v", event["event"])
	}

	if event["distro"] != "testo" {
		t.Fatalf("custom telemetry properties were lost: %v", event["distro"])
	}

	if v, _ := event["version"].(string); v == "" {
		t.Fatalf("the boot event lost its version property: %v", event)
	}

	if has, _ := event["has-secret"].(bool); !has {
		t.Fatalf("the configuration had a secret but the event reports has-secret=%v", event["has-secret"])
	}
}
