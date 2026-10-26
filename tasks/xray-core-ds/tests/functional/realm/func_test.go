package realm_test

import (
	stdnet "net"
	"testing"
)

// A pinned-CA HTTPS client must keep working when the certificate is valid for the host it
// connects to.
func TestFunc_RealmPinnedCAValidHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartRealmServer(t, ca.makeLeaf(t, nil, []stdnet.IP{stdnet.ParseIP("127.0.0.1")}))
	defer stop()

	if err := hiddenRegister(hiddenRealmClient(port, ca.hash())); err != nil {
		t.Fatalf("a certificate valid for the connected host was rejected: %v", err)
	}
}
