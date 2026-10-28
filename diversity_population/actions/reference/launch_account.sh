#!/bin/bash
# Set up the build matrix on ONE more account and dispatch its share of the jobs.
#   KEY_FILE=... bash launch_account.sh <TOKEN_VAR_IN_.env> <ids, e.g. t08,t09,...>
# Creates <login>/build-matrix-k7 (public: workflow + README + the SAME encrypted payload), commits as
# the account's GitHub no-reply address, pushes over HTTPS with the token (not stored anywhere), sets
# the two secrets from files, and dispatches the ids in build mode. The token lives only in this process.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
VAR=${1:?token variable name in ~/terminal-bench/.env}; IDS=${2:?comma-separated ids}
KEY_FILE=${KEY_FILE:?set KEY_FILE to the payload passphrase file}
ENVF=~/terminal-bench/.env
export GH_TOKEN=$(grep "^$VAR=" "$ENVF" | cut -d= -f2- | tr -d "\"' \r")
LOGIN=$(gh api user -q .login); UID_=$(gh api user -q .id); REPO="$LOGIN/build-matrix-k7"
echo "account: $LOGIN -> $REPO; ids: $IDS"

# 1. A separate working copy per account (own commit identity), same workflow and payload.
W="$HERE/repo-$LOGIN"; rm -rf "$W"; mkdir -p "$W/.github/workflows"
cp "$HERE/repo/.github/workflows/matrix.yml" "$W/.github/workflows/"
cp "$HERE/repo/README.md" "$HERE/repo/payload.tar.gz.gpg" "$W/"
cd "$W"
git init -q -b main
git config user.name "$LOGIN"
git config user.email "$UID_+$LOGIN@users.noreply.github.com"
git add . && git commit -qm "build matrix"

# 2. Repo + push (HTTPS; the token is passed as a one-off header, never written to git config).
gh repo view "$REPO" >/dev/null 2>&1 || gh repo create "$REPO" --public --description "build matrix" >/dev/null
AUTH=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 | tr -d '\n')
git -c credential.helper= -c "http.extraHeader=Authorization: Basic $AUTH" \
    push -q "https://github.com/$REPO.git" main
unset AUTH

# 3. Secrets (read from files; never echoed).
gh secret set PAYLOAD_KEY -R "$REPO" < "$KEY_FILE"
grep '^DEEPSEEK_API_KEY=' "$ENVF" | cut -d= -f2- | tr -d "\"' \r\n" | gh secret set DEEPSEEK_API_KEY -R "$REPO"

# 4. Dispatch this account's share (the workflow file must be visible first).
for i in 1 2 3 4 5 6; do gh workflow view matrix -R "$REPO" >/dev/null 2>&1 && break; sleep 5; done
gh workflow run matrix -R "$REPO" -f ids="$IDS" -f mode=build
sleep 8
echo "dispatched: $(gh run list -R "$REPO" -w matrix -L1 --json databaseId,status -q '.[0] | "run \(.databaseId) \(.status)"')"
unset GH_TOKEN
