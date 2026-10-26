package vault

import (
	"testing"
)

// The older lease aliases sit outside the canonical namespace scoping and must
// enforce the same isolation.

func TestSec_LegacyRevokeByPathForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/revoke/"+id, nil)
}

func TestSec_LegacyRevokeByBodyForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/revoke", map[string]any{"lease_id": id, "sync": true})
}

func TestSec_LegacyRevokePrefixForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/revoke-prefix/"+id, nil)
}

func TestSec_LegacyRevokeForceForeignNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.ctx2, env.tok2, "sys/revoke-force/"+id, nil)
}

func TestSec_LegacyRevokeParentLeaseFromChildNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.ctx1, env.tok1)
	env.mustBlockRevoke(t, env.childCtx, env.tokChild, "sys/revoke/"+id, nil)
}
