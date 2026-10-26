package vault

import (
	"testing"
)

// Reading a lease's details is a lease-scoped operation too: a request from one
// namespace must not obtain the details of a lease that belongs to another.

func TestSec_LookupRootLeaseFromSiblingNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.rootCtx, env.root)
	env.mustBlockLookup(t, env.ctx2, env.tok2, id)
}

func TestSec_LookupRootLeaseFromNestedNamespace(t *testing.T) {
	env := stkNewEnv(t)
	id := env.lease(t, env.rootCtx, env.root)
	env.mustBlockLookup(t, env.childCtx, env.tokChild, id)
}
