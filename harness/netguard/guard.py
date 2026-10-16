"""netguard mitmproxy addon: refuse the task's own repository on every route (client rule,
2026-10-14: trials have internet but no access to the task's own repository).

Configured by the sidecar's environment (set per task in environment/docker-compose.yaml):
    NETGUARD_BLOCK_REPOS   space-separated owner/repo   e.g. "rclone/rclone"
    NETGUARD_BLOCK_NAMES   space-separated names: the repo name plus the package names it is
                           published under, e.g. "rclone"  or  "webob WebOb"
Only GUARDED hosts (code hosts, package registries, source CDNs) are decrypted and checked; all
other TLS traffic passes through undecrypted (decided on the SNI in tls_clienthello). Every decision on a guarded host is
logged to stdout as one JSON line: {"netguard": "block"|"allow", "host": .., "path": ..}.

    python3 guard.py --ignore-regex     # prints the regex for mitmproxy's --ignore-hosts
"""
import json
import os
import re
import sys

GUARDED = [
    "github.com", "api.github.com", "raw.githubusercontent.com", "codeload.github.com",
    "objects.githubusercontent.com", "gist.github.com", "gist.githubusercontent.com",
    "gitlab.com", "bitbucket.org",
    "pypi.org", "files.pythonhosted.org", "registry.npmjs.org", "www.npmjs.com",
    "repo1.maven.org", "repo.maven.apache.org", "central.sonatype.com", "search.maven.org",
    "crates.io", "static.crates.io", "index.crates.io", "docs.rs",
    "proxy.golang.org", "pkg.go.dev", "sum.golang.org",
    "rubygems.org", "index.rubygems.org", "packagist.org", "repo.packagist.org",
    "cdn.jsdelivr.net", "unpkg.com", "sourcegraph.com", "deps.dev",
    "archive.softwareheritage.org",
]


def ignore_regex():
    alt = "|".join(re.escape(h) for h in GUARDED)
    # mitmproxy matches this against "host:port"; ignore (pass through) everything not guarded
    return rf"^(?!(?:{alt})(?::\d+)?$).*"


REPOS = [r.lower() for r in os.environ.get("NETGUARD_BLOCK_REPOS", "").split() if "/" in r]
NAMES = sorted({n.lower() for n in os.environ.get("NETGUARD_BLOCK_NAMES", "").split() if n}
               | {r.split("/", 1)[1] for r in REPOS})
_name_alt = "|".join(re.escape(n) for n in NAMES) or r"(?!x)x"
# A release file or ref of a blocked name: name, name.git, name-1.2.3..., name_1.2..., name@1.2, name==1.2
_NAME = rf"(?:{_name_alt})(?:\.git|[-_]v?\d[^/]*|[@=][^/]*)?"
# Code hosts: the REPOSITORY position only (/<any owner>/<repo>), so forks and mirrors of the task's
# repo are refused but the owner's other repositories stay reachable.
CODE_HOSTS = {"github.com", "raw.githubusercontent.com", "codeload.github.com", "gist.github.com",
              "gist.githubusercontent.com", "gitlab.com", "bitbucket.org"}
CODE_PATH = re.compile(rf"^/(?:repos/)?[^/?#]+/{_NAME}(?:/|$|\?|#)", re.I)
# Registries and source CDNs: any path segment naming the package or one of its releases.
SEGMENT = re.compile(rf"(?:^|/){_NAME}(?:/|$|\?|#)", re.I)


def blocked(host, path):
    host = host.lower().split(":")[0]
    if host not in GUARDED:
        return False
    if host == "objects.githubusercontent.com":
        return False                  # opaque blob URLs; their repo pages are refused first
    if host in CODE_HOSTS or host == "api.github.com":
        return bool(CODE_PATH.search(path))
    return bool(SEGMENT.search(path))


def guarded_host(host):
    return (host or "").lower().split(":")[0] in GUARDED


class Guard:
    def tls_clienthello(self, data):
        """Decrypt only guarded hosts. Decided on the TLS SNI: in transparent mode the
        --ignore-hosts option is matched against the destination IP before the hostname is
        known, which let guarded hosts pass through (netguard-check, 2026-10-16)."""
        sni = data.client_hello.sni
        if not guarded_host(sni):
            data.ignore_connection = True

    def request(self, flow):
        host, path = flow.request.pretty_host, flow.request.path
        if host.lower() not in GUARDED:
            return
        bad = blocked(host, path)
        print(json.dumps({"netguard": "block" if bad else "allow", "host": host,
                          "path": path[:300], "method": flow.request.method}), flush=True)
        if bad:
            from mitmproxy import http
            flow.response = http.Response.make(
                403, b"Blocked by trial policy: this task's own repository is not reachable.\n",
                {"Content-Type": "text/plain"})


addons = [Guard()]

if __name__ == "__main__" and "--ignore-regex" in sys.argv:
    print(ignore_regex())
