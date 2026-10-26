package hysteria_test

import (
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
)

// A QUIC client that pins a CA must refuse a server certificate issued by that CA for a host
// other than the one it dials, even though the QUIC stack fills in the server name for its own
// handshake copy.
func TestSec_HysteriaPinnedCAWrongHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartHysteria(t, ca.makeLeaf(t, []string{"unrelated.example"}, nil))
	defer stop()

	settings := hiddenHysteriaClientSettings(ca.hash())
	conn, err := hiddenDialHysteria(t, xnet.TCPDestination(xnet.LocalHostIP, port), settings, 20*time.Second)
	if err == nil {
		defer conn.Close()
		_, _ = conn.Write([]byte("ping"))
		_ = conn.SetReadDeadline(time.Now().Add(3 * time.Second))
		b := make([]byte, 64)
		_, _ = conn.Read(b)
		t.Fatalf("a certificate issued by the pinned CA for unrelated.example was accepted")
	}
}
