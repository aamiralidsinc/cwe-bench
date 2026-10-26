package hiddencheck

import (
	"net/http"
	"testing"
)

// Requests that say nothing about certificates keep the behaviour the product
// has today: the connection is made without validating the server certificate.
func TestFuncInspectorCredentialCheckWithoutOptionsKeepsCurrentBehaviour(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	code, _ := s.request(t, http.MethodPost, "/inspector/credentials", credentials(o.URL()))

	assertConnected(t, o, false)
	_ = code
}

// Explicitly skipping validation keeps connecting to self-signed endpoints.
func TestFuncInspectorCredentialCheckWithExplicitSkip(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = true
	code, _ := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertConnected(t, o, false)
	_ = code
}

// A well formed authority bundle that did issue the server certificate is used
// for validation and the connection is established.
func TestFuncInspectorCredentialCheckWithAuthorityBundle(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "localhost", true)
	o := newTLSOracle(t, id, rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = string(id.caPEM)
	code, _ := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertConnected(t, o, false)
	_ = code
}

// Supplying an authority bundle together with an explicit request to validate
// is the ordinary verified configuration and keeps working.
func TestFuncInspectorCredentialCheckWithBundleAndExplicitVerify(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "localhost", true)
	o := newTLSOracle(t, id, rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = string(id.caPEM)
	creds["skipTls"] = false
	code, _ := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertConnected(t, o, false)
	_ = code
}

// The forecasting credential preflight works with a supplied authority bundle.
func TestFuncForecasterCredentialCheckWithAuthorityBundle(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "localhost", true)
	o := newTLSOracle(t, id, rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = string(id.caPEM)
	code, _ := s.request(t, http.MethodPut, "/forecaster/credentials", creds)

	assertConnected(t, o, false)
	_ = code
}

// A background collection that explicitly skips validation keeps connecting.
func TestFuncRightsizingWithExplicitSkip(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = true
	code, _ := s.request(t, http.MethodPost, "/rightsizing", map[string]any{"credentials": creds})

	assertConnected(t, o, true)
	_ = code
}

// A background inventory collection that explicitly skips validation keeps
// connecting.
func TestFuncCollectorWithExplicitSkip(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = true
	code, _ := s.request(t, http.MethodPost, "/collector", creds)

	assertConnected(t, o, true)
	_ = code
}

// Verification against a supplied bundle works end to end against a vCenter
// that presents a certificate issued by that bundle.
func TestFuncInspectorStartWithAuthorityBundle(t *testing.T) {
	s := newStack(t)
	s.seedVddk(t)
	s.seedVM(t, "vm-1", "test-vm-1")
	id := newIdentity(t, "localhost", true)
	backend, closeBackend := liveBackend(t)
	t.Cleanup(closeBackend)
	o := newTLSOracle(t, id, backend)

	req := inspectorBody(o.URL(), []string{"vm-1"})
	req["credentials"].(map[string]any)["cacert"] = string(id.caPEM)
	code, body := s.request(t, http.MethodPost, "/inspector", req)
	if code != http.StatusAccepted {
		t.Fatalf("expected the inspection to start, got %d: %s", code, body)
	}
	assertConnected(t, o, false)
	_, _ = s.request(t, http.MethodDelete, "/inspector", nil)
}

// A forecast started with a verified connection works end to end against a
// vCenter that presents a certificate issued by the supplied bundle.
func TestFuncForecasterStartWithAuthorityBundle(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "localhost", true)
	backend, closeBackend := liveBackend(t)
	t.Cleanup(closeBackend)
	o := newTLSOracle(t, id, backend)

	req := forecasterBody(o.URL(), map[string]any{"cacert": string(id.caPEM)})
	code, body := s.request(t, http.MethodPost, "/forecaster", req)
	if code != http.StatusAccepted {
		t.Fatalf("expected the forecast to start, got %d: %s", code, body)
	}
	assertConnected(t, o, false)
	_, _ = s.request(t, http.MethodDelete, "/forecaster", nil)
}
