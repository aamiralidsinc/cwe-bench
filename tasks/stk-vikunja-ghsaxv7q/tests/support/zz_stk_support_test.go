// Hidden test support for the stacked OpenID task. Copied into the product package at grade
// time and used only by the TestSec_/TestFunc_ suites.
package openid

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"math/big"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"code.vikunja.io/api/pkg/db"
	"code.vikunja.io/api/pkg/modules/keyvalue"
	"code.vikunja.io/api/pkg/user"

	"code.vikunja.io/api/pkg/web"
	"github.com/labstack/echo/v5"
	"github.com/stretchr/testify/require"
	"golang.org/x/oauth2"
)

const stkClientID = "stk-client"

type stkOIDC struct {
	srv         *httptest.Server
	key         *rsa.PrivateKey
	tokenClaims map[string]any
	userInfo    map[string]any
}

func stkB64(b []byte) string { return base64.RawURLEncoding.EncodeToString(b) }

type stkSigner struct {
	key *rsa.PrivateKey
}

func (s *stkSigner) sign(claims map[string]any) string {
	header := map[string]any{"alg": "RS256", "kid": "stk-key", "typ": "JWT"}
	h, _ := json.Marshal(header)
	p, _ := json.Marshal(claims)
	signing := stkB64(h) + "." + stkB64(p)
	sum := sha256.Sum256([]byte(signing))
	sig, err := rsa.SignPKCS1v15(rand.Reader, s.key, crypto.SHA256, sum[:])
	if err != nil {
		panic(err)
	}
	return signing + "." + stkB64(sig)
}

// stkNewOIDC starts an in-process OpenID Connect provider whose ID-token claims and userinfo
// response each test controls.
func stkNewOIDC(t *testing.T) *stkOIDC {
	t.Helper()
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	require.NoError(t, err)
	f := &stkOIDC{key: key}
	signer := &stkSigner{key: key}
	mux := http.NewServeMux()
	mux.HandleFunc("/.well-known/openid-configuration", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"issuer":                                f.srv.URL,
			"authorization_endpoint":                f.srv.URL + "/authorize",
			"token_endpoint":                        f.srv.URL + "/token",
			"userinfo_endpoint":                     f.srv.URL + "/userinfo",
			"jwks_uri":                              f.srv.URL + "/keys",
			"id_token_signing_alg_values_supported": []string{"RS256"},
			"response_types_supported":              []string{"code"},
			"subject_types_supported":               []string{"public"},
		})
	})
	mux.HandleFunc("/keys", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"keys": []map[string]any{{
			"kty": "RSA", "kid": "stk-key", "use": "sig", "alg": "RS256",
			"n": stkB64(key.N.Bytes()),
			"e": stkB64(big.NewInt(int64(key.E)).Bytes()),
		}}})
	})
	mux.HandleFunc("/token", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"access_token": "stk-access-token",
			"token_type":   "Bearer",
			"expires_in":   3600,
			"id_token":     signer.sign(f.tokenClaims),
		})
	})
	mux.HandleFunc("/userinfo", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(f.userInfo)
	})
	f.srv = httptest.NewServer(mux)
	t.Cleanup(f.srv.Close)
	return f
}

// stkIdentity returns token claims with all non-email fields filled so that only the email
// claims differ between tests. The picture is deliberately omitted: no avatar fetch is wanted.
func (f *stkOIDC) stkIdentity(subject string) map[string]any {
	return map[string]any{
		"iss": f.srv.URL, "aud": stkClientID, "sub": subject,
		"exp": 4102444800, "iat": 1700000000,
		"name": "Test Identity", "preferred_username": "test-identity",
	}
}

func (f *stkOIDC) stkProvider(key string, emailFallback, forceUserInfo, usernameFallback bool) *Provider {
	return &Provider{
		Name:             "STK Provider",
		Key:              key,
		OriginalAuthURL:  f.srv.URL,
		ClientID:         stkClientID,
		ClientSecret:     "stk-secret",
		EmailFallback:    emailFallback,
		UsernameFallback: usernameFallback,
		ForceUserInfo:    forceUserInfo,
		Oauth2Config: &oauth2.Config{
			ClientID:     stkClientID,
			ClientSecret: "stk-secret",
			Endpoint: oauth2.Endpoint{
				AuthURL:  f.srv.URL + "/authorize",
				TokenURL: f.srv.URL + "/token",
			},
		},
	}
}

// stkRegisterOIDCProvider makes the configured provider discoverable through the product's own
// provider lookup and returns the provider key to use in the callback request.
func (f *stkOIDC) stkRegisterOIDCProvider(t *testing.T, emailFallback, forceUserInfo, usernameFallback bool) string {
	t.Helper()
	key := "stk-" + strings.ToLower(strings.ReplaceAll(t.Name(), "/", "-"))
	if len(key) > 60 {
		key = key[:60]
	}
	require.NoError(t, keyvalue.Put("openid_provider_"+key, f.stkProvider(key, emailFallback, forceUserInfo, usernameFallback)))
	return key
}

// stkCallback drives the product's real OIDC callback endpoint and returns the response status,
// body and the error the handler returned.
func stkCallback(t *testing.T, providerKey string) (int, string, error) {
	t.Helper()
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/openid/"+providerKey+"/callback",
		strings.NewReader(`{"code":"stk-code","redirect_url":"http://localhost/callback"}`))
	req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	c.SetPathValues(echo.PathValues{{Name: "provider", Value: providerKey}})
	err := HandleCallback(c)
	return rec.Code, rec.Body.String(), err
}

// stkTokenUserID reads the user id from the session token the callback returned.
func stkTokenUserID(t *testing.T, body string) int64 {
	t.Helper()
	var response struct {
		Token string `json:"token"`
	}
	require.NoError(t, json.Unmarshal([]byte(body), &response), "the callback response must carry a session token")
	parts := strings.Split(response.Token, ".")
	require.Len(t, parts, 3)
	raw, err := base64.RawURLEncoding.DecodeString(parts[1])
	require.NoError(t, err)
	var claims struct {
		ID int64 `json:"id"`
	}
	require.NoError(t, json.Unmarshal(raw, &claims))
	return claims.ID
}

// stkRequireClientRefusal asserts the request failed with a client error and never produced a
// session token.
func stkRequireClientRefusal(t *testing.T, status int, body string, err error) {
	t.Helper()
	require.Error(t, err, "the sign-in must be refused")
	var processor web.HTTPErrorProcessor
	require.True(t, errors.As(err, &processor), "the refusal must carry an HTTP status, got %T", err)
	code := processor.HTTPError().HTTPCode
	require.GreaterOrEqual(t, code, 400, "the refusal must be a client error")
	require.Less(t, code, 500, "the refusal must be a client error")
	require.NotContains(t, body, "\"token\"", "a refused sign-in must not return a session")
}

// stkRequireSessionFor asserts the callback succeeded and authenticated the given account.
func stkRequireSessionFor(t *testing.T, userID int64, status int, body string, err error) {
	t.Helper()
	require.NoError(t, err)
	require.Equal(t, 200, status)
	require.Equal(t, userID, stkTokenUserID(t, body))
}

func stkLocalUser(t *testing.T, email string) *user.User {
	t.Helper()
	s := db.NewSession()
	defer s.Close()
	u := &user.User{}
	has, err := s.Where("email = ? AND issuer = ?", email, user.IssuerLocal).Get(u)
	require.NoError(t, err)
	require.True(t, has, "the local account %s must still exist", email)
	return u
}

func stkSetUserStatus(t *testing.T, id int64, status user.Status) {
	t.Helper()
	s := db.NewSession()
	defer s.Close()
	_, err := s.Exec("UPDATE users SET status = ? WHERE id = ?", int(status), id)
	require.NoError(t, err)
	require.NoError(t, s.Commit())
}

func stkInsertLinkedUser(t *testing.T, issuer, subject, email string) *user.User {
	t.Helper()
	s := db.NewSession()
	defer s.Close()
	u := &user.User{
		Username: "stk-linked-user",
		Email:    email,
		Issuer:   issuer,
		Subject:  subject,
		Status:   user.StatusActive,
	}
	_, err := s.Insert(u)
	require.NoError(t, err)
	require.NoError(t, s.Commit())
	return u
}

// stkCountUsersByIssuer counts the accounts the provider has created for one subject.
func stkCountUsersByIssuer(t *testing.T, issuer, subject string) int64 {
	t.Helper()
	s := db.NewSession()
	defer s.Close()
	n, err := s.Where("issuer = ? AND subject = ?", issuer, subject).Count(&user.User{})
	require.NoError(t, err)
	return n
}
