package grpc_test

import (
	"context"
	"crypto/tls"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/grpc"
	"github.com/xtls/xray-core/transport/internet/stat"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

func hiddenGRPCSettings(t *testing.T, cert tls.Certificate) *internet.MemoryStreamConfig {
	t.Helper()
	certPEM, keyPEM := hiddenCertPEM(t, cert)
	return &internet.MemoryStreamConfig{
		ProtocolName:     "grpc",
		ProtocolSettings: &grpc.Config{},
		SecuritySettings: &xtls.Config{Certificate: []*xtls.Certificate{{Certificate: certPEM, Key: keyPEM}}},
	}
}

func hiddenStartGRPC(t *testing.T, cert tls.Certificate) (xnet.Port, func()) {
	t.Helper()
	port := xnet.Port(hiddenFreePort(t))
	ctx, cancel := context.WithCancel(context.Background())
	l, err := grpc.Listen(ctx, xnet.LocalHostIP, port, hiddenGRPCSettings(t, cert), func(c stat.Connection) {
		go func() {
			defer c.Close()
			b := make([]byte, 1024)
			n, err := c.Read(b)
			if err != nil {
				return
			}
			time.Sleep(100 * time.Millisecond)
			_, _ = c.Write(append([]byte("reply:"), b[:n]...))
			time.Sleep(200 * time.Millisecond)
		}()
	})
	if err != nil {
		cancel()
		t.Fatalf("listen: %v", err)
	}
	return port, func() { _ = l.Close(); cancel() }
}

func hiddenDialGRPC(t *testing.T, dest xnet.Destination, settings *internet.MemoryStreamConfig, timeout time.Duration) (stat.Connection, error) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	t.Cleanup(cancel)
	return grpc.Dial(ctx, dest, settings)
}

func hiddenRoundTrip(c stat.Connection) error {
	if _, err := c.Write([]byte("ping")); err != nil {
		return err
	}
	_ = c.SetReadDeadline(time.Now().Add(4 * time.Second))
	b := make([]byte, 64)
	_, err := c.Read(b)
	return err
}
