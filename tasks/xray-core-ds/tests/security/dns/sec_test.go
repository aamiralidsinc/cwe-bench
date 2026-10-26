package dns_test

import (
	"testing"
)

// A resolver configured to trust a pinned CA must refuse a certificate issued by that CA for a
// host other than the one it connects to.
func TestSec_DoHPinnedCAWrongHost(t *testing.T) {
	ca := newHiddenCA(t)
	port := hiddenStartDoH(t, ca.makeLeaf(t, []string{"unrelated.example"}, nil))
	ips, err := hiddenDoHQuery(hiddenDoHAddress(port, ca.hash()))
	if err == nil {
		t.Fatalf("a certificate issued by the pinned CA for unrelated.example was accepted: %v", ips)
	}
}
