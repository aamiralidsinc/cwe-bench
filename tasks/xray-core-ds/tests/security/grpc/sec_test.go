package grpc_test

import (
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/grpc"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

// A client that pins a CA must refuse a server certificate issued by that CA for a host other
// than the one it dials, including when the dial target is an IP address and no server name is
// configured.
func TestSec_GRPCPinnedCAWrongHost(t *testing.T) {
	ca := newHiddenCA(t)
	port, stop := hiddenStartGRPC(t, ca.makeLeaf(t, []string{"unrelated.example"}, nil))
	defer stop()

	settings := &internet.MemoryStreamConfig{
		ProtocolName:     "grpc",
		ProtocolSettings: &grpc.Config{},
		SecuritySettings: &xtls.Config{PinnedPeerCertSha256: [][]byte{ca.hash()}},
	}
	conn, err := hiddenDialGRPC(t, xnet.TCPDestination(xnet.LocalHostIP, port), settings, 20*time.Second)
	if err == nil {
		defer conn.Close()
		_ = hiddenRoundTrip(conn)
		t.Fatalf("a certificate issued by the pinned CA for unrelated.example was accepted")
	}
}
