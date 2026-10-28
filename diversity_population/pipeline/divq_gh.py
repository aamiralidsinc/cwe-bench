"""divq GitHub executor: dispatch workflows, follow runs, download artifacts, via the `gh` CLI.

The core (divq_core.py) never imports this; it receives an executor object. The tests pass a fake. Tokens are
read from the settings' env_file by variable name and passed to `gh` through GH_TOKEN in the child environment only;
they are never written to disk, a log or the DB.
"""
import json, os, subprocess, time
from pathlib import Path


class GH:
    def __init__(self, s):
        self.s = s
        self.env_file = os.path.expanduser(s.data["paths"]["env_file"])
        self._tok = {}
        self.repo = {a["name"]: a["repo"] for a in s.accounts(enabled_only=False)}
        self.token_var = {a["name"]: a["token_var"] for a in s.accounts(enabled_only=False)}

    def _token(self, account):
        if account not in self._tok:
            var = self.token_var[account]
            val = ""
            for line in open(self.env_file):
                if line.startswith(var + "="):
                    val = line.split("=", 1)[1].strip().strip("\"'").rstrip("\r")
                    break
            if not val:
                raise RuntimeError(f"token {var} not found in {self.env_file}")
            self._tok[account] = val
        return self._tok[account]

    def _gh(self, account, *args, timeout=120, check=False):
        env = dict(os.environ, GH_TOKEN=self._token(account), GH_PROMPT_DISABLED="1")
        r = subprocess.run(["gh", *args], capture_output=True, text=True, env=env, timeout=timeout)
        if check and r.returncode:
            raise RuntimeError(f"gh {args[0]} failed ({r.returncode}): {r.stderr.strip()[:200]}")
        return r

    def login(self, account):
        """Returns the login gh resolves for the account's token, for preflight (never the token)."""
        return self._gh(account, "api", "user", "-q", ".login").stdout.strip()

    def workflow_registered(self, account, workflow):
        return self._gh(account, "workflow", "view", workflow, "-R", self.repo[account]).returncode == 0

    def secret_names(self, account):
        r = self._gh(account, "secret", "list", "-R", self.repo[account], "--json", "name", "-q", ".[].name")
        return set(r.stdout.split())

    def _run_ids(self, account, workflow):
        r = self._gh(account, "run", "list", "-R", self.repo[account], "-w", workflow, "-L", "40",
                     "--json", "databaseId", "-q", ".[].databaseId")
        return [x for x in r.stdout.split() if x]

    def dispatch(self, account, workflow, inputs):
        before = set(self._run_ids(account, workflow))
        args = ["workflow", "run", workflow, "-R", self.repo[account]]
        for k, v in inputs.items():
            args += ["-f", f"{k}={v}"]
        if self._gh(account, *args).returncode:
            return None
        for _ in range(15):
            time.sleep(4)
            new = [r for r in self._run_ids(account, workflow) if r not in before]
            if new:
                return new[0]
        return None

    def find_run(self, account, workflow, token):
        """Fallback when a dispatch did not return a run id: the newest run whose `job` input matches the token."""
        for rid in self._run_ids(account, workflow):
            r = self._gh(account, "run", "view", rid, "-R", self.repo[account], "--json", "displayTitle,jobs",
                         "-q", ".displayTitle")
            if token in r.stdout:
                return rid
        return None

    def run_status(self, account, run_id):
        r = self._gh(account, "run", "view", run_id, "-R", self.repo[account],
                     "--json", "status,conclusion,jobs")
        try:
            d = json.loads(r.stdout)
        except json.JSONDecodeError:
            return ("unknown", "", None)
        started = None
        for j in d.get("jobs", []):
            if j.get("startedAt"):
                started = j["startedAt"].replace(".000Z", "Z")
                break
        return (d.get("status") or "unknown", d.get("conclusion") or "", started)

    def download_artifact(self, account, run_id, name, dest):
        r = self._gh(account, "run", "download", run_id, "-R", self.repo[account], "-n", name, "-D", dest,
                     timeout=1200)
        if r.returncode:
            return None
        hits = list(Path(dest).rglob("*.tgz.gpg"))
        return str(hits[0]) if hits else None
