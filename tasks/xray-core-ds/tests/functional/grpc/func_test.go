package grpc_test

import (
	stdnet "net"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/grpc"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

// Pinning a CA and dialing an IP address must keep working when the server certificate is valid
// for that address; the dialed address is the host the client knows it is connecting to.
func TestFunc_GRPCPinnedCAValidHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartGRPC(t, ca.makeLeaf(t, nil, []stdnet.IP{stdnet.ParseIP("127.0.0.1")}))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "grpc",
		ProtocolSettings: &grpc.Config{},
		SecuritySettings: &xtls.Config{PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	conn, err := hiddenDialGRPC(t, xnet.TCPDestination(xnet.LocalHostIP, port), settings, 8*time.Second)
	if err != nil {
		t.Fatalf("a certificate valid for the dialed address was rejected: %v", err)
	}
	defer conn.Close()
	if err := hiddenRoundTrip(conn); err != nil {
		t.Fatalf("round trip failed: %v", err)
	}
}

// Pinning the server's own (leaf) certificate is a direct identity check and must keep working
// without any server name.
func TestFunc_GRPCPinnedLeafNoName(t *testing.T) {
	ca := newHiddenCA(t)
	leaf := ca.makeLeaf(t, []string{"leaf-only.example"}, nil)
	port, stop := hiddenStartGRPC(t, leaf)
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "grpc",
		ProtocolSettings: &grpc.Config{},
		SecuritySettings: &xtls.Config{PinnedPeerCertSha256: [][]byte{hiddenLeafHash(leaf)}},
	}
	conn, err := hiddenDialGRPC(t, xnet.TCPDestination(xnet.LocalHostIP, port), settings, 8*time.Second)
	if err != nil {
		t.Fatalf("a pinned leaf certificate was rejected: %v", err)
	}
	defer conn.Close()
	if err := hiddenRoundTrip(conn); err != nil {
		t.Fatalf("round trip failed: %v", err)
	}
}
