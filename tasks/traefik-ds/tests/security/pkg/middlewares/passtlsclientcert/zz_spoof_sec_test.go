package passtlsclientcert

import (
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

const zzSpoof = "zz-spoofed-cert"

// The headers that carry the verified client certificate must not be accompanied by a
// client-supplied spelling of the same header.
func TestSecZZPassTLSClientCertHeaderAlias(t *testing.T) {
	cert := zzClientCert(t, "zz-client")
	config := dynamic.PassTLSClientCert{
		PEM:  true,
		Info: &dynamic.TLSClientCertificateInfo{Subject: &dynamic.TLSClientCertificateSubjectDNInfo{CommonName: true}},
	}
	cases := map[string][]string{
		"X-Forwarded-Tls-Client-Cert":      {"X_Forwarded_Tls_Client_Cert", "X-Forwarded_Tls-Client-Cert", "x_forwarded_tls_client_cert"},
		"X-Forwarded-Tls-Client-Cert-Info": {"X_Forwarded_Tls_Client_Cert_Info", "X-Forwarded-Tls-Client_Cert-Info"},
	}
	for name, spellings := range cases {
		for _, spelling := range spellings {
			t.Run(name+" client "+spelling, func(t *testing.T) {
				status, backend := zzServeTLS(t, config, cert, [][2]string{{spelling, zzSpoof}})
				zzAssertNotSpoofed(t, status, backend, name, zzSpoof)
			})
		}
	}
}
