// Package htests contains the shared harness for the hidden behavioural suites.
// Every test drives a real fabio process over its network listeners so that any
// valid placement of the fix (configuration wiring, request handling or the
// proxy transport) is exercised in the same way an operator would exercise it.
package htests

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/protobuf/types/known/emptypb"
)

const fabioBin = "/workspace/.htests/bin/fabio"

func binary() string {
	if v := os.Getenv("FABIO_BIN"); v != "" {
		return v
	}
	return fabioBin
}

// FreeAddr returns a loopback address with a free TCP port.
func FreeAddr(t *testing.T) string {
	t.Helper()
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("reserve port: %v", err)
	}
	defer l.Close()
	return l.Addr().String()
}

type logBuffer struct {
	mu sync.Mutex
	b  bytes.Buffer
}

func (l *logBuffer) Write(p []byte) (int, error) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.b.Len() < 128*1024 {
		return l.b.Write(p)
	}
	return len(p), nil
}

func (l *logBuffer) String() string {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.b.String()
}

// Fabio is a running fabio process.
type Fabio struct {
	addr string
	cmd  *exec.Cmd
	log  *logBuffer
}

// StartFabio starts the product binary with a static routing table and the
// given extra command-line options. listen is the full -proxy.addr value.
func StartFabio(t *testing.T, listen string, extra ...string) *Fabio {
	t.Helper()
	dial := strings.Split(listen, ";")[0]
	args := []string{
		"-proxy.addr", listen,
		"-ui.addr", FreeAddr(t),
		"-registry.backend", "static",
		"-log.level", "ERROR",
	}
	args = append(args, extra...)

	cmd := exec.Command(binary(), args...)
	log := &logBuffer{}
	cmd.Stdout = log
	cmd.Stderr = log
	if err := cmd.Start(); err != nil {
		t.Fatalf("start fabio: %v", err)
	}
	f := &Fabio{addr: dial, cmd: cmd, log: log}
	t.Cleanup(f.Stop)

	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		c, err := net.DialTimeout("tcp", dial, 200*time.Millisecond)
		if err == nil {
			c.Close()
			return f
		}
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatalf("fabio did not listen on %s; log:\n%s", dial, log.String())
	return nil
}

// Stop terminates the process.
func (f *Fabio) Stop() {
	if f.cmd.Process != nil {
		_ = f.cmd.Process.Signal(syscall.SIGKILL)
		_, _ = f.cmd.Process.Wait()
	}
}

// Addr is the loopback address the proxy listener is bound to.
func (f *Fabio) Addr() string { return f.addr }

// Log returns the process output collected so far.
func (f *Fabio) Log() string { return f.log.String() }

// HTTPBackend starts a backend that records the headers of each request.
func HTTPBackend(t *testing.T) (*httptest.Server, <-chan http.Header) {
	t.Helper()
	headers := make(chan http.Header, 16)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case headers <- r.Header.Clone():
		default:
		}
		w.WriteHeader(http.StatusOK)
		_, _ = io.WriteString(w, "ok")
	}))
	t.Cleanup(srv.Close)
	return srv, headers
}

// GRPCBackend starts a transparent gRPC backend that records the metadata of
// each call and answers it.
func GRPCBackend(t *testing.T) (string, <-chan metadata.MD) {
	t.Helper()
	calls := make(chan metadata.MD, 16)
	srv := grpc.NewServer(grpc.UnknownServiceHandler(func(_ any, stream grpc.ServerStream) error {
		md, _ := metadata.FromIncomingContext(stream.Context())
		select {
		case calls <- md.Copy():
		default:
		}
		var msg emptypb.Empty
		if err := stream.RecvMsg(&msg); err != nil {
			return err
		}
		return stream.SendMsg(&msg)
	}))
	lis, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	go func() { _ = srv.Serve(lis) }()
	t.Cleanup(srv.Stop)
	return lis.Addr().String(), calls
}

// GRPCCall invokes a method through the given address with the given metadata
// and returns the call error. The backend records the metadata it receives.
func GRPCCall(addr string, kv ...string) error {
	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return err
	}
	defer conn.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs(kv...))
	var out emptypb.Empty
	return conn.Invoke(ctx, "/htest.Echo/Call", &emptypb.Empty{}, &out)
}

// BuildRequest renders a raw HTTP/1.1 request with full control over the
// header lines, so that repeated headers stay repeated on the wire.
func BuildRequest(method, path, host string, headerLines ...string) string {
	var b strings.Builder
	fmt.Fprintf(&b, "%s %s HTTP/1.1\r\nHost: %s\r\n", method, path, host)
	for _, h := range headerLines {
		b.WriteString(h)
		b.WriteString("\r\n")
	}
	b.WriteString("\r\n")
	return b.String()
}

// RawRequest sends the request to addr and returns everything read back.
func RawRequest(t *testing.T, addr, request string) string {
	t.Helper()
	c, err := net.DialTimeout("tcp", addr, 5*time.Second)
	if err != nil {
		t.Fatalf("dial proxy: %v", err)
	}
	defer c.Close()
	_ = c.SetDeadline(time.Now().Add(10 * time.Second))
	if _, err := io.WriteString(c, request); err != nil {
		t.Fatalf("write request: %v", err)
	}
	b, _ := io.ReadAll(c)
	return string(b)
}

// RecvHeader returns the next recorded backend request header set.
func RecvHeader(t *testing.T, ch <-chan http.Header) http.Header {
	t.Helper()
	select {
	case h := <-ch:
		return h
	case <-time.After(10 * time.Second):
		t.Fatal("backend received no request")
		return nil
	}
}

// RecvMetadata returns the next recorded backend gRPC metadata set.
func RecvMetadata(t *testing.T, ch <-chan metadata.MD) metadata.MD {
	t.Helper()
	select {
	case md := <-ch:
		return md
	case <-time.After(10 * time.Second):
		t.Fatal("backend received no gRPC call")
		return nil
	}
}

// HTTPRoute renders a static route command for the given target.
func HTTPRoute(target string) string {
	return "route add web example.com/ " + target
}

// GRPCRoute renders a static gRPC route command for the given target.
func GRPCRoute(target string) string {
	return "route add grpc / grpc://" + target + ` opts "proto=grpc"`
}

// IsLoopbackValue reports whether v names the loopback client address. A fix
// may use either the bare host or host:port form.
func IsLoopbackValue(v string) bool {
	return v == "127.0.0.1" || v == "::1" || strings.HasPrefix(v, "127.0.0.1:") || strings.HasPrefix(v, "[::1]:")
}
