// Package security holds the exploit tests. Each drives the running
// `rclone serve s3` auth-proxy server over HTTP as an S3 client would and
// asserts the attack is BLOCKED (HTTP 403).
//
// The attack: the auth proxy authenticates access key IDs, but the client
// never transmits its secret, only a signature made with it. Each test signs
// a request for a VALID (proxy-known) access key ID with an EMPTY secret -
// something an attacker can always compute without knowing the real secret.
// On vulnerable code the server verifies the signature against an empty secret
// and accepts it, so the attacker acts as that user (data is listed, read,
// written and deleted). A correct fix verifies the signature against the
// secret the proxy supplies for the access key ID, so every one of these is
// refused.
package security

import (
	"net/http"
	"os"
	"strings"
	"testing"

	"rclones3harness/s3test"
)

var proxy *s3test.Server

func TestMain(m *testing.M) {
	s3test.PortBase = 38100
	if err := s3test.SetupData(); err != nil {
		panic(err)
	}
	code := m.Run()
	if proxy != nil {
		proxy.Stop()
	}
	os.Exit(code)
}

func server(t *testing.T) *s3test.Server {
	if proxy == nil {
		proxy = s3test.StartProxyServer(t)
	}
	return proxy
}

// blocked asserts the request was refused with 403 Forbidden and that no
// bucket listing or object content leaked in the body.
func blocked(t *testing.T, code int, body, leak string) {
	t.Helper()
	if code != http.StatusForbidden {
		t.Fatalf("attack was NOT blocked: got HTTP %d, body=%q", code, body)
	}
	if leak != "" && strings.Contains(body, leak) {
		t.Fatalf("attack leaked data %q in body: %q", leak, body)
	}
}

// 1. List the account's buckets as alice, signed with an empty secret.
func TestListBucketsAliceEmptySecret(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.AliceKey, "", nil)
	blocked(t, code, body, "ListAllMyBucketsResult")
}

// 2. Read one of alice's objects, signed with an empty secret (data theft).
func TestGetObjectAliceEmptySecret(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "GET", "/alicebucket/readable.txt", s3test.AliceKey, "", nil)
	blocked(t, code, body, "ALICE CONFIDENTIAL FILE")
}

// 3. Write a new object into alice's bucket, signed with an empty secret.
func TestPutObjectAliceEmptySecret(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "PUT", "/alicebucket/injected.txt", s3test.AliceKey, "", []byte("owned"))
	blocked(t, code, body, "")
}

// 4. Delete one of alice's objects, signed with an empty secret.
func TestDeleteObjectAliceEmptySecret(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "DELETE", "/alicebucket/deletable.txt", s3test.AliceKey, "", nil)
	blocked(t, code, body, "")
}

// 5. Act as a DIFFERENT proxy-mapped user (bob) with an empty secret, proving
//    the flaw is not tied to one access key ID or backend.
func TestListBucketsBobEmptySecret(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.BobKey, "", nil)
	blocked(t, code, body, "ListAllMyBucketsResult")
}
