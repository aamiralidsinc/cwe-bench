package command

// Hidden functional test: `weed mini` bootstraps its configured table buckets.

import (
	"fmt"
	"testing"

	"github.com/seaweedfs/seaweedfs/weed/s3api/s3tables"
)

func zzPointMiniAtFiler(t *testing.T, f *zzFiler) {
	t.Helper()
	var host string
	var httpPort, grpcPort int
	if _, err := fmt.Sscanf(string(f.addr), "127.0.0.1:%d.%d", &httpPort, &grpcPort); err != nil {
		t.Fatalf("filer address %q: %v", f.addr, err)
	}
	host = "127.0.0.1"
	oldIp, oldPort, oldGrpc := *miniIp, *miniFilerOptions.port, *miniFilerOptions.portGrpc
	*miniIp, *miniFilerOptions.port, *miniFilerOptions.portGrpc = host, httpPort, grpcPort
	t.Cleanup(func() {
		*miniIp, *miniFilerOptions.port, *miniFilerOptions.portGrpc = oldIp, oldPort, oldGrpc
	})
}

func TestFuncZZMiniBootstrapsTableBuckets(t *testing.T) {
	f := zzStartFiler(t)
	f.seedTableBucket("taken-tb", "acct-alice", "")
	zzPointMiniAtFiler(t, f)

	if err := ensureMiniTableBuckets("boot-tb, boot-two, taken-tb"); err != nil {
		t.Fatalf("ensureMiniTableBuckets: %v", err)
	}
	for _, name := range []string{"boot-tb", "boot-two"} {
		if !f.isTableBucket(name) {
			t.Fatalf("%s not created", name)
		}
		if owner := f.bucketOwner(name); owner != s3tables.DefaultAccountID {
			t.Fatalf("%s owner = %q, want %q", name, owner, s3tables.DefaultAccountID)
		}
	}
	if owner := f.bucketOwner("taken-tb"); owner != "acct-alice" {
		t.Fatalf("existing bucket taken-tb changed owner to %q", owner)
	}
	// A second start finds the buckets already there.
	if err := ensureMiniTableBuckets("boot-tb"); err != nil {
		t.Fatalf("second ensureMiniTableBuckets: %v", err)
	}
	if !f.isTableBucket("boot-tb") || f.bucketOwner("boot-tb") != s3tables.DefaultAccountID {
		t.Fatalf("boot-tb changed on second start")
	}
}
