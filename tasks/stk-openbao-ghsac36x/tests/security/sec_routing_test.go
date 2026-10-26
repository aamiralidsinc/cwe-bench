package vault

import (
	"testing"
)

// Requests that name a lease in another namespace must not be authorized by the
// namespace the caller happens to sit in. These drive the canonical lease
// endpoints through their path forms.

func TestSec_RevokeByPathForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/leases/revoke/"+id, nil)
}

func TestSec_RevokePrefixSingleIDForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/leases/revoke-prefix/"+id, nil)
}

func TestSec_RevokeForceSingleIDForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/leases/revoke-force/"+id, nil)
}

func TestSec_RevokeParentLeaseFromChildNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.childCtx, env.tokChild, "sys/leases/revoke/"+id, nil)
}

func TestSec_RevokePrefixParentLeaseFromChildNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.childCtx, env.tokChild, "sys/leases/revoke-prefix/"+id, nil)
}
