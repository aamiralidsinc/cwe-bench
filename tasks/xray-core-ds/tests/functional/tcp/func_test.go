package tcp_test

import (
	"context"
	stdnet "net"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/common/session"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/tcp"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

// A configured server name keeps being the expected host.
func TestFunc_TCPPinnedCAConfiguredName(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartTCP(t, "127.0.0.1", ca.makeLeaf(t, []string{"tls.example"}, nil))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{ServerName: "tls.example", PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	conn, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.LocalHostIP, port), settings)
	if err != nil {
		t.Fatalf("dial failed: %v", err)
	}
	defer conn.Close()
	if err := hiddenTCPRoundTrip(conn); err != nil {
		t.Fatalf("round trip failed: %v", err)
	}
}

// Pinning the server's own certificate is a direct identity check: it must keep working when the
// connection has no host name to validate.
func TestFunc_TCPPinnedLeafWithoutKnownHost(t *testing.T) {
	ca := newHiddenCA(t)
	leaf := ca.makeLeaf(t, []string{"leaf-only.example"}, nil)
	port, stop := hiddenStartTCP(t, "127.0.0.1", leaf)
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{ServerName: "fromMitm", PinnedPeerCertSha256: [][]byte{hiddenLeafHash(leaf)}},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	conn, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.LocalHostIP, port), settings)
	if err != nil {
		t.Fatalf("dial failed: %v", err)
	}
	defer conn.Close()
	if err := hiddenTCPRoundTrip(conn); err != nil {
		t.Fatalf("a pinned leaf certificate was rejected: %v", err)
	}
}

// A connection that recovers its server name from its context must keep validating against it.
func TestFunc_TCPPinnedCAFromContextName(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartTCP(t, "127.0.0.1", ca.makeLeaf(t, []string{"mitm.example"}, nil))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{ServerName: "fromMitm", PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	ctx = session.ContextWithMitmServerName(ctx, "mitm.example")
	conn, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.LocalHostIP, port), settings)
	if err != nil {
		t.Fatalf("dial failed: %v", err)
	}
	defer conn.Close()
	if err := hiddenTCPRoundTrip(conn); err != nil {
		t.Fatalf("round trip failed: %v", err)
	}
}

// Repeated connections with the same settings keep working, and each is validated against its own
// destination.
func TestFunc_TCPPinnedCARepeatedDial(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartTCP(t, "127.0.0.1", ca.makeLeaf(t, nil, []stdnet.IP{stdnet.ParseIP("127.0.0.1")}))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	for i := 0; i < 2; i++ {
		conn, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.LocalHostIP, port), settings)
		if err != nil {
			t.Fatalf("dial %d failed: %v", i, err)
		}
		if err := hiddenTCPRoundTrip(conn); err != nil {
			_ = conn.Close()
			t.Fatalf("round trip %d failed: %v", i, err)
		}
		_ = conn.Close()
	}
}

// The explicit list of names a certificate may be valid for keeps working with a pinned CA.
func TestFunc_TCPPinnedCANamedCert(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartTCP(t, "127.0.0.1", ca.makeLeaf(t, []string{"named.example"}, nil))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "tcp",
		ProtocolSettings: &tcp.Config{},
		SecuritySettings: &xtls.Config{
			VerifyPeerCertByName: []string{"named.example"},
			PinnedPeerCertSha256: [][]byte{ca.hash()},
		},
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	conn, err := hiddenDialTCP(ctx, xnet.TCPDestination(xnet.LocalHostIP, port), settings)
	if err != nil {
		t.Fatalf("dial failed: %v", err)
	}
	defer conn.Close()
	if err := hiddenTCPRoundTrip(conn); err != nil {
		t.Fatalf("round trip failed: %v", err)
	}
}
