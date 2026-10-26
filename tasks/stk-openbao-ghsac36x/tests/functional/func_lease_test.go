package vault

import (
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

func TestFunc_SameNamespaceRevokeForms(t *testing.T) {
	env := stkNewEnv(t)

	id := env.lease(t, env.ctx1, env.tok1)
	_, err := env.do(env.ctx1, env.tok1, "sys/leases/revoke", map[string]any{"lease_id": id, "sync": true})
	require.NoError(t, err)
	require.False(t, env.alive(t, env.ctx1, id), "same-namespace revoke by body must work")

	id = env.lease(t, env.ctx1, env.tok1)
	_, err = env.do(env.ctx1, env.tok1, "sys/leases/revoke/"+id, nil)
	require.NoError(t, err)
	require.False(t, env.alive(t, env.ctx1, id), "same-namespace revoke by path must work")
}

func TestFunc_SameNamespaceRevokePrefixForms(t *testing.T) {
	env := stkNewEnv(t)

	a := env.lease(t, env.ctx1, env.tok1)
	b := env.lease(t, env.ctx1, env.tok1)
	_, err := env.do(env.ctx1, env.tok1, "sys/leases/revoke-prefix/test", nil)
	require.NoError(t, err)
	require.False(t, env.alive(t, env.ctx1, a), "prefix revoke must cover the caller's own leases")
	require.False(t, env.alive(t, env.ctx1, b), "prefix revoke must cover the caller's own leases")

	id := env.lease(t, env.ctx1, env.tok1)
	_, err = env.do(env.ctx1, env.tok1, "sys/leases/revoke-prefix/"+id, nil)
	require.NoError(t, err)
	require.False(t, env.alive(t, env.ctx1, id), "single-identifier prefix revoke must work")

	id = env.lease(t, env.ctx1, env.tok1)
	_, err = env.do(env.ctx1, env.tok1, "sys/leases/revoke-force/"+id, nil)
	require.NoError(t, err)
	require.False(t, env.alive(t, env.ctx1, id), "single-identifier force revoke must work")
}

func TestFunc_SameNamespaceDeferredRevoke(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	res, err := env.do(env.ctx1, env.tok1, "sys/leases/revoke", map[string]any{"lease_id": id, "sync": false})
	require.NoError(t, err)
	require.True(t, res == nil || !res.IsError(), "deferred revoke must be accepted")
}

func TestFunc_ParentNamespaceAdministersChildLease(t *testing.T) {
	env := stkNewEnv(t)

	id := env.lease(t, env.ctx1, env.tok1)
	_, err := env.do(env.rootCtx, env.root, "sys/leases/revoke", map[string]any{"lease_id": id, "sync": true})
	require.NoError(t, err)
	require.False(t, env.alive(t, env.ctx1, id), "a parent operator must be able to revoke a child lease by body")
}

func TestFunc_RootNamespaceManagesRootLeases(t *testing.T) {
	env := stkNewEnv(t)

	id := env.lease(t, env.rootCtx, env.root)
	_, err := env.do(env.rootCtx, env.root, "sys/leases/revoke", map[string]any{"lease_id": id, "sync": true})
	require.NoError(t, err)
	require.False(t, env.alive(t, env.rootCtx, id), "a root request must revoke a root lease by body")

	id = env.lease(t, env.rootCtx, env.root)
	_, err = env.do(env.rootCtx, env.root, "sys/leases/revoke/"+id, nil)
	require.NoError(t, err)
	require.False(t, env.alive(t, env.rootCtx, id), "a root request must revoke a root lease by path")

	id = env.lease(t, env.rootCtx, env.root)
	_, err = env.do(env.rootCtx, env.root, "sys/leases/revoke-prefix/"+id, nil)
	require.NoError(t, err)
	require.False(t, env.alive(t, env.rootCtx, id), "a root request must revoke a root lease by prefix")
}

func TestFunc_LeaseDetailsReadableInScope(t *testing.T) {
	env := stkNewEnv(t)

	id := env.lease(t, env.ctx1, env.tok1)
	res, err := env.do(env.ctx1, env.tok1, "sys/leases/lookup", map[string]any{"lease_id": id})
	require.NoError(t, err)
	require.False(t, res.IsError())
	require.Equal(t, "test/generate-lease", res.Data["path"])

	res, err = env.do(env.rootCtx, env.root, "sys/leases/lookup", map[string]any{"lease_id": id})
	require.NoError(t, err)
	require.False(t, res.IsError(), "a parent operator must be able to read a child lease")

	own := env.lease(t, env.rootCtx, env.root)
	res, err = env.do(env.rootCtx, env.root, "sys/leases/lookup", map[string]any{"lease_id": own})
	require.NoError(t, err)
	require.False(t, res.IsError(), "a root request must read a root lease")
	require.Equal(t, "test/generate-lease", res.Data["path"])
}

func TestFunc_LeaseRenewalForms(t *testing.T) {
	env := stkNewEnv(t)

	id := env.lease(t, env.ctx1, env.tok1)
	for _, path := range []string{"sys/leases/renew", "sys/leases/renew/" + id} {
		data := map[string]any{"increment": 60}
		if path == "sys/leases/renew" {
			data["lease_id"] = id
		}
		res, err := env.do(env.ctx1, env.tok1, path, data)
		require.NoError(t, err, "same-namespace renewal must work: %s", path)
		require.True(t, res == nil || !res.IsError(), "same-namespace renewal must work: %s", path)
	}

	res, err := env.do(env.rootCtx, env.root, "sys/leases/renew", map[string]any{"lease_id": id, "increment": 60})
	require.NoError(t, err, "a parent operator must renew a child lease by body")
	require.True(t, res == nil || !res.IsError())
}

func TestFunc_TokenRevocationRevokesItsLeasesAcrossNamespaces(t *testing.T) {
	env := stkNewEnv(t)

	id := env.lease(t, env.ctx1, env.tok1)
	before := env.counter.count()

	res, err := env.do(env.rootCtx, env.root, "auth/token/revoke", map[string]any{"token": env.tok1})
	require.NoError(t, err)
	require.True(t, res == nil || !res.IsError(), "revoking a child token from a parent must work")

	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) && env.counter.count() == before {
		time.Sleep(50 * time.Millisecond)
	}
	require.Greater(t, env.counter.count(), before,
		"revoking a token must revoke the leases it created in its own namespace")
	require.False(t, env.alive(t, env.ctx1, id))
}
