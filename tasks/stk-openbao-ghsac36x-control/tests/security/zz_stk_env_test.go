package vault

// Shared fixtures for the lease-isolation suites. These files are copied into
// the product's vault package at grading time, so everything here is prefixed
// to stay clear of the project's own test helpers.

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/openbao/openbao/helper/namespace"
	"github.com/openbao/openbao/sdk/v2/logical"
	backendTest "github.com/openbao/openbao/vault/backend"
	"github.com/stretchr/testify/require"
)

// stkCounter records revocations that actually reached a backend.
type stkCounter struct {
	mu      sync.Mutex
	revokes int
}

func (c *stkCounter) add() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.revokes++
}

func (c *stkCounter) count() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.revokes
}

type stkBackend struct {
	backendTest.Noop
	counter *stkCounter
}

func (b *stkBackend) HandleRequest(ctx context.Context, req *logical.Request) (*logical.Response, error) {
	if req.Operation == logical.RevokeOperation {
		b.counter.add()
	}
	return b.Noop.HandleRequest(ctx, req)
}

type stkEnv struct {
	core    *Core
	root    string
	counter *stkCounter

	ns1, ns2, child *namespace.Namespace
	rootCtx         context.Context
	ctx1, ctx2      context.Context
	childCtx        context.Context
	tok1, tok2      string
	tokChild        string
}

const stkPolicy = `
path "sys/leases/*" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/leases/revoke" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/leases/renew" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/leases/lookup" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/leases/revoke-prefix/*" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/leases/revoke-force/*" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/revoke*" { capabilities = ["create", "read", "update", "sudo"] }
path "sys/renew*" { capabilities = ["create", "read", "update", "sudo"] }
path "test/*" { capabilities = ["create", "read", "update", "sudo"] }
path "auth/token/*" { capabilities = ["create", "read", "update", "sudo"] }
`

func stkNewEnv(t *testing.T) *stkEnv {
	t.Helper()

	core, _, root := TestCoreUnsealed(t)

	ns1 := &namespace.Namespace{Path: "ns1"}
	ns2 := &namespace.Namespace{Path: "ns2"}
	child := &namespace.Namespace{Path: "ns1/child"}
	TestCoreCreateNamespaces(t, core, ns1, ns2, child)

	counter := &stkCounter{}
	core.logicalBackends["test"] = func(context.Context, *logical.BackendConfig) (logical.Backend, error) {
		return &stkBackend{
			Noop: backendTest.Noop{
				BackendType: logical.TypeLogical,
				Response: &logical.Response{
					Secret: &logical.Secret{
						LeaseOptions: logical.LeaseOptions{TTL: time.Hour, Renewable: true},
					},
				},
			},
			counter: counter,
		}, nil
	}

	env := &stkEnv{
		core:     core,
		root:     root,
		counter:  counter,
		ns1:      ns1,
		ns2:      ns2,
		child:    child,
		rootCtx:  namespace.RootContext(context.Background()),
		ctx1:     namespace.ContextWithNamespace(context.Background(), ns1),
		ctx2:     namespace.ContextWithNamespace(context.Background(), ns2),
		childCtx: namespace.ContextWithNamespace(context.Background(), child),
	}

	for _, ctx := range []context.Context{env.rootCtx, env.ctx1, env.ctx2, env.childCtx} {
		res, err := core.HandleRequest(ctx, &logical.Request{
			Path:        "sys/mounts/test",
			Operation:   logical.UpdateOperation,
			ClientToken: root,
			Data:        map[string]any{"type": "test"},
		})
		require.NoError(t, err)
		require.NoError(t, res.Error())
	}

	env.tok1 = stkMintToken(t, env, env.ctx1)
	env.tok2 = stkMintToken(t, env, env.ctx2)
	env.tokChild = stkMintToken(t, env, env.childCtx)
	return env
}

func stkMintToken(t *testing.T, env *stkEnv, ctx context.Context) string {
	t.Helper()
	res, err := env.core.HandleRequest(ctx, &logical.Request{
		Path:        "sys/policy/test",
		Operation:   logical.UpdateOperation,
		ClientToken: env.root,
		Data:        map[string]any{"rules": stkPolicy},
	})
	require.NoError(t, err)
	require.NoError(t, res.Error())

	res, err = env.core.HandleRequest(ctx, &logical.Request{
		Path:        "auth/token/create",
		Operation:   logical.UpdateOperation,
		ClientToken: env.root,
		Data:        map[string]any{"policies": []string{"test"}, "ttl": "1h"},
	})
	require.NoError(t, err)
	require.NoError(t, res.Error())
	return res.Auth.ClientToken
}

func (e *stkEnv) do(ctx context.Context, token, path string, data map[string]any) (*logical.Response, error) {
	return e.core.HandleRequest(ctx, &logical.Request{
		Operation:   logical.UpdateOperation,
		Path:        path,
		ClientToken: token,
		Data:        data,
	})
}

func (e *stkEnv) lease(t *testing.T, ctx context.Context, token string) string {
	t.Helper()
	res, err := e.core.HandleRequest(ctx, &logical.Request{
		Operation:   logical.ReadOperation,
		Path:        "test/generate-lease",
		ClientToken: token,
	})
	require.NoError(t, err)
	require.NoError(t, res.Error())
	require.NotNil(t, res.Secret)
	return res.Secret.LeaseID
}

// alive reports whether the lease can still be looked up from the namespace
// that owns it.
func (e *stkEnv) alive(t *testing.T, owner context.Context, leaseID string) bool {
	t.Helper()
	res, err := e.do(owner, e.root, "sys/leases/lookup", map[string]any{"lease_id": leaseID})
	if err != nil || res == nil || res.IsError() {
		return false
	}
	return true
}

// stkRefused reports whether the operation reported a client-side refusal.
func stkRefused(res *logical.Response, err error) bool {
	if err != nil {
		return true
	}
	return res != nil && res.IsError()
}

// mustBlockRevoke asserts that the request was refused and that no revocation
// reached a backend.
func (e *stkEnv) mustBlockRevoke(t *testing.T, ctx context.Context, token, path string, data map[string]any) {
	t.Helper()
	before := e.counter.count()
	res, err := e.do(ctx, token, path, data)
	if !stkRefused(res, err) {
		t.Fatalf("revocation request %q reported success", path)
	}
	if got := e.counter.count(); got != before {
		t.Fatalf("revocation request %q revoked the target lease", path)
	}
}

// mustBlockLookup asserts that the request did not disclose lease details.
func (e *stkEnv) mustBlockLookup(t *testing.T, ctx context.Context, token string, leaseID string) {
	t.Helper()
	res, err := e.do(ctx, token, "sys/leases/lookup", map[string]any{"lease_id": leaseID})
	if !stkRefused(res, err) {
		t.Fatalf("lease lookup for %q reported success", leaseID)
	}
	if res != nil && res.Data != nil {
		if _, ok := res.Data["path"]; ok {
			t.Fatalf("lease lookup for %q disclosed lease details", leaseID)
		}
		if _, ok := res.Data["ttl"]; ok {
			t.Fatalf("lease lookup for %q disclosed lease details", leaseID)
		}
	}
}
