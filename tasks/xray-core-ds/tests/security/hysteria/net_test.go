package hysteria_test

import (
	"context"
	"crypto/tls"
	stdnet "net"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/hysteria"
	"github.com/xtls/xray-core/transport/internet/stat"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

const hiddenHysteriaAuth = "hidden-test-auth"

func hiddenHysteriaServerSettings(t *testing.T, cert tls.Certificate) *internet.MemoryStreamConfig {
	t.Helper()
	certPEM, keyPEM := hiddenCertPEM(t, cert)
	return &internet.MemoryStreamConfig{
		ProtocolName:     "hysteria",
		ProtocolSettings: &hysteria.Config{Auth: hiddenHysteriaAuth},
		SecuritySettings: &xtls.Config{Certificate: []*xtls.Certificate{{Certificate: certPEM, Key: keyPEM}}},
	}
}

func hiddenStartHysteria(t *testing.T, cert tls.Certificate) (xnet.Port, func()) {
	t.Helper()
	port := xnet.Port(hiddenFreeUDPPort(t))
	ctx, cancel := context.WithCancel(context.Background())
	l, err := hysteria.Listen(ctx, xnet.LocalHostIP, port, hiddenHysteriaServerSettings(t, cert), func(c stat.Connection) {
		go func() {
			b := make([]byte, 1024)
			n, err := c.Read(b)
			if err == nil {
				time.Sleep(100 * time.Millisecond)
				_, _ = c.Write(append([]byte("reply:"), b[:n]...))
				time.Sleep(500 * time.Millisecond)
			}
			_ = c.Close()
		}()
	})
	if err != nil {
		cancel()
		t.Fatalf("listen: %v", err)
	}
	return port, func() { _ = l.Close(); cancel() }
}

func hiddenHysteriaClientSettings(caHash []byte) *internet.MemoryStreamConfig {
	return &internet.MemoryStreamConfig{
		ProtocolName:     "hysteria",
		ProtocolSettings: &hysteria.Config{Auth: hiddenHysteriaAuth},
		SecuritySettings: &xtls.Config{PinnedPeerCertSha256: [][]byte{caHash}},
	}
}

func hiddenDialHysteria(t *testing.T, dest xnet.Destination, settings *internet.MemoryStreamConfig, timeout time.Duration) (stat.Connection, error) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	t.Cleanup(cancel)
	return hysteria.Dial(ctx, dest, settings)
}

func hiddenFreeUDPPort(t *testing.T) int {
	t.Helper()
	c, err := stdnet.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	p := c.LocalAddr().(*stdnet.UDPAddr).Port
	_ = c.Close()
	return p
}
