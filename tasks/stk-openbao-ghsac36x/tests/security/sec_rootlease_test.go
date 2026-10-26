package vault

import (
	"testing"
)

// A lease identifier that carries no namespace part names a lease in the root
// namespace. Requests from a child namespace must not reach it, in any of the
// forms that accept a single lease identifier.

func TestSec_RevokeRootLeaseByBodyFromChild(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.rootCtx, env.root)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/leases/revoke", map[string]any{"lease_id": id, "sync": true})
}

func TestSec_RevokeRootLeaseByPathFromChild(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.rootCtx, env.root)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/leases/revoke/"+id, nil)
}

func TestSec_RevokeRootLeaseByPrefixFromChild(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.rootCtx, env.root)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/leases/revoke-prefix/"+id, nil)
}

func TestSec_RevokeRootLeaseByForceFromNestedChild(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.rootCtx, env.root)
	env.mustBlockRevoke(t, env.childCtx, env.tokChild, "sys/leases/revoke-force/"+id, nil)
}
