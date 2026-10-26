package tcp_test

import (
	"context"
	stdnet "net"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/tcp"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

// When a client pins a CA but the connection carries no usable server name, a certificate issued
// by the pinned CA for an unrelated host must not be accepted.
func TestSec_TCPPinnedCAWithoutKnownHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartTCP(t, "127.0.0.1", ca.makeLeaf(t, []string{"unrelated.example"}, nil))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{ServerName: "fromMitm", PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	conn, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.LocalHostIP, port), settings)
	if err != nil {
		return
	}
	defer conn.Close()
	// The first write performs the TLS handshake; a nil error means the certificate was accepted.
	if _, err := conn.Write([]byte("ping")); err == nil {
		t.Fatalf("a certificate issued by the pinned CA for unrelated.example was accepted")
	}
}

// The host a client validates against must be the host of the connection it is opening, not a
// host it validated earlier with the same settings.
func TestSec_TCPPinnedCASecondDestination(t *testing.T) {
	ca := newHiddenCA(t)
	certA := ca.makeLeaf(t, nil, []stdnet.IP{stdnet.ParseIP("127.0.0.1")})
	portA, stopA := hiddenStartTCP(t, "127.0.0.1", certA)
	defer stopA()
	portB, stopB := hiddenStartTCP(t, "127.0.0.2", certA)
	defer stopB()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	first, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.ParseAddress("127.0.0.1"), portA), settings)
	if err != nil {
		t.Fatalf("first destination failed: %v", err)
	}
	if _, err := first.Write([]byte("ping")); err != nil {
		t.Fatalf("first destination handshake failed: %v", err)
	}
	_ = first.Close()

	second, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.ParseAddress("127.0.0.2"), portB), settings)
	if err != nil {
		return
	}
	defer second.Close()
	if _, err := second.Write([]byte("ping")); err == nil {
		t.Fatalf("a certificate valid only for 127.0.0.1 was accepted when dialing 127.0.0.2")
	}
}
