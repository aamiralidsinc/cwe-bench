# rclone-sib build notes

Injection task built on the mined base task `rclone` (CWE-287 auth bypass in
`serve s3 --auth-proxy`, DeepSeek-solved).

## What was verified
- Base s3 flaw unchanged and still reproduces (injection patch touches only the
  sibling files).
- 4 injected siblings, each an independent credential-verification site in a
  distinct serve surface, each reachable over its real protocol from a local
  client:
  1. `serve http --user/--pass` (lib/http single-user basic auth)
  2. `serve http --htpasswd`    (lib/http htpasswd basic auth)
  3. `serve ftp --user/--pass`  (cmd/serve/ftp)
  4. `serve sftp --user/--pass` (cmd/serve/sftp)
- Oracle fix.patch = revert the 4 injected sites to upstream form + the base s3
  upstream fix. Applies to the injected /app with `patch -p1`.

## Decisive checks (manifest patch_checks)
- base_fix_only.patch  -> security_fail (base s3 fix only; 4 siblings open)
- partial_fix.patch    -> security_fail (3/4 siblings + s3 fixed; sftp open)
- disable_feature.patch-> functional_fail (http basic auth rejects everyone)
- alt_correct_fix.patch-> pass (differently-shaped correct fix)

## Environment reuse
Same base image as task `rclone` (golang:1.26-bookworm, same git fetch of the
vulnerable commit) so Docker reuses the base build layers; the only added build
work is the injection patch (invalidates the rclone build layer -> one full
rebuild) and the harness now resolves two extra client deps (jlaffaye/ftp,
golang.org/x/crypto) at build time via `go mod tidy`.

## Not done
- No model trials run (per instructions).

## 2026-10-16 test repair

Brief: build/audit/REPAIR-BRIEF-2026-10-16.md. Items and decisions:

| # | Item (source) | Decision |
|---|---|---|
| 1 | No correct-secret test; refuse-all proxy patch scored 1.0 (ypUhTQw audit, mimo-seq1) | already fixed earlier today (TestS3Proxy{Alice,Bob}CorrectSecretServed, reject_all_proxy.patch) |
| 2 | Correct-secret tests check GET only (coordinator notes; also the rclone mimo-r21 REC) | **fixed**: security::TestS3ProxyAliceCorrectSecretWrites does a correct-secret PUT (checked on disk), GET read-back and DELETE (checked gone on disk). It sits in the security group because the vulnerable code refuses correct secrets too. |
| 3 | Sibling write paths with the correct password | **fixed**: functional::TestFTPCorrectUserWrites and TestSFTPCorrectUserWrites upload, read back and delete their own file, with the side effect checked in /data/pub. `serve http` has no write path (GET-only router), so it gets no write test. |
| 4 | FTP/SFTP correct-login tests check only that login succeeds (mimo-r21 Q268R5d audit) | **fixed**: TestFTPCorrectLogin and TestSFTPCorrectAuth now also list the root (pubfile.txt must be listed) and download pubfile.txt (content must match). |
| 5 | Empty password on the siblings (deepseek-r21 and deepseek-seq3 RECs; instruction says "wrong or empty password") | **fixed** for HTTP basic, htpasswd and SFTP (security::Test{HTTPBasic,HTTPHtpasswd,SFTP}EmptyPassword). FTP **skipped**: goftp.io/server rejects a PASS with an empty argument ("553 required param missing") before rclone's credential check, so the case cannot fail on the vulnerable code (nop showed it passing). |
| 6 | Wrong non-empty S3 secret as a security test (deepseek-r21 REC) | skip: already covered by functional::TestS3ProxyWrongSecretRefused (a failure there forces reward 0) |
| 7 | Siblings recoverable by diffing against public upstream / lookup-assisted solves (deepseek-seq3, mimo-r4 RECs) | skip: task-design note, not a test fault; out of scope for a test repair |

Fairness: every new assertion follows from instruction.md ("list, read, write and delete";
"a client that presents the correct secret or password ... must still be served"; "a wrong or
empty password must be refused"). No instruction change. The tests use no product helpers; they
use only protocol clients, plus checks on the backing directories the tests create. The new SFTP
client is a minimal SFTP v3 implementation over x/crypto/ssh in tests/lib/s3test.go, because the
harness module has no pkg/sftp and the verifier runs with GOPROXY=off.

New patch checks (each = reference fix + one defect):
- proxy_reads_only.patch (security_fail): --auth-proxy verifies the secret but refuses non-GET/HEAD -> fails only TestS3ProxyAliceCorrectSecretWrites.
- siblings_reads_only.patch (functional_fail): ftp/sftp refuse uploads -> fails TestFTPCorrectUserWrites, TestSFTPCorrectUserWrites.
- empty_password_accepted.patch (security_fail): sftp and single-user http compare the password only when one is supplied -> fails TestHTTPBasicEmptyPassword, TestSFTPEmptyPassword.
- login_serves_nothing.patch (functional_fail): correct FTP/SFTP login, but no listing or download -> fails TestFTPCorrectLogin, TestSFTPCorrectAuth (+ the write tests).

Gate (build/rclone-sib/gate-20261016-repair.log): **PASSED**. nop: 16 security tests all fail, 12 functional tests all pass;
oracle 1.0 twice; alt_correct_fix 1.0; every existing check still behaves as declared.
(The first attempt failed in nop when the Colima Docker disk was 100% full. It passed after the coordinator freed space.)

Regrade (build/regrade_from_code.py, with the repaired tests: 16 security + 12 functional) of every saved-code run whose reward was 1.0:

| trial | old | new | failing tests |
|---|---|---|---|
| rclone-sib-deepseek-r21-20261015-231813-n001/rclone-sib__zb5n8CC | 1.0 | 1.0 (regrade-20261016T080023Z) | none |
| rclone-sib-mimo-r21-20261015-231843-n001/rclone-sib__Q268R5d | 1.0 | 1.0 (regrade-20261016T070354Z) | none |
| rclone-sib-mimo-r4-20261015-190745-n001/rclone-sib__ZQjsPJU | 1.0 | 1.0 (regrade-20261016T075921Z) | none |
| rclone-sib-mimo-r5-20261015-190805-n001/rclone-sib__KSSdUqb | 1.0 | 1.0 (regrade-20261016T075953Z) | none |

Not regraded: mimo-r6 StBjAQQ (0.8182; no test was relaxed, so runs below 1.0 are not regraded); the
seq* runs and mimo-r4 Yxr3bw7 (no final-code/changes.patch). No reward dropped.
