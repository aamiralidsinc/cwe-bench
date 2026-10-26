package realm_test

import (
	"testing"
)

// A pinned-CA HTTPS client used by a rendezvous helper must refuse a certificate issued by the
// pinned CA for a host other than the one it connects to.
func TestSec_RealmPinnedCAWrongHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartRealmServer(t, ca.makeLeaf(t, []string{"unrelated.example"}, nil))
	defer stop()

	if err := hiddenRegister(hiddenRealmClient(port, ca.hash())); err == nil {
		t.Fatalf("a certificate issued by the pinned CA for unrelated.example was accepted")
	}
}
