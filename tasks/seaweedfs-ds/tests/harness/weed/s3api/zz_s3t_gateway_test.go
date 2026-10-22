package s3api

// Hidden-test harness: a SeaweedFS S3 gateway (S3 Tables API and Iceberg REST
// catalog) wired the way `weed s3` wires them, backed by an in-memory filer.

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	v4 "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	"github.com/gorilla/mux"
	"github.com/seaweedfs/seaweedfs/weed/s3api/iceberg"
)

// zzStaticConfig is an operator's identities file (s3.json format).
const zzStaticConfig = `{
  "accounts": [
    {"id": "acct-alice", "displayName": "alice"},
    {"id": "acct-bob", "displayName": "bob"}
  ],
  "identities": [
    {"name": "alice", "account": {"id": "acct-alice"},
     "credentials": [{"accessKey": "AKALICE", "secretKey": "alice-secret"}],
     "actions": ["Read", "Write", "List", "Tagging", "s3tables:CreateTableBucket"]},
    {"name": "bob", "account": {"id": "acct-bob"},
     "credentials": [{"accessKey": "AKBOB", "secretKey": "bob-secret"}],
     "actions": ["Read", "Write", "List", "Tagging"]},
    {"name": "carol", "account": {"id": "admin"},
     "credentials": [{"accessKey": "AKCAROL", "secretKey": "carol-secret"}],
     "actions": ["Read", "List"]},
    {"name": "dave", "account": {"id": "acct-dave-typo"},
     "credentials": [{"accessKey": "AKDAVE", "secretKey": "dave-secret"}],
     "actions": ["Read", "List"]},
    {"name": "frank", "account": {"id": "acct-bob"},
     "credentials": [{"accessKey": "AKFRANK", "secretKey": "frank-secret"}],
     "actions": ["Read", "s3tables:GetTableBucket", "s3tables:ListTableBuckets", "s3tables:ListNamespaces"]},
    {"name": "root", "account": {"id": "admin"},
     "credentials": [{"accessKey": "AKROOT", "secretKey": "root-secret"}],
     "actions": ["Admin"]},
    {"name": "ops-star", "account": {"id": "admin"},
     "credentials": [{"accessKey": "AKOPSSTAR", "secretKey": "opsstar-secret"}],
     "actions": ["*"]},
    {"name": "ops-s3", "account": {"id": "admin"},
     "credentials": [{"accessKey": "AKOPSS3", "secretKey": "opss3-secret"}],
     "actions": ["s3:*"]},
    {"name": "ops-tables",
     "credentials": [{"accessKey": "AKOPSTABLES", "secretKey": "opstables-secret"}],
     "actions": ["s3tables:*"]},
    {"name": "anonymous", "actions": ["Read", "List"]}
  ]
}`

type zzUser struct{ ak, sk string }

var (
	zzAlice     = zzUser{"AKALICE", "alice-secret"}
	zzBob       = zzUser{"AKBOB", "bob-secret"}
	zzCarol     = zzUser{"AKCAROL", "carol-secret"}
	zzDave      = zzUser{"AKDAVE", "dave-secret"}
	zzFrank     = zzUser{"AKFRANK", "frank-secret"}
	zzRoot      = zzUser{"AKROOT", "root-secret"}
	zzOpsStar   = zzUser{"AKOPSSTAR", "opsstar-secret"}
	zzOpsS3     = zzUser{"AKOPSS3", "opss3-secret"}
	zzOpsTables = zzUser{"AKOPSTABLES", "opstables-secret"}
	zzAnon      = zzUser{}
)

type zzGateway struct {
	t      *testing.T
	filer  *zzFiler
	s3a    *S3ApiServer
	tables *httptest.Server // S3 Tables API (the S3 port)
	ice    *httptest.Server // Iceberg REST catalog port
}

var zzGatewayMu sync.Mutex

// zzNewGateway starts a gateway. withIdentities=false is a server with no
// identities configured (authentication off). auth, when not nil, replaces the
// catalog's authenticator (an embedding that plugs in its own).
func zzNewGateway(t *testing.T, filer *zzFiler, withIdentities bool, auth iceberg.S3Authenticator) *zzGateway {
	t.Helper()
	zzGatewayMu.Lock()
	defer zzGatewayMu.Unlock()
	if filer == nil {
		filer = zzStartFiler(t)
	}
	iam := &IdentityAccessManagement{}
	iam.hashes = make(map[string]*sync.Pool)
	iam.hashCounters = make(map[string]*int32)
	if withIdentities {
		if err := iam.LoadS3ApiConfigurationFromBytes([]byte(zzStaticConfig)); err != nil {
			t.Fatalf("load identities: %v", err)
		}
		if !iam.isEnabled() {
			t.Fatalf("authentication should be on once identities are configured")
		}
	}
	s3a := &S3ApiServer{
		option: &S3ApiServerOption{GrpcDialOption: zzDialOption()},
		iam:    iam,
	}
	s3a.option.Filers = append(s3a.option.Filers, filer.addr)

	router := mux.NewRouter().SkipClean(true)
	s3a.registerS3TablesRoutes(router)
	tables := httptest.NewServer(router)
	t.Cleanup(tables.Close)

	var authenticator iceberg.S3Authenticator = s3a
	if auth != nil {
		authenticator = auth
	}
	iceRouter := mux.NewRouter().SkipClean(true)
	srv := iceberg.NewServer(s3a, authenticator)
	srv.SetCredentialValidator(s3a)
	srv.RegisterRoutes(iceRouter)
	ice := httptest.NewServer(iceRouter)
	t.Cleanup(ice.Close)

	return &zzGateway{t: t, filer: filer, s3a: s3a, tables: tables, ice: ice}
}

func zzSign(t *testing.T, req *http.Request, body []byte, u zzUser, service string) {
	t.Helper()
	sum := sha256.Sum256(body)
	hash := hex.EncodeToString(sum[:])
	req.Header.Set("X-Amz-Content-Sha256", hash)
	if u.ak == "" {
		return
	}
	signer := v4.NewSigner()
	creds := aws.Credentials{AccessKeyID: u.ak, SecretAccessKey: u.sk}
	if err := signer.SignHTTP(context.Background(), creds, req, hash, service, "us-east-1", time.Now().UTC()); err != nil {
		t.Fatalf("sign: %v", err)
	}
}

type zzResp struct {
	status int
	body   []byte
}

func (r zzResp) json(t *testing.T) map[string]interface{} {
	t.Helper()
	out := map[string]interface{}{}
	if err := json.Unmarshal(r.body, &out); err != nil {
		t.Fatalf("response is not JSON (status %d): %s", r.status, string(r.body))
	}
	return out
}

func zzDo(t *testing.T, req *http.Request) zzResp {
	t.Helper()
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("%s %s: %v", req.Method, req.URL.Path, err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return zzResp{status: resp.StatusCode, body: b}
}

// tablesCall sends an S3 Tables API operation (X-Amz-Target form, as the AWS SDKs do).
// extraHeaders are sent as the client sets them.
func (g *zzGateway) tablesCall(u zzUser, op string, payload interface{}, extraHeaders map[string]string) zzResp {
	g.t.Helper()
	body, _ := json.Marshal(payload)
	req, _ := http.NewRequest(http.MethodPost, g.tables.URL+"/", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/x-amz-json-1.1")
	req.Header.Set("X-Amz-Target", "S3Tables."+op)
	for k, v := range extraHeaders {
		req.Header.Set(k, v)
	}
	zzSign(g.t, req, body, u, "s3tables")
	return zzDo(g.t, req)
}

// iceCall sends an Iceberg REST catalog request. headers are sent as given.
func (g *zzGateway) iceCall(u zzUser, method, p string, payload interface{}, headers map[string]string) zzResp {
	g.t.Helper()
	var body []byte
	if payload != nil {
		body, _ = json.Marshal(payload)
	}
	req, _ := http.NewRequest(method, g.ice.URL+p, bytes.NewReader(body))
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	zzSign(g.t, req, body, u, "s3")
	return zzDo(g.t, req)
}

func zzBucketARN(name string) string {
	return "arn:aws:s3tables:us-east-1:000000000000:bucket/" + name
}

func zzIs2xx(s int) bool { return s >= 200 && s < 300 }
func zzIs4xx(s int) bool { return s >= 400 && s < 500 }

// zzListedBuckets returns the bucket names in a ListTableBuckets response.
func zzListedBuckets(t *testing.T, r zzResp) []string {
	t.Helper()
	var out struct {
		TableBuckets []struct {
			Name string `json:"name"`
		} `json:"tableBuckets"`
	}
	if err := json.Unmarshal(r.body, &out); err != nil {
		t.Fatalf("ListTableBuckets response is not JSON (status %d): %s", r.status, string(r.body))
	}
	var names []string
	for _, b := range out.TableBuckets {
		names = append(names, b.Name)
	}
	return names
}

func zzContains(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}

func zzEsc(s string) string { return url.PathEscape(s) }

func zzHas(body []byte, s string) bool { return strings.Contains(string(body), s) }

// zzDenyAllPolicy is a bucket policy that denies every table action to everyone.
// The owner and administrators are not subject to bucket policies.
const zzDenyAllPolicy = `{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Principal":"*","Action":"s3tables:*","Resource":"*"}]}`
