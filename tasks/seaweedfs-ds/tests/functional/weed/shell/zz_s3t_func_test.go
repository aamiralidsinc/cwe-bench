package shell

// Hidden functional tests: the admin shell manages table buckets for any account.

import (
	"bytes"
	"strings"
	"testing"
)

func zzShellEnv(f *zzFiler) *CommandEnv {
	return &CommandEnv{
		env:    make(map[string]string),
		option: &ShellOptions{FilerAddress: f.addr, GrpcDialOption: zzDialOption()},
	}
}

func TestFuncZZShellCreatesBucketForAccount(t *testing.T) {
	f := zzStartFiler(t)
	env := zzShellEnv(f)
	var out bytes.Buffer
	cmd := &commandS3TablesBucket{}
	if err := cmd.Do([]string{"-create", "-name", "shell-tb", "-account", "bob"}, env, &out); err != nil {
		t.Fatalf("s3tables.bucket -create: %v", err)
	}
	if owner := f.bucketOwner("shell-tb"); owner != "bob" {
		t.Fatalf("bucket owner = %q, want bob", owner)
	}
	out.Reset()
	if err := cmd.Do([]string{"-list", "-account", "bob"}, env, &out); err != nil {
		t.Fatalf("s3tables.bucket -list: %v", err)
	}
	if !strings.Contains(out.String(), "shell-tb") {
		t.Fatalf("list output misses shell-tb: %s", out.String())
	}
	out.Reset()
	if err := cmd.Do([]string{"-get", "-name", "shell-tb", "-account", "bob"}, env, &out); err != nil {
		t.Fatalf("s3tables.bucket -get: %v", err)
	}
}

func TestFuncZZShellManagesAnyAccountsBucket(t *testing.T) {
	f := zzStartFiler(t)
	f.seedTableBucket("alice-old", "acct-alice", "")
	env := zzShellEnv(f)
	var out bytes.Buffer
	cmd := &commandS3TablesBucket{}
	if err := cmd.Do([]string{"-get", "-name", "alice-old", "-account", "ops"}, env, &out); err != nil {
		t.Fatalf("s3tables.bucket -get for another account's bucket: %v", err)
	}
	out.Reset()
	if err := cmd.Do([]string{"-delete", "-name", "alice-old", "-account", "ops"}, env, &out); err != nil {
		t.Fatalf("s3tables.bucket -delete for another account's bucket: %v", err)
	}
	if f.isTableBucket("alice-old") {
		t.Fatalf("alice-old still exists")
	}
}
