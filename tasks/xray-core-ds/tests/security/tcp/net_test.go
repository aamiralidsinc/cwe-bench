package tcp_test

import (
	"context"
	"crypto/tls"
	stdnet "net"
	"testing"
	"time"

	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/transport/internet"
	"github.com/xtls/xray-core/transport/internet/stat"
	"github.com/xtls/xray-core/transport/internet/tcp"
)

func hiddenStartTCP(t *testing.T, ip string, cert tls.Certificate) (xnet.Port, func()) {
	t.Helper()
	l, err := stdnet.Listen("tcp", ip+":0")
	if err != nil {
		t.Fatal(err)
	}
	port := l.Addr().(*stdnet.TCPAddr).Port
	ln := tls.NewListener(l, &tls.Config{Certificates: []tls.Certificate{cert}})
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
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
		}
	}()
	return xnet.Port(port), func() { _ = ln.Close() }
}

func hiddenDialTCP(ctx context.Context, dest xnet.Destination, settings *internet.MemoryStreamConfig) (stat.Connection, error) {
	return tcp.Dial(ctx, dest, settings)
}

func hiddenTCPRoundTrip(c stat.Connection) error {
	if _, err := c.Write([]byte("ping")); err != nil {
		return err
	}
	_ = c.SetReadDeadline(time.Now().Add(4 * time.Second))
	b := make([]byte, 64)
	_, err := c.Read(b)
	return err
}
