"""Leaked Harbor compose networks (common/util/compose_cleanup.py, reports/gate-compose-rca-20261029.md): the network
step of hourly_cleanup.sh removes only old, unreferenced Harbor run networks outside tasks under repair, and
remove_projects() removes a trial's compose projects whole, networks included.
Run: python3 -m pytest common/util/tests/test_compose_cleanup.py"""
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "common" / "util"))
import compose_cleanup as cc  # noqa: E402

NOW = datetime(2026, 10, 29, 20, 0, 0, tzinfo=timezone.utc)
OLD = "2026-10-29 17:00:00.123456789 +0000 UTC"          # 3 h before NOW
YOUNG = "2026-10-29 19:00:00.5 +0000 UTC"               # 1 h before NOW


def row(project, created=OLD, name=None):
    return (name or f"{project}_default", created, project)


def test_harbor_projects_pairs_env_and_verifier():
    assert cc.harbor_projects("t-s2__abc1234__env") == ["t-s2__abc1234__env", "t-s2__abc1234__verifier__trial"]
    assert cc.harbor_projects("t-s2__abc1234__verifier__trial") == cc.harbor_projects("t-s2__abc1234__env")
    assert cc.harbor_projects("buildx_default") == ["buildx_default"]


def test_parse_created_reads_docker_times_with_offsets():
    assert cc.parse_created(OLD) == datetime(2026, 10, 29, 17, 0, 0, tzinfo=timezone.utc)
    assert cc.parse_created("2026-10-29 13:00:00 -0400 EDT") == datetime(2026, 10, 29, 17, 0, 0, tzinfo=timezone.utc)
    assert cc.parse_created("yesterday") is None


def test_only_old_unreferenced_harbor_run_networks_are_leaked():
    rows = [
        row("a-s2__aaaaaaa__env"),                                   # leaked env network
        row("a-s2__aaaaaaa__verifier__trial"),                       # leaked verifier network
        row("b-s2__bbbbbbb__env", YOUNG),                            # young: may be starting up
        row("c-s2__ccccccc__env"),                                   # a container (kept or running) uses it
        row("myapp"),                                                # not a Harbor run project
        row("d-s2__ddddddd__env", name="d-s2__ddddddd__env_custom"),  # not the project's default network
        ("bridge", OLD, ""),                                         # no compose label
        row("e-s2__eeeeeee__env", "garbled"),                        # age unknown: never removed
    ]
    used = {"c-s2__ccccccc__env_default", "bridge"}
    assert cc.leaked_networks(rows, used, NOW, 2) == ["a-s2__aaaaaaa__env_default",
                                                      "a-s2__aaaaaaa__verifier__trial_default"]


def test_tasks_under_repair_keep_their_networks():
    rows = [row("held-s2__aaaaaaa__env"), row("other-s2__bbbbbbb__env")]
    # the same alternation hourly_cleanup.sh builds from .hold-repair (grep -viE "$keep"); case-insensitive
    assert cc.leaked_networks(rows, set(), NOW, 2, keep="HELD-s2|zzz") == ["other-s2__bbbbbbb__env_default"]


def test_min_age_is_respected():
    rows = [row("a-s2__aaaaaaa__env", "2026-10-29 18:30:00 +0000 UTC")]   # 1.5 h old
    assert cc.leaked_networks(rows, set(), NOW, 2) == []
    assert cc.leaked_networks(rows, set(), NOW, 1) == ["a-s2__aaaaaaa__env_default"]


class FakeDocker:
    """Containers {id: (project, [networks])} and networks {name: project}; records every call."""

    def __init__(self, containers, networks, created=OLD):
        self.containers, self.networks, self.created, self.calls = dict(containers), dict(networks), created, []

    def __call__(self, args, timeout=None):
        self.calls.append(list(args))
        if args[:2] == ["ps", "-aq"]:
            proj = args[3].split("=", 2)[2]
            return "\n".join(i for i, (p, _) in self.containers.items() if p == proj)
        if args[:2] == ["ps", "-a"]:
            return "\n".join(",".join(n) for _, n in self.containers.values())
        if args[:1] == ["rm"]:
            for i in args:
                self.containers.pop(i, None)
            return "\n".join(args[3:])
        if args[:3] == ["network", "ls", "-q"]:
            proj = args[4].split("=", 2)[2]
            return "\n".join(n for n, p in self.networks.items() if p == proj)
        if args[:2] == ["network", "ls"]:
            return "\n".join(f"{n}\t{self.created}\t{p}" for n, p in self.networks.items())
        if args[:2] == ["network", "rm"]:
            gone = [n for n in args[2:] if self.networks.pop(n, None) is not None]
            return "\n".join(gone)
        raise AssertionError(f"unexpected docker call {args}")


def test_remove_projects_takes_sidecar_verifier_and_both_networks():
    d = FakeDocker(
        {"m": ("t__x__env", ["t__x__env_default"]), "s": ("t__x__env", ["t__x__env_default"]),
         "v": ("t__x__verifier__trial", ["t__x__verifier__trial_default"]),
         "o": ("u__y__env", ["u__y__env_default"])},
        {"t__x__env_default": "t__x__env", "t__x__verifier__trial_default": "t__x__verifier__trial",
         "u__y__env_default": "u__y__env"})
    assert cc.remove_projects(cc.harbor_projects("t__x__env"), docker=d) == (3, 2)
    assert set(d.containers) == {"o"} and set(d.networks) == {"u__y__env_default"}   # another trial untouched


def test_remove_leaked_counts_and_rechecks(monkeypatch):
    nets = {f"t{i}__abcdefg__env_default": f"t{i}__abcdefg__env" for i in range(150)}
    d = FakeDocker({"k": ("t3__abcdefg__env", ["t3__abcdefg__env_default"])}, nets)
    orig = d.__call__

    def docker(args, timeout=None):                 # a container appears on network t120 after the first read
        if args[:2] == ["ps", "-a"] and sum(c[:2] == ["ps", "-a"] for c in d.calls) == 1:
            d.containers["new"] = ("t120__abcdefg__env", ["t120__abcdefg__env_default"])
        return orig(args, timeout)
    slept = []
    r = cc.remove_leaked(2, None, 0.2, docker=docker, sleep=slept.append, now=NOW)
    assert r == {"candidates": 149, "removed": 148, "in_use": 1, "failed": 0, "left": 0}
    assert set(d.networks) == {"t3__abcdefg__env_default", "t120__abcdefg__env_default"}
    assert len(slept) == 148 and set(slept) == {0.2}                # serial, with a pause after each removal


def test_remove_leaked_dry_run_removes_nothing():
    d = FakeDocker({}, {"t__abcdefg__env_default": "t__abcdefg__env"})
    r = cc.remove_leaked(2, None, 0, dry_run=True, docker=d, sleep=lambda s: None, now=NOW)
    assert r["candidates"] == 1 and d.networks and not any(c[:2] == ["network", "rm"] for c in d.calls)


def test_a_refused_removal_counts_as_failed():
    d = FakeDocker({}, {"t__abcdefg__env_default": "t__abcdefg__env"})
    orig = d.__call__
    r = cc.remove_leaked(2, None, 0, docker=lambda a, t=None: "" if a[:2] == ["network", "rm"] else orig(a, t),
                         sleep=lambda s: None, now=NOW)
    assert r == {"candidates": 1, "removed": 0, "in_use": 0, "failed": 1, "left": 0}


def test_the_time_budget_leaves_the_rest_for_the_next_pass():
    d = FakeDocker({}, {f"t{i}__abcdefg__env_default": f"t{i}__abcdefg__env" for i in range(10)})
    ticks = iter(range(100))                                        # one second per clock read
    r = cc.remove_leaked(2, None, 0, docker=d, sleep=lambda s: None, now=NOW, max_sec=3.5, clock=lambda: next(ticks))
    assert r["removed"] == 3 and r["left"] == 7 and len(d.networks) == 7
