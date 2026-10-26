package dns_test

import (
	"context"
	"crypto/tls"
	"encoding/hex"
	"fmt"
	"io"
	stdnet "net"
	"net/http"
	"testing"
	"time"

	. "github.com/xtls/xray-core/app/dns"
	xnet "github.com/xtls/xray-core/common/net"
	dns_feature "github.com/xtls/xray-core/features/dns"
	"golang.org/x/net/dns/dnsmessage"
)

func hiddenStartDoH(t *testing.T, cert tls.Certificate) int {
	t.Helper()
	h := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		var p dnsmessage.Parser
		hd, err := p.Start(body)
		if err != nil {
			http.Error(w, "bad query", http.StatusBadRequest)
			return
		}
		q, err := p.Question()
		if err != nil {
			http.Error(w, "bad query", http.StatusBadRequest)
			return
		}
		b := dnsmessage.NewBuilder(nil, dnsmessage.Header{ID: hd.ID, Response: true, RCode: dnsmessage.RCodeSuccess})
		b.EnableCompression()
		_ = b.StartQuestions()
		_ = b.Question(q)
		_ = b.StartAnswers()
		_ = b.AResource(dnsmessage.ResourceHeader{Name: q.Name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET, TTL: 60}, dnsmessage.AResource{A: [4]byte{1, 2, 3, 4}})
		msg, err := b.Finish()
		if err != nil {
			http.Error(w, "bad answer", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/dns-message")
		_, _ = w.Write(msg)
	})
	srv := &http.Server{Handler: h, TLSConfig: &tls.Config{Certificates: []tls.Certificate{cert}, NextProtos: []string{"h2"}}}
	l, err := stdnet.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	port := l.Addr().(*stdnet.TCPAddr).Port
	go func() { _ = srv.ServeTLS(l, "", "") }()
	t.Cleanup(func() { _ = srv.Close() })
	return port
}

func hiddenDoHAddress(port int, caHash []byte) string {
	return fmt.Sprintf("https+local://127.0.0.1:%d/dns-query?pinnedPeerCertSha256=%s", port, hex.EncodeToString(caHash))
}

func hiddenDoHQuery(address string) ([]xnet.IP, error) {
	srv, err := NewServer(context.Background(), xnet.Destination{Address: xnet.DomainAddress(address)}, nil, true, false, 0, nil)
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	ips, _, err := srv.QueryIP(ctx, "example.com", dns_feature.IPOption{IPv4Enable: true})
	return ips, err
}
