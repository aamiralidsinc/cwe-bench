// Package refusal: refusal-tolerant assertions for Go security tests. Copy into tests/support/refusal/.
//
// A security test that drives a hardened entry point must accept every secure outcome the instruction allows:
// the call is refused (a client error, or one of the product's own refusal errors), or it completes and leaves
// nothing unsafe behind. A crash is not a refusal: a 5xx, a panic, or an error outside the declared refusal
// checks fails the test, so a fix that merely breaks the call is still caught (wrong-fix class crash_as_refusal).
//
//	out := refusal.Do(t, func() (int, error) { rec := serve(req); return rec.Code, nil })
//	if !out.Refused { assertNoSecret(t, body) }
//	assertNothingReached(t)   // side effects are checked after every outcome
//
//	refusal.Do(t, func() (int, error) { return 0, store.Put(key, v) },
//	    func(err error) bool { return errors.Is(err, store.ErrForbidden) })
package refusal

import (
	"fmt"
	"testing"
)

// Outcome is what one call did.
type Outcome struct {
	Refused bool
	Status  int
	Err     error
	Reason  string
}

// Do runs call, which returns an HTTP-like status (0 when there is none) and an error. The call is refused when
// the status is a client error (4xx) or the error matches one of the refusal checks. A 5xx, a panic, or any other
// error fails the test.
func Do(t testing.TB, call func() (int, error), refusals ...func(error) bool) (out Outcome) {
	t.Helper()
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("the call panicked (%v): a crash is not a refusal", r)
		}
	}()
	status, err := call()
	out.Status, out.Err = status, err
	switch {
	case status >= 400 && status < 500:
		out.Refused, out.Reason = true, fmt.Sprintf("status %d", status)
		return out
	case status >= 500:
		t.Fatalf("server error %d: a crash is not a refusal", status)
	}
	if err != nil {
		for _, r := range refusals {
			if r(err) {
				out.Refused, out.Reason = true, err.Error()
				return out
			}
		}
		t.Fatalf("unexpected error (not a declared refusal): %v", err)
	}
	return out
}

// MustRefuse passes only when the call is refused.
func MustRefuse(t testing.TB, call func() (int, error), refusals ...func(error) bool) Outcome {
	t.Helper()
	out := Do(t, call, refusals...)
	if !out.Refused {
		t.Fatalf("expected a refusal (a client error or a refusal error), the call completed")
	}
	return out
}
