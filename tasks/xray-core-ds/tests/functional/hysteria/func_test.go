package hysteria_test

import (
	stdnet "net"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
)

// A pinned-CA QUIC connection must keep working when the certificate is valid for the dialed
// address.
func TestFunc_HysteriaPinnedCAValidHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartHysteria(t, ca.makeLeaf(t, nil, []stdnet.IP{stdnet.ParseIP("127.0.0.1")}))
	defer stop()

	settings := hiddenHysteriaClientSettings(ca.hash())
	conn, err := hiddenDialHysteria(t, xnet.TCPDestination(xnet.LocalHostIP, port), settings, 10*time.Second)
	if err != nil {
		t.Fatalf("a certificate valid for the dialed address was rejected: %v", err)
	}
	defer conn.Close()
	if _, err := conn.Write([]byte("ping")); err != nil {
		t.Fatalf("write failed: %v", err)
	}
	_ = conn.SetReadDeadline(time.Now().Add(5 * time.Second))
	b := make([]byte, 64)
	if _, err := conn.Read(b); err != nil {
		t.Fatalf("read failed: %v", err)
	}
}
