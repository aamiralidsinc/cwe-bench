// Package security holds the exploit tests. Each drives a running `rclone
// serve ...` process over its real network protocol as a client would and
// asserts the attack is BLOCKED.
//
// The shared flaw: several serve surfaces authenticate a client by its
// identity (S3 access key ID, or a username) but fail to actually verify the
// secret the client presents. An attacker who knows a valid identity can then
// authenticate with an empty or wrong secret. Each test presents a VALID
// identity with a bad secret; on vulnerable code the server lets it in, on a
// correct fix every one is refused.
package security

import (
	"crypto/md5"
	"encoding/hex"
	"net/http"
	"os"
	"strings"
	"testing"

	"rclones3harness/s3test"
)

var (
	s3proxy  *s3test.Server
	httpB    *s3test.Server
	httpH    *s3test.Server
	ftpS     *s3test.Server
	sftpS    *s3test.Server
)

func TestMain(m *testing.M) {
	s3test.PortBase = 38100
	if err := s3test.SetupData(); err != nil {
		panic(err)
	}
	code := m.Run()
	for _, s := range []*s3test.Server{s3proxy, httpB, httpH, ftpS, sftpS} {
		if s != nil {
			s.Stop()
		}
	}
	os.Exit(code)
}

func s3ProxyServer(t *testing.T) *s3test.Server {
	if s3proxy == nil {
		s3proxy = s3test.StartProxyServer(t)
	}
	return s3proxy
}
func httpBasicServer(t *testing.T) *s3test.Server {
	if httpB == nil {
		httpB = s3test.StartHTTPBasic(t)
	}
	return httpB
}
func httpHtpasswdServer(t *testing.T) *s3test.Server {
	if httpH == nil {
		httpH = s3test.StartHTTPHtpasswd(t)
	}
	return httpH
}
func ftpServer(t *testing.T) *s3test.Server {
	if ftpS == nil {
		ftpS = s3test.StartFTP(t)
	}
	return ftpS
}
func sftpServer(t *testing.T) *s3test.Server {
	if sftpS == nil {
		sftpS = s3test.StartSFTP(t)
	}
	return sftpS
}

// s3blocked asserts an S3 request was refused (any 4xx) and leaked no data.
func s3blocked(t *testing.T, code int, body, leak string) {
	t.Helper()
	if code < 400 || code >= 500 {
		t.Fatalf("attack was NOT blocked: got HTTP %d, body=%q", code, body)
	}
	if leak != "" && strings.Contains(body, leak) {
		t.Fatalf("attack leaked data %q in body: %q", leak, body)
	}
}

// httpBlocked asserts an HTTP request was refused (not 2xx) and leaked no data.
func httpBlocked(t *testing.T, code int, body string) {
	t.Helper()
	if code >= 200 && code < 300 {
		t.Fatalf("attack was NOT blocked: got HTTP %d, body=%q", code, body)
	}
	if strings.Contains(body, s3test.PubContent) {
		t.Fatalf("attack leaked served content in body: %q", body)
	}
}

// ---- base S3 auth-proxy flaw: signature verified against an empty secret ----

// 1. List buckets as alice, signed with an empty secret.
func TestS3ListBucketsAliceEmptySecret(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.AliceKey, "", nil)
	s3blocked(t, code, body, "ListAllMyBucketsResult")
}

// 2. Read one of alice's objects, signed with an empty secret (data theft).
func TestS3GetObjectAliceEmptySecret(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/alicebucket/readable.txt", s3test.AliceKey, "", nil)
	s3blocked(t, code, body, "ALICE CONFIDENTIAL FILE")
}

// 3. Write an object into alice's bucket, signed with an empty secret.
func TestS3PutObjectAliceEmptySecret(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "PUT", "/alicebucket/injected.txt", s3test.AliceKey, "", []byte("owned"))
	s3blocked(t, code, body, "")
}

// 4. Delete one of alice's objects, signed with an empty secret.
func TestS3DeleteObjectAliceEmptySecret(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "DELETE", "/alicebucket/deletable.txt", s3test.AliceKey, "", nil)
	s3blocked(t, code, body, "")
}

// 5. Act as a DIFFERENT proxy-mapped user (bob) with an empty secret.
func TestS3ListBucketsBobEmptySecret(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.BobKey, "", nil)
	s3blocked(t, code, body, "ListAllMyBucketsResult")
}

// ---- sibling: serve http single-user basic auth ----

// 6. Present the configured HTTP username with a WRONG password.
func TestHTTPBasicWrongPassword(t *testing.T) {
	s := httpBasicServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, s3test.WebUser, "totally-wrong-pass")
	httpBlocked(t, code, body)
}

// ---- sibling: serve http htpasswd-file basic auth ----

// 7. Present a username present in the htpasswd file with a WRONG password.
func TestHTTPHtpasswdWrongPassword(t *testing.T) {
	s := httpHtpasswdServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, s3test.HtUser, "totally-wrong-pass")
	httpBlocked(t, code, body)
}

// ---- sibling: serve ftp single-user auth ----

// 8. Log in as the configured FTP user with a WRONG password.
func TestFTPWrongPassword(t *testing.T) {
	s := ftpServer(t)
	if err := s3test.FTPLogin(s.Addr, s3test.FTPUser, "totally-wrong-pass"); err == nil {
		t.Fatalf("attack was NOT blocked: FTP accepted a wrong password for %q", s3test.FTPUser)
	}
}

// ---- sibling: serve sftp single-user auth ----

// 9. Authenticate as the configured SFTP user with a WRONG password.
func TestSFTPWrongPassword(t *testing.T) {
	s := sftpServer(t)
	if err := s3test.SFTPAuth(s.Addr, s3test.SFTPUser, "totally-wrong-pass"); err == nil {
		t.Fatalf("attack was NOT blocked: SFTP accepted a wrong password for %q", s3test.SFTPUser)
	}
}

// Auth-proxy mode must SERVE a client signing with the correct per-user secret the proxy
// returns: the instruction requires the signature to verify against the identity's real
// secret. The vulnerable code checks it against an empty secret, so correct users fail too;
// a fix that refuses every proxy request must fail here (added 2026-10-16, run ypUhTQw).
func TestS3ProxyAliceCorrectSecretServed(t *testing.T) {
	s := s3ProxyServer(t)
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
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.BobKey, s3test.BobSecret, nil)
	if code != http.StatusOK || !strings.Contains(body, "bobbucket") {
		t.Fatalf("bob with his correct secret was not served his bucket listing via the auth proxy: HTTP %d, body=%q", code, body)
	}
}

// The proxy knows carol but returns no secret for her: every request must be refused,
// whatever the client signs with: an empty secret, the access key ID itself, or its MD5.
// (2026-10-16: a fix that fell back to the access key ID as the secret passed before.)
func TestS3ProxyNoSecretRefused(t *testing.T) {
	s := s3ProxyServer(t)
	const carol = "AKIACAROL00000003"
	sum := md5.Sum([]byte(carol))
	for _, secret := range []string{"", carol, hex.EncodeToString(sum[:])} {
		code, body := s3test.Do(s.Base, "GET", "/alicebucket/readable.txt", carol, secret, nil)
		if code < 400 || code >= 500 || strings.Contains(body, "ALICE CONFIDENTIAL FILE") {
			t.Fatalf("identity with no secret was served (signed with %q): HTTP %d, body=%q", secret, code, body)
		}
	}
}

// Writes and deletes with the correct secret must work too: the instruction says a correctly
// authenticated client must still be served for the operations its identity is entitled to
// (list, read, write, delete). A fix that verifies reads but refuses writes fails here.
// The vulnerable code verifies against an empty secret, so this fails there too.
// (added 2026-10-16)
func TestS3ProxyAliceCorrectSecretWrites(t *testing.T) {
	s := s3ProxyServer(t)
	const obj = "/alicebucket/correct-put.txt"
	const onDisk = "/data/alice/alicebucket/correct-put.txt"
	content := []byte("ALICE WROTE THIS WITH HER OWN SECRET\n")
	_ = os.Remove(onDisk)
	code, body := s3test.Do(s.Base, "PUT", obj, s3test.AliceKey, s3test.AliceSecret, content)
	if code < 200 || code >= 300 {
		t.Fatalf("alice with her correct secret could not PUT an object via the auth proxy: HTTP %d, body=%q", code, body)
	}
	if err := s3test.WaitFile(onDisk, content, true); err != nil {
		t.Fatalf("correct-secret PUT did not store the object: %v", err)
	}
	code, body = s3test.Do(s.Base, "GET", obj, s3test.AliceKey, s3test.AliceSecret, nil)
	if code != http.StatusOK || body != string(content) {
		t.Fatalf("alice could not read back the object she wrote: HTTP %d, body=%q", code, body)
	}
	code, body = s3test.Do(s.Base, "DELETE", obj, s3test.AliceKey, s3test.AliceSecret, nil)
	if code < 200 || code >= 300 {
		t.Fatalf("alice with her correct secret could not DELETE her object via the auth proxy: HTTP %d, body=%q", code, body)
	}
	if err := s3test.WaitFile(onDisk, nil, false); err != nil {
		t.Fatalf("correct-secret DELETE did not remove the object: %v", err)
	}
}

// ---- empty passwords on the username/password surfaces (added 2026-10-16) ----
// The instruction says a wrong OR EMPTY password must be refused. (No FTP case: the FTP
// server library itself rejects a PASS command with an empty argument, so an empty FTP
// password never reaches the credential check, on vulnerable or fixed code.)

func TestHTTPBasicEmptyPassword(t *testing.T) {
	s := httpBasicServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, s3test.WebUser, "")
	httpBlocked(t, code, body)
}

func TestHTTPHtpasswdEmptyPassword(t *testing.T) {
	s := httpHtpasswdServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, s3test.HtUser, "")
	httpBlocked(t, code, body)
}

func TestSFTPEmptyPassword(t *testing.T) {
	s := sftpServer(t)
	if err := s3test.SFTPAuth(s.Addr, s3test.SFTPUser, ""); err == nil {
		t.Fatalf("attack was NOT blocked: SFTP accepted an empty password for %q", s3test.SFTPUser)
	}
}
