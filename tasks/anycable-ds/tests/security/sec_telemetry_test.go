package vtests

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// The server must not contact the telemetry service unless this deployment has been given its own
// telemetry token. A compiled-in or shipped default is not the deployment's own.

func TestSec_StockStartSendsNoTelemetry(t *testing.T) {
	s := newSink(t)

	caps := runServer(t, s, runOpts{}, false)

	if len(caps) > 0 {
		t.Fatalf("a stock start with no telemetry token sent %d telemetry request(s); first credential %q",
			len(caps), caps[0].auth)
	}
}

// Enabling telemetry through configuration without giving the deployment a token must not fall
// back to a credential that ships with the product.
func TestSec_ConfigOptInWithoutTokenSendsNoTelemetry(t *testing.T) {
	dir := t.TempDir()
	cfg := filepath.Join(dir, "anycable.toml")

	if err := os.WriteFile(cfg, []byte("[telemetry]\nenabled = true\n"), 0o600); err != nil {
		t.Fatalf("writing the configuration file: %v", err)
	}

	s := newSink(t)

	caps := runServer(t, s, runOpts{args: []string{"--config-path=" + cfg}}, false)

	if len(caps) > 0 {
		t.Fatalf("a configuration that enables telemetry without a token sent %d request(s); first credential %q",
			len(caps), caps[0].auth)
	}
}

// A secret supplied through the environment must not influence what is sent.
func TestSec_EnvironmentSecretNotDerived(t *testing.T) {
	s := newSink(t)

	run := func(secret string) map[string]any {
		caps := runServer(t, s, runOpts{
			env: []string{
				"ANYCABLE_TELEMETRY_TOKEN=operator-token",
				"ANYCABLE_SECRET=" + secret,
			},
		}, true)

		event, _ := bootEvent(t, caps)

		return event
	}

	a := run("alpha-environment-secret")
	a2 := run("alpha-environment-secret")
	b := run("beta-environment-secret")

	assertSecretInvariant(t, a, a2, b, "the secret supplied through the environment")
}

// A secret supplied on the command line must not influence what is sent.
func TestSec_ArgumentSecretNotDerived(t *testing.T) {
	s := newSink(t)

	run := func(secret string) map[string]any {
		caps := runServer(t, s, runOpts{
			env:  []string{"ANYCABLE_TELEMETRY_TOKEN=operator-token"},
			args: []string{"--secret=" + secret},
		}, true)

		event, _ := bootEvent(t, caps)

		return event
	}

	a := run("alpha-argument-secret")
	a2 := run("alpha-argument-secret")
	b := run("beta-argument-secret")

	assertSecretInvariant(t, a, a2, b, "the secret supplied as a command-line option")
}

// A secret supplied through the configuration file must not influence what is sent.
func TestSec_ConfigFileSecretNotDerived(t *testing.T) {
	dir := t.TempDir()
	cfg := filepath.Join(dir, "anycable.toml")

	write := func(secret string) {
		t.Helper()

		body := fmt.Sprintf("secret = %q\n", secret)
		if err := os.WriteFile(cfg, []byte(body), 0o600); err != nil {
			t.Fatalf("writing the configuration file: %v", err)
		}
	}

	s := newSink(t)

	run := func(secret string) map[string]any {
		write(secret)

		caps := runServer(t, s, runOpts{
			env:  []string{"ANYCABLE_TELEMETRY_TOKEN=operator-token"},
			args: []string{"--config-path=" + cfg},
		}, true)

		event, _ := bootEvent(t, caps)

		return event
	}

	a := run("alpha-file-secret")
	a2 := run("alpha-file-secret")
	b := run("beta-file-secret")

	assertSecretInvariant(t, a, a2, b, "the secret supplied in the configuration file")
}

// A credential embedded inside a larger configured value must not reach the service either raw
// or in derived form.
func TestSec_EmbeddedCredentialNotDerived(t *testing.T) {
	s := newSink(t)

	run := func(password string) map[string]any {
		url := "redis://:" + password + "@127.0.0.1:6379/0"

		caps := runServer(t, s, runOpts{
			env:  []string{"ANYCABLE_TELEMETRY_TOKEN=operator-token"},
			args: []string{"--redis_url=" + url},
		}, true)

		event, body := bootEvent(t, caps)

		if strings.Contains(string(body), password) {
			t.Fatalf("the telemetry payload contains the credential configured inside another value")
		}

		return event
	}

	a := run("AlphaPasswordMarker1")
	a2 := run("AlphaPasswordMarker1")
	b := run("BetaPasswordMarker2")

	assertSecretInvariant(t, a, a2, b, "the credential embedded in a configured value")
}
