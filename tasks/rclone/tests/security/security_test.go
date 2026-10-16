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
	"crypto/md5"
	"encoding/hex"
	"errors"
	"io/fs"
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
	// alice's own object for the correct-secret DELETE test; seeded before the server starts.
	_ = os.Remove(aliceUploadPath)
	if err := os.WriteFile(aliceOwnDeletePath, []byte("ALICE OWN DELETE\n"), 0o644); err != nil {
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

// blocked asserts the request was refused (any 4xx) and that no bucket listing
// or object content leaked in the body.
func blocked(t *testing.T, code int, body, leak string) {
	t.Helper()
	if code < 400 || code >= 500 {
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

// Auth-proxy mode must SERVE a client signing with the correct per-user secret the proxy
// returns: the instruction requires the signature to verify against the identity's real
// secret. The vulnerable code checks it against an empty secret, so correct users fail too;
// a fix that refuses every proxy request must fail here (added 2026-10-16, run ypUhTQw).
func TestS3ProxyAliceCorrectSecretServed(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.AliceKey, s3test.AliceSecret, nil)
	if code != http.StatusOK || !strings.Contains(body, "alicebucket") {
		t.Fatalf("alice with her correct secret was not served her bucket listing via the auth proxy: HTTP %d, body=%q", code, body)
	}
	code, body = s3test.Do(s.Base, "GET", "/alicebucket/readable.txt", s3test.AliceKey, s3test.AliceSecret, nil)
	if code != http.StatusOK || !strings.Contains(body, "ALICE CONFIDENTIAL FILE") {
		t.Fatalf("alice with her correct secret could not read her own object via the auth proxy: HTTP %d, body=%q", code, body)
	}
}

func TestS3ProxyBobCorrectSecretServed(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.BobKey, s3test.BobSecret, nil)
	if code != http.StatusOK || !strings.Contains(body, "bobbucket") {
		t.Fatalf("bob with his correct secret was not served his bucket listing via the auth proxy: HTTP %d, body=%q", code, body)
	}
}

// The proxy knows carol but returns no secret for her: every request must be refused,
// whatever the client signs with: an empty secret, the access key ID itself, or its MD5.
// (2026-10-16: a fix that fell back to the access key ID as the secret passed before.)
func TestS3ProxyNoSecretRefused(t *testing.T) {
	s := server(t)
	const carol = "AKIACAROL00000003"
	sum := md5.Sum([]byte(carol))
	for _, secret := range []string{"", carol, hex.EncodeToString(sum[:])} {
		code, body := s3test.Do(s.Base, "GET", "/alicebucket/readable.txt", carol, secret, nil)
		if code < 400 || code >= 500 || strings.Contains(body, "ALICE CONFIDENTIAL FILE") {
			t.Fatalf("identity with no secret was served (signed with %q): HTTP %d, body=%q", secret, code, body)
		}
	}
}

// Correct-secret WRITES must be served too (2026-10-16): the instruction says a client that
// signs with the correct secret must be served for all S3 operations, so a fix that verifies
// reads but refuses PUT/DELETE in auth-proxy mode is not acceptable. The side effect is
// checked on alice's backend directory, not just the status.
const (
	aliceUploadPath    = "/data/alice/alicebucket/alice-upload.txt"
	aliceOwnDeletePath = "/data/alice/alicebucket/alice-own-delete.txt"
)

func TestS3ProxyAliceCorrectSecretPutServed(t *testing.T) {
	s := server(t)
	const content = "ALICE UPLOAD VIA PROXY\n"
	code, body := s3test.Do(s.Base, "PUT", "/alicebucket/alice-upload.txt", s3test.AliceKey, s3test.AliceSecret, []byte(content))
	if code < 200 || code >= 300 {
		t.Fatalf("alice with her correct secret could not PUT into her own bucket via the auth proxy: HTTP %d, body=%q", code, body)
	}
	got, err := os.ReadFile(aliceUploadPath)
	if err != nil || string(got) != content {
		t.Fatalf("PUT answered HTTP %d but the object was not written to alice's backend: err=%v, content=%q", code, err, got)
	}
	code, body = s3test.Do(s.Base, "GET", "/alicebucket/alice-upload.txt", s3test.AliceKey, s3test.AliceSecret, nil)
	if code != http.StatusOK || body != content {
		t.Fatalf("alice could not read back the object she uploaded: HTTP %d, body=%q", code, body)
	}
}

func TestS3ProxyAliceCorrectSecretDeleteServed(t *testing.T) {
	s := server(t)
	code, body := s3test.Do(s.Base, "DELETE", "/alicebucket/alice-own-delete.txt", s3test.AliceKey, s3test.AliceSecret, nil)
	if code < 200 || code >= 300 {
		t.Fatalf("alice with her correct secret could not DELETE her own object via the auth proxy: HTTP %d, body=%q", code, body)
	}
	if _, err := os.Stat(aliceOwnDeletePath); !errors.Is(err, fs.ErrNotExist) {
		t.Fatalf("DELETE answered HTTP %d but the object is still on alice's backend (stat err=%v)", code, err)
	}
}
