package passtlsclientcert

import (
	"encoding/base64"
	"net/http"
	"net/url"
	"reflect"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

// With only the certificate enabled, Traefik sets the certificate header; the info header it does
// not manage, and unrelated underscore headers, arrive unchanged.
func TestFuncZZPassTLSClientCertPEMKeepsOtherHeaders(t *testing.T) {
	cert := zzClientCert(t, "zz-client")
	status, backend := zzServeTLS(t, dynamic.PassTLSClientCert{PEM: true}, cert, [][2]string{
		{"X_Request_Tag", "tag-1"},
		{"X_Forwarded_Tls_Client_Cert_Info", "info-1"},
	})
	reached, header := backend.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("status %d, reached backend %v", status, reached)
	}
	want := base64.StdEncoding.EncodeToString(cert.Certificate[0])
	if got := header["X-Forwarded-Tls-Client-Cert"]; !reflect.DeepEqual(got, []string{want}) {
		t.Errorf("X-Forwarded-Tls-Client-Cert = %v, want [%s]", got, want)
	}
	if got := header["X_request_tag"]; !reflect.DeepEqual(got, []string{"tag-1"}) {
		t.Errorf("unrelated X_Request_Tag = %v, want unchanged (headers %v)", got, header)
	}
	if got := header["X_forwarded_tls_client_cert_info"]; !reflect.DeepEqual(got, []string{"info-1"}) {
		t.Errorf("unmanaged X_Forwarded_Tls_Client_Cert_Info = %v, want unchanged (headers %v)", got, header)
	}
}

// With the certificate info enabled, the info header carries the selected subject fields.
func TestFuncZZPassTLSClientCertInfoKeepsOtherHeaders(t *testing.T) {
	cert := zzClientCert(t, "zz-client")
	config := dynamic.PassTLSClientCert{
		Info: &dynamic.TLSClientCertificateInfo{Subject: &dynamic.TLSClientCertificateSubjectDNInfo{CommonName: true}},
	}
	status, backend := zzServeTLS(t, config, cert, [][2]string{{"X_Request_Tag", "tag-1"}})
	reached, header := backend.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("status %d, reached backend %v", status, reached)
	}
	want := url.QueryEscape(`Subject="CN=zz-client"`)
	if got := header["X-Forwarded-Tls-Client-Cert-Info"]; !reflect.DeepEqual(got, []string{want}) {
		t.Errorf("X-Forwarded-Tls-Client-Cert-Info = %v, want [%s]", got, want)
	}
	if got := header["X_request_tag"]; !reflect.DeepEqual(got, []string{"tag-1"}) {
		t.Errorf("unrelated X_Request_Tag = %v, want unchanged (headers %v)", got, header)
	}
}
