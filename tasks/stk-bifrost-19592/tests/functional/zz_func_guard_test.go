package utils_test

import (
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
	"syscall"
	"testing"
	"time"

	providerUtils "github.com/maximhq/bifrost/core/providers/utils"
	"github.com/valyala/fasthttp"
)

func hiddenFuncGuardReachedNetwork(err error) bool {
	if err == nil {
		return false
	}
	for _, target := range []error{
		io.EOF, io.ErrUnexpectedEOF,
		syscall.ENETUNREACH, syscall.EHOSTUNREACH, syscall.ECONNREFUSED,
		syscall.ECONNRESET, syscall.EPIPE, syscall.EACCES,
	} {
		if errors.Is(err, target) {
			return true
		}
	}
	var opErr *net.OpError
	if errors.As(err, &opErr) && opErr.Timeout() {
		return true
	}
	if os.IsTimeout(err) {
		return true
	}
	msg := strings.ToLower(err.Error())
	for _, marker := range []string{
		"network is unreachable", "no route to host", "connection refused",
		"connection reset", "broken pipe", "i/o timeout", "timed out", "empty reply",
		"non-2xx status", "eof",
	} {
		if strings.Contains(msg, marker) {
			return true
		}
	}
	return false
}

func hiddenLocalIPv4(t *testing.T) string {
	t.Helper()
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		t.Fatalf("cannot list local addresses: %v", err)
	}
	for _, addr := range addrs {
		ipNet, ok := addr.(*net.IPNet)
		if !ok || ipNet.IP.IsLoopback() {
			continue
		}
		if v4 := ipNet.IP.To4(); v4 != nil {
			return v4.String()
		}
	}
	t.Fatal("the environment has no non-loopback IPv4 address to test with")
	return ""
}

func hiddenDialAndClose(client *fasthttp.Client, addr string) error {
	conn, err := client.Dial(addr)
	if err != nil {
		return err
	}
	_ = conn.Close()
	return nil
}

// Loopback endpoints keep working: providers such as Ollama/vLLM/SGL are local.
func TestFunc_GuardAllowsLoopback(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("cannot start a local listener: %v", err)
	}
	defer ln.Close()
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			_ = c.Close()
		}
	}()

	client := &fasthttp.Client{ReadTimeout: 3 * time.Second}
	providerUtils.ConfigureDialer(client, false)
	if err := hiddenDialAndClose(client, ln.Addr().String()); err != nil {
		t.Fatalf("a loopback provider endpoint must keep working, got %v", err)
	}
}

// An operator-opted-in private endpoint keeps working.
func TestFunc_GuardAllowsPrivateWhenOptedIn(t *testing.T) {
	ip := hiddenLocalIPv4(t)
	ln, err := net.Listen("tcp", net.JoinHostPort(ip, "0"))
	if err != nil {
		t.Fatalf("cannot listen on the private address: %v", err)
	}
	defer ln.Close()
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			_ = c.Close()
		}
	}()

	client := &fasthttp.Client{ReadTimeout: 3 * time.Second}
	providerUtils.ConfigureDialer(client, true)
	if err := hiddenDialAndClose(client, ln.Addr().String()); err != nil {
		t.Fatalf("an opted-in private endpoint must keep working, got %v", err)
	}
}

// Without the opt-in, the same private endpoint is still refused before dialing.
func TestFunc_GuardRefusesPrivateByDefault(t *testing.T) {
	ip := hiddenLocalIPv4(t)
	client := &fasthttp.Client{ReadTimeout: 3 * time.Second}
	providerUtils.ConfigureDialer(client, false)
	conn, err := client.Dial(net.JoinHostPort(ip, "51999"))
	if conn != nil {
		_ = conn.Close()
	}
	if err == nil {
		t.Fatal("a private endpoint must be refused without the opt-in")
	}
	if hiddenFuncGuardReachedNetwork(err) {
		t.Fatalf("the private endpoint was not refused before connecting: %v", err)
	}
}

// A public IPv4 carried inside a 6to4 address is still a public destination.
func TestFunc_GuardAllowsSixToFourPublic(t *testing.T) {
	client := &fasthttp.Client{ReadTimeout: 3 * time.Second}
	providerUtils.ConfigureDialer(client, false)
	conn, err := client.Dial("[2002:0808:0808::]:51999")
	if conn != nil {
		_ = conn.Close()
		return
	}
	if err == nil {
		return
	}
	if !hiddenFuncGuardReachedNetwork(err) {
		t.Fatalf("a public 6to4 destination was refused instead of dialed: %v", err)
	}
}

// A proxy/custom dial owns routing and is kept as-is.
func TestFunc_GuardKeepsExistingDial(t *testing.T) {
	sentinel := fmt.Errorf("proxy-routed")
	client := &fasthttp.Client{}
	client.Dial = func(addr string) (net.Conn, error) { return nil, sentinel }
	providerUtils.ConfigureDialer(client, false)
	_, err := client.Dial("10.0.0.1:80")
	if !errors.Is(err, sentinel) {
		t.Fatalf("an existing dial must still own routing, got %v", err)
	}
}
