#!/bin/bash
# netguard wiring check: blocked routes must fail, open routes must work. Runs inside main.
mkdir -p /logs/verifier
pass=0; fail=0; out=""
code() { curl -s -o /dev/null -m 25 -w '%{http_code}' "$1"; }
check() { # name expected actual
  if [ "$2" = "$3" ]; then pass=$((pass+1)); r=pass; else fail=$((fail+1)); r=FAIL; fi
  out="$out$r $1 expected=$2 got=$3\n"
}
check "raw own repo"        403 "$(code https://raw.githubusercontent.com/rclone/rclone/master/README.md)"
check "api own repo"        403 "$(code https://api.github.com/repos/rclone/rclone)"
check "fork path"           403 "$(code https://github.com/ncw/rclone)"
check "own repo advisory"   403 "$(code https://github.com/rclone/rclone/security/advisories)"
check "go proxy release"    403 "$(code https://proxy.golang.org/github.com/rclone/rclone/@v/list)"
check "pypi own name"       403 "$(code https://pypi.org/simple/rclone/)"
git ls-remote https://github.com/rclone/rclone >/dev/null 2>&1; check "git ls-remote own repo" fail "$([ $? = 0 ] && echo ok || echo fail)"
timeout 8 bash -c 'echo > /dev/tcp/github.com/22' 2>/dev/null; check "ssh port 22 egress" fail "$([ $? = 0 ] && echo ok || echo fail)"
check "other repo raw"      200 "$(code https://raw.githubusercontent.com/minio/minio/master/README.md)"
check "global advisory db"  200 "$(code https://github.com/advisories)"
check "plain site"          200 "$(code https://example.com/)"
check "pypi other package"  200 "$(code https://pypi.org/simple/requests/)"
check "python tls other"    200 "$(python3 -c "import urllib.request;print(urllib.request.urlopen('https://pypi.org/simple/six/',timeout=25).status)" 2>/dev/null)"
git ls-remote https://github.com/minio/mc >/dev/null 2>&1; check "git ls-remote other repo" ok "$([ $? = 0 ] && echo ok || echo fail)"
printf "$out" | tee /logs/verifier/checks.txt
reward=$([ $fail = 0 ] && echo 1 || echo 0)
echo $reward > /logs/verifier/reward.txt; printf '{"reward": %s}\n' $reward > /logs/verifier/reward.json
