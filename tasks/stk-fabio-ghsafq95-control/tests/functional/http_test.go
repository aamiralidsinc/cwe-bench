package functional

import (
	"bytes"
	"io"
	"net"
	"strings"
	"testing"
	"time"

	htests "github.com/fabiolb/fabio/htests_support"
)

// A client-supplied X-Real-Ip is kept today for chained proxy deployments
// when the operator has not designated that header.
func TestFunc_PreservesClientRealIPWhenNotDesignated(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close",
		"X-Real-Ip: 6.6.6.6"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Real-Ip"); got != "6.6.6.6" {
		t.Errorf("backend saw X-Real-Ip %q, want the preserved client value %q", got, "6.6.6.6")
	}
}

// A client-supplied forwarding host is kept today for chained proxies.
func TestFunc_PreservesClientForwardedHost(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close",
		"X-Forwarded-Host: 9.10.11.12"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Forwarded-Host"); got != "9.10.11.12" {
		t.Errorf("backend saw X-Forwarded-Host %q, want the preserved client value %q", got, "9.10.11.12")
	}
}

// The documented forwarding chain keeps appending the observed address.
func TestFunc_AppendsForwardedForChain(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close",
		"X-Forwarded-For: 3.3.3.3"))

	h := htests.RecvHeader(t, headers)
	if got, want := h.Get("X-Forwarded-For"), "3.3.3.3, 127.0.0.1"; got != want {
		t.Errorf("backend saw X-Forwarded-For %q, want %q", got, want)
	}
}

// A hop-by-hop declaration that names an ordinary header keeps stripping it.
func TestFunc_OrdinaryHopByHopHeaderStillStripped(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close, X-Legit",
		"X-Legit: keep-me"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Legit"); got != "" {
		t.Errorf("backend saw X-Legit %q, want it stripped as an ordinary hop-by-hop header", got)
	}
}

// The operator-configured client-address header is set on an ordinary request.
func TestFunc_ConfiguredClientIPHeaderIsSet(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL),
		"-proxy.header.clientip", "X-Client-IP")

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Client-IP"); !htests.IsLoopbackValue(got) {
		t.Errorf("backend saw X-Client-IP %q, want the value derived from the client address", got)
	}
}

// The operator-configured request id is set on an ordinary request.
func TestFunc_RequestIDHeaderIsSet(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL),
		"-proxy.header.requestid", "X-Request-ID")

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Request-ID"); got == "" {
		t.Errorf("backend saw no X-Request-ID, want a value the proxy generated")
	}
}

// wsBackend accepts a websocket handshake only when the forwarded request
// still carries a Connection token that negotiates the upgrade.
func wsBackend(t *testing.T) (string, <-chan string) {
	t.Helper()
	lis, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	t.Cleanup(func() { lis.Close() })
	seen := make(chan string, 8)
	go func() {
		for {
			c, err := lis.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				_ = c.SetReadDeadline(time.Now().Add(10 * time.Second))
				var buf []byte
				tmp := make([]byte, 1024)
				for {
					n, err := c.Read(tmp)
					buf = append(buf, tmp[:n]...)
					if err != nil || bytes.Contains(buf, []byte("\r\n\r\n")) {
						break
					}
				}
				select {
				case seen <- string(buf):
				default:
				}
				if strings.Contains(strings.ToLower(string(buf)), "connection: upgrade") {
					_, _ = io.WriteString(c, "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n")
				} else {
					_, _ = io.WriteString(c, "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
				}
				time.Sleep(200 * time.Millisecond)
			}(c)
		}
	}()
	return lis.Addr().String(), seen
}

// A websocket handshake keeps working when the request also names a header
// the proxy derives.
func TestFunc_WebsocketUpgrade(t *testing.T) {
	backend, _ := wsBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute("http://"+backend))

	resp := htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/ws", "example.com",
		"Upgrade: websocket",
		"Connection: Upgrade, X-Forwarded-Host",
		"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
		"Sec-WebSocket-Version: 13"))
	if !strings.Contains(resp, "101") {
		t.Errorf("websocket handshake failed: %q", resp)
	}
}

// A legitimate handshake keeps working when its hop-by-hop tokens are spread
// over more than one declaration line.
func TestFunc_WebsocketDeclarationAcrossLines(t *testing.T) {
	backend, _ := wsBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute("http://"+backend))

	resp := htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/ws", "example.com",
		"Upgrade: websocket",
		"Connection: X-Forwarded-Host",
		"Connection: Upgrade",
		"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
		"Sec-WebSocket-Version: 13"))
	if !strings.Contains(resp, "101") {
		t.Errorf("websocket handshake failed: %q", resp)
	}
}

// The documented forwarding chain keeps appending when the operator designates
// the chain header as the client-address header.
func TestFunc_AppendsForwardedForChainWhenConfigured(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL),
		"-proxy.header.clientip", "X-Forwarded-For")

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close",
		"X-Forwarded-For: 3.3.3.3"))

	h := htests.RecvHeader(t, headers)
	if got, want := h.Get("X-Forwarded-For"), "3.3.3.3, 127.0.0.1"; got != want {
		t.Errorf("backend saw X-Forwarded-For %q, want %q", got, want)
	}
}
