package realm_test

import (
	"context"
	"crypto/tls"
	"encoding/json"
	stdnet "net"
	"net/http"
	"strconv"
	"testing"
	"time"

	"github.com/xtls/xray-core/transport/internet/finalmask/realm"
	xtls "github.com/xtls/xray-core/transport/internet/tls"
)

func hiddenStartRealmServer(t *testing.T, cert tls.Certificate) (int, func()) {
	t.Helper()
	l, err := stdnet.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := l.Addr().(*stdnet.TCPAddr).Port
	srv := &http.Server{
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(map[string]any{"session_id": "hidden-session", "ttl": 30})
		}),
		TLSConfig: &tls.Config{Certificates: []tls.Certificate{cert}},
	}
	go func() { _ = srv.ServeTLS(l, "", "") }()
	return port, func() { _ = srv.Close() }
}

func hiddenRealmClient(port int, caHash []byte) *realm.Client {
	return realm.NewClient("https", "127.0.0.1", strconv.Itoa(port), "hidden-token", &xtls.Config{
		PinnedPeerCertSha256: [][]byte{caHash},
	})
}

func hiddenRegister(c *realm.Client) error {
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	_, err := c.Register(ctx, "hidden-realm", []string{"1.2.3.4:1000"})
	return err
}
