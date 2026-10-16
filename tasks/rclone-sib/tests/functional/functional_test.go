// Package functional holds the feature tests. They assert that each serve
// surface keeps working after a fix: a correctly authenticated client is
// served and bad credentials are still refused. A fix that over-blocks (tears
// a server down, or refuses correct credentials) fails these.
package functional

import (
	"net/http"
	"os"
	"strings"
	"testing"

	"rclones3harness/s3test"
)

var (
	s3static *s3test.Server
	s3proxy  *s3test.Server
	httpB    *s3test.Server
	httpH    *s3test.Server
	ftpS     *s3test.Server
	sftpS    *s3test.Server
)

func TestMain(m *testing.M) {
	s3test.PortBase = 38200
	if err := s3test.SetupData(); err != nil {
		panic(err)
	}
	code := m.Run()
	for _, s := range []*s3test.Server{s3static, s3proxy, httpB, httpH, ftpS, sftpS} {
		if s != nil {
			s.Stop()
		}
	}
	os.Exit(code)
}

func s3StaticServer(t *testing.T) *s3test.Server {
	if s3static == nil {
		s3static = s3test.StartStaticServer(t)
	}
	return s3static
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

// ---- S3 (base task) --------------------------------------------------------

// 1. A correctly signed static-key client is served its bucket listing.
func TestS3StaticKeyCorrectIsServed(t *testing.T) {
	s := s3StaticServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.StaticKey, s3test.StaticSecret, nil)
	if code != http.StatusOK {
		t.Fatalf("legitimate static-key request was not served: HTTP %d, body=%q", code, body)
	}
	if !strings.Contains(body, "ListAllMyBucketsResult") {
		t.Fatalf("expected a bucket listing, got: %q", body)
	}
}

// 2. A static-key client with the wrong secret is refused.
func TestS3StaticKeyWrongSecretRefused(t *testing.T) {
	s := s3StaticServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.StaticKey, "wrong-secret", nil)
	if code < 400 || code >= 500 {
		t.Fatalf("wrong static secret should be refused with a 4xx, got HTTP %d, body=%q", code, body)
	}
}

// 3. Auth-proxy mode refuses a known access key ID signed with a wrong secret.
func TestS3ProxyWrongSecretRefused(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.AliceKey, "not-the-real-secret", nil)
	if code < 400 || code >= 500 {
		t.Fatalf("wrong proxy secret should be refused with a 4xx, got HTTP %d, body=%q", code, body)
	}
}

// 4. Auth-proxy mode refuses a request with no credentials at all.
func TestS3ProxyNoAuthRefused(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.DoNoAuth(s.Base, "GET", "/")
	if code < 400 || code >= 500 {
		t.Fatalf("unauthenticated request should be refused with a 4xx error, got HTTP %d, body=%q", code, body)
	}
	if strings.Contains(body, "ListAllMyBucketsResult") {
		t.Fatalf("unauthenticated request was served a bucket listing: %q", body)
	}
}

// 5. Auth-proxy mode refuses an access key ID the proxy does not know.
func TestS3ProxyUnknownKeyRefused(t *testing.T) {
	s := s3ProxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.UnknownKey, "some-secret", nil)
	if code < 400 || code >= 500 {
		t.Fatalf("unknown access key ID should be refused with a 4xx, got HTTP %d, body=%q", code, body)
	}
}

// ---- serve http single-user basic auth ------------------------------------

// 6. The configured user with the correct password is served.
func TestHTTPBasicCorrectIsServed(t *testing.T) {
	s := httpBasicServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, s3test.WebUser, s3test.WebPass)
	if code != http.StatusOK {
		t.Fatalf("legitimate http basic request was not served: HTTP %d, body=%q", code, body)
	}
	if !strings.Contains(body, s3test.PubContent) {
		t.Fatalf("expected served file content, got: %q", body)
	}
}

// 7. An unknown HTTP username is refused.
func TestHTTPBasicUnknownUserRefused(t *testing.T) {
	s := httpBasicServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, "nobody", "whatever")
	if code >= 200 && code < 300 {
		t.Fatalf("unknown http user should be refused, got HTTP %d, body=%q", code, body)
	}
}

// ---- serve http htpasswd-file basic auth -----------------------------------

// 8. An htpasswd user with the correct password is served.
func TestHTTPHtpasswdCorrectIsServed(t *testing.T) {
	s := httpHtpasswdServer(t)
	code, body := s3test.DoBasic(s.Base, "GET", "/"+s3test.PubFile, s3test.HtUser, s3test.HtPass)
	if code != http.StatusOK {
		t.Fatalf("legitimate htpasswd request was not served: HTTP %d, body=%q", code, body)
	}
	if !strings.Contains(body, s3test.PubContent) {
		t.Fatalf("expected served file content, got: %q", body)
	}
}

// ---- serve ftp single-user auth --------------------------------------------

// 9. The configured FTP user with the correct password logs in.
func TestFTPCorrectLogin(t *testing.T) {
	s := ftpServer(t)
	if err := s3test.FTPLogin(s.Addr, s3test.FTPUser, s3test.FTPPass); err != nil {
		t.Fatalf("legitimate FTP login failed: %v", err)
	}
	// Being let in is not enough: the user must be served the remote (2026-10-16).
	names, err := s3test.FTPList(s.Addr, s3test.FTPUser, s3test.FTPPass)
	if err != nil || !contains(names, s3test.PubFile) {
		t.Fatalf("FTP listing for the correct user does not show %s: %v, %v", s3test.PubFile, names, err)
	}
	got, err := s3test.FTPGet(s.Addr, s3test.FTPUser, s3test.FTPPass, s3test.PubFile)
	if err != nil || string(got) != s3test.PubContent {
		t.Fatalf("FTP download for the correct user failed: %q, %v", got, err)
	}
}

// ---- serve sftp single-user auth -------------------------------------------

// 10. The configured SFTP user with the correct password authenticates.
func TestSFTPCorrectAuth(t *testing.T) {
	s := sftpServer(t)
	if err := s3test.SFTPAuth(s.Addr, s3test.SFTPUser, s3test.SFTPPass); err != nil {
		t.Fatalf("legitimate SFTP auth failed: %v", err)
	}
	// Being let in is not enough: the user must be served the remote (2026-10-16).
	names, err := s3test.SFTPList(s.Addr, s3test.SFTPUser, s3test.SFTPPass, "/")
	if err != nil || !contains(names, s3test.PubFile) {
		t.Fatalf("SFTP listing for the correct user does not show %s: %v, %v", s3test.PubFile, names, err)
	}
	got, err := s3test.SFTPGet(s.Addr, s3test.SFTPUser, s3test.SFTPPass, "/"+s3test.PubFile)
	if err != nil || string(got) != s3test.PubContent {
		t.Fatalf("SFTP download for the correct user failed: %q, %v", got, err)
	}
}

func contains(list []string, want string) bool {
	for _, x := range list {
		if x == want {
			return true
		}
	}
	return false
}

// ---- write paths with the correct password (added 2026-10-16) --------------
// The instruction requires a correctly authenticated client to keep being served for every
// operation its identity is entitled to, not only reads. `serve http` is read-only, so only
// FTP and SFTP have write paths. Each test uploads, reads back and deletes its own file and
// checks the effect in the served directory.

func checkWriteCycle(t *testing.T, proto, name string,
	put func(name string, data []byte) error,
	get func(name string) ([]byte, error),
	del func(name string) error) {
	t.Helper()
	onDisk := "/data/pub/" + name
	content := []byte(proto + " UPLOAD BY THE CORRECT USER\n")
	_ = os.Remove(onDisk)
	if err := put(name, content); err != nil {
		t.Fatalf("%s upload with the correct password failed: %v", proto, err)
	}
	if err := s3test.WaitFile(onDisk, content, true); err != nil {
		t.Fatalf("%s upload did not store the file: %v", proto, err)
	}
	got, err := get(name)
	if err != nil || string(got) != string(content) {
		t.Fatalf("%s read-back of the uploaded file failed: %q, %v", proto, got, err)
	}
	if err := del(name); err != nil {
		t.Fatalf("%s delete with the correct password failed: %v", proto, err)
	}
	if err := s3test.WaitFile(onDisk, nil, false); err != nil {
		t.Fatalf("%s delete did not remove the file: %v", proto, err)
	}
}

// 11. The configured FTP user can upload, read back and delete a file.
func TestFTPCorrectUserWrites(t *testing.T) {
	s := ftpServer(t)
	u, p := s3test.FTPUser, s3test.FTPPass
	checkWriteCycle(t, "FTP", "ftp-upload.txt",
		func(n string, d []byte) error { return s3test.FTPPut(s.Addr, u, p, n, d) },
		func(n string) ([]byte, error) { return s3test.FTPGet(s.Addr, u, p, n) },
		func(n string) error { return s3test.FTPDelete(s.Addr, u, p, n) })
}

// 12. The configured SFTP user can upload, read back and delete a file.
func TestSFTPCorrectUserWrites(t *testing.T) {
	s := sftpServer(t)
	u, p := s3test.SFTPUser, s3test.SFTPPass
	checkWriteCycle(t, "SFTP", "sftp-upload.txt",
		func(n string, d []byte) error { return s3test.SFTPPut(s.Addr, u, p, "/"+n, d) },
		func(n string) ([]byte, error) { return s3test.SFTPGet(s.Addr, u, p, "/"+n) },
		func(n string) error { return s3test.SFTPRemove(s.Addr, u, p, "/"+n) })
}
