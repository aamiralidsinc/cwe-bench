package hiddencheck

import (
	"net/http"
	"testing"
)

// A request that explicitly asks for certificate validation, without supplying an
// authority bundle, must validate against the system trust store and therefore
// must not complete a session with a self-signed endpoint.
func TestSecInspectorCredentialCheckRejectsUnverifiedServer(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = false
	code, body := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertBlocked(t, code, o, false)
	assertClientError(t, code, body)
}

// The same property holds when the connection details are nested in a request
// that starts an operation rather than a credential check.
func TestSecInspectorStartRejectsUnverifiedServer(t *testing.T) {
	s := newStack(t)
	s.seedVddk(t)
	s.seedVM(t, "vm-1", "test-vm-1")
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	req := inspectorBody(o.URL(), []string{"vm-1"})
	req["credentials"].(map[string]any)["skipTls"] = false
	code, _ := s.request(t, http.MethodPost, "/inspector", req)

	assertBlocked(t, code, o, false)
}

// The credential preflight of the forecasting feature opens its own connection;
// it must honour the same requirement.
func TestSecForecasterCredentialCheckRejectsUnverifiedServer(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = false
	code, _ := s.request(t, http.MethodPut, "/forecaster/credentials", creds)

	assertBlocked(t, code, o, false)
}

// Starting a forecast with inline credentials must not reach an endpoint the
// caller asked to validate against a trust store that does not cover it.
func TestSecForecasterStartRejectsUnverifiedServer(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	req := forecasterBody(o.URL(), map[string]any{"skipTls": false})
	code, _ := s.request(t, http.MethodPost, "/forecaster", req)

	assertBlocked(t, code, o, false)
}

// A collection run started in the background must not complete a session with
// an endpoint the caller asked to validate.
func TestSecRightsizingRejectsUnverifiedServer(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = false
	code, _ := s.request(t, http.MethodPost, "/rightsizing", map[string]any{"credentials": creds})

	assertBlocked(t, code, o, true)
}

// An inventory collection started in the background must not complete a session
// with an endpoint the caller asked to validate.
func TestSecCollectorRejectsUnverifiedServer(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["skipTls"] = false
	code, _ := s.request(t, http.MethodPost, "/collector", creds)

	assertBlocked(t, code, o, true)
}

// An authority bundle that did not issue the server's certificate must prevent
// the session even though the bundle itself is well formed.
func TestSecInspectorRejectsMismatchedAuthority(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())
	unrelated := newIdentity(t, "localhost", true)

	creds := credentials(o.URL())
	creds["cacert"] = string(unrelated.caPEM)
	code, body := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertBlocked(t, code, o, false)
	assertClientError(t, code, body)
}

// A bundle that is not a usable certificate bundle must be refused before any
// connection is attempted.
func TestSecInspectorRejectsUnusableAuthority(t *testing.T) {
	s := newStack(t)
	o := newTLSOracle(t, newIdentity(t, "localhost", true), rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = "this is not a certificate bundle"
	code, body := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertBlocked(t, code, o, false)
	assertClientError(t, code, body)
}

// A certificate that chains to the supplied bundle but is not valid for the
// requested host must still be rejected.
func TestSecInspectorRejectsCertificateForAnotherHost(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "vc.example.com", false)
	o := newTLSOracle(t, id, rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = string(id.caPEM)
	code, body := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertBlocked(t, code, o, false)
	assertClientError(t, code, body)
}

// Skipping validation while also supplying an authority bundle is contradictory
// and must be refused before any connection is attempted (nested shape).
func TestSecRightsizingRejectsConflictingOptions(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "localhost", true)
	o := newTLSOracle(t, id, rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = string(id.caPEM)
	creds["skipTls"] = true
	code, body := s.request(t, http.MethodPost, "/rightsizing", map[string]any{"credentials": creds})

	assertBlocked(t, code, o, false)
	assertClientError(t, code, body)
}

// The same contradiction is refused when the connection details are the body of
// the request.
func TestSecInspectorRejectsConflictingOptions(t *testing.T) {
	s := newStack(t)
	id := newIdentity(t, "localhost", true)
	o := newTLSOracle(t, id, rejectingBackend())

	creds := credentials(o.URL())
	creds["cacert"] = string(id.caPEM)
	creds["skipTls"] = true
	code, body := s.request(t, http.MethodPost, "/inspector/credentials", creds)

	assertBlocked(t, code, o, false)
	assertClientError(t, code, body)
}
