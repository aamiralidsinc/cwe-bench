// authproxy is the auth-proxy program used with `rclone serve s3 --auth-proxy`.
//
// rclone runs it once per authentication, passing a JSON object on stdin and
// reading a JSON object on stdout. It maps a small set of access key IDs to a
// local backend directory and the secret access key for that ID.
//
// It recovers the access key ID across both the old and new auth-proxy
// protocols so the same program works whatever the server does with it:
//   - new protocol: the access key ID is sent as "user" with no "pass".
//   - old protocol: an MD5 hash is sent as "user" and the access key ID itself
//     as "pass".
//
// An unknown access key ID is refused (the program exits non-zero).
package main

import (
	"encoding/json"
	"log"
	"os"
)

// accessKeyID -> {backend root, secret access key}
var mapping = map[string][2]string{
	"AKIAALICE00000001": {"/data/alice", "alice-secret-0001"},
	"AKIABOB0000000002": {"/data/bob", "bob-secret-0002"},
	// carol is known to the proxy but has NO secret: a fix must refuse her requests
	// (2026-10-16). Mapped onto alice's data so any acceptance visibly leaks.
	"AKIACAROL00000003": {"/data/alice", ""},
}

func main() {
	var in map[string]string
	if err := json.NewDecoder(os.Stdin).Decode(&in); err != nil {
		log.Fatalf("authproxy: decode input: %v", err)
	}
	accessKeyID := in["user"]
	if pass, ok := in["pass"]; ok { // old protocol carries the access key ID in pass
		accessKeyID = pass
	}
	m, ok := mapping[accessKeyID]
	if !ok {
		log.Fatalf("authproxy: unknown access key ID %q", accessKeyID)
	}
	out := map[string]string{"type": "local", "_root": m[0]}
	if m[1] != "" {
		out["_secret_access_key"] = m[1]
	}
	if err := json.NewEncoder(os.Stdout).Encode(&out); err != nil {
		log.Fatalf("authproxy: encode output: %v", err)
	}
}
