package dns_test

import (
	stdnet "net"
	"testing"
)

// A resolver configured to trust a pinned CA keeps resolving while the certificate is valid for
// the host it connects to.
func TestFunc_DoHPinnedCAValidHost(t *testing.T) {
	ca := newHiddenCA(t)
	port := hiddenStartDoH(t, ca.makeLeaf(t, nil, []stdnet.IP{stdnet.ParseIP("127.0.0.1")}))
	ips, err := hiddenDoHQuery(hiddenDoHAddress(port, ca.hash()))
	if err != nil {
		t.Fatalf("a certificate valid for the connected host was rejected: %v", err)
	}
	if len(ips) == 0 {
		t.Fatalf("resolver returned no addresses")
	}
}
