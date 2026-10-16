#!/usr/bin/env python3
"""Build tests/peer/russh-peer.tar.gz: the attacker peer for the hidden tests (2026-10-16 repair).

The peer is russh at the VULNERABLE commit (unmodified negotiation), renamed to the crate
`russh-peer` so it can sit next to the agent's russh in the harness. The security tests use it
as the malicious counterparty, so a fix that hardens only one role (client or server) is graded
from the victim's side, not saved by the attacker running the fixed library too.

One test-only hook is added: `russh_peer::KEX_OVERRIDE`. While set, the peer offers and selects
only the listed key exchanges. The re-key test sets it after the initial handshake, so the peer
answers a re-key offering only the null key exchange.

    python3 build/russh-sib/make_peer.py <pristine russh checkout at 3430fd26> [--app /app] [--out PATH]

The checkout is what environment/Dockerfile fetches (git fetch --depth 1 ... 3430fd26...).
`--app` is where the agent's repository lives at grading time (its cryptovec and russh-util
crates are shared by both peers so Cargo sees one copy of each).
"""
import argparse
import io
import re
import sys
import tarfile
from pathlib import Path

WS_DEPS = {  # [workspace.dependencies] of the root Cargo.toml at 3430fd26
    "aes": '"0.9"', "async-trait": '"0.1.50"', "byteorder": '"1.4"', "bytes": '"1.7"',
    "digest": '"0.11.0"', "delegate": '"0.13"', "futures": '"0.3"', "hmac": '"0.13"',
    "log": '"0.4.11"', "rand": '{ version = "0.10", features = ["thread_rng"] }',
    "sha1": '{ version = "0.11", features = ["oid"] }', "sha2": '{ version = "0.11", features = ["oid"] }',
    "signature": '"3"', "ssh-encoding": '{ version = "0.3", features = ["bytes"] }',
    "ssh-key": '{ version = "=0.7.0-rc.11", features = ["ed25519", "p256", "p384", "p521", "encryption", "ppk", "sha1"] }',
    "thiserror": '"2.0.18"',
}

HOOK = '''
// ---- russh-peer (hidden-test attacker copy, not part of russh) ----------------
/// While set, this peer offers and selects only these key exchanges.
pub static KEX_OVERRIDE: std::sync::Mutex<Option<Vec<kex::Name>>> = std::sync::Mutex::new(None);

fn peer_pref(pref: &Preferred) -> Preferred {
    let mut p = pref.clone();
    if let Some(k) = KEX_OVERRIDE.lock().map(|g| g.clone()).unwrap_or(None) {
        p.kex = Cow::Owned(k);
    }
    p
}
// --------------------------------------------------------------------------------
'''


def manifest(src: str, app: str) -> str:
    """Standalone manifest: package renamed, workspace keys inlined, dev/bench parts dropped."""
    head, _, _ = src.partition("[dev-dependencies]")
    head = head.replace('name = "russh"', 'name = "russh-peer"', 1)
    head = re.sub(r'(?m)^readme = .*\n', '', head)
    head = head.replace('path = "../cryptovec"', f'path = "{app}/cryptovec"')
    head = head.replace('path = "../russh-util"', f'path = "{app}/russh-util"')
    head = re.sub(r'(?ms)^\[target\.\'cfg\(windows\)\'\.dependencies\]\n.*?\n\n', '', head)
    head = re.sub(r'(?m)^criterion = .*\n', '', head)
    head = re.sub(r'(?m)^_bench = .*\n', '_bench = []\n', head)

    text = re.sub(r'(?m)^([\w-]+)\.workspace = true[ \t]*$', lambda m: f"{m.group(1)} = {WS_DEPS[m.group(1)]}", head)
    text = text.replace('async-trait = { workspace = true, optional = true }',
                        'async-trait = { version = "0.1.50", optional = true }')
    text = re.sub(r'tokio = \{ workspace = true, features = \[(.*?)\] \}',
                  lambda m: f'tokio = {{ version = "1.17.0", features = [{m.group(1)}] }}', text, flags=re.S)
    if "workspace" in text:
        sys.exit("make_peer: unresolved workspace key: " + str([l for l in text.splitlines() if "workspace" in l]))
    return text.rstrip() + "\n\n[lib]\npath = \"src/lib.rs\"\n"


def patch_negotiation(src: str) -> str:
    anchor = "pub(crate) trait Select {"
    assert src.count(anchor) == 1
    src = src.replace(anchor, HOOK + "\n" + anchor, 1)
    # read_kex: use the peer's (possibly overridden) preferences.
    old = "        let &Some(mut r) = &buffer.get(17..) else {"
    assert src.count(old) == 1
    src = src.replace(old, "        let __peer_pref = peer_pref(pref);\n        let pref = &__peer_pref;\n" + old, 1)
    # write_kex: same for the offer.
    old = "    writer.packet_bytes(|w| {\n        msg::KEXINIT.encode(w)?;"
    assert src.count(old) == 1
    src = src.replace(old, "    let __peer_pref = peer_pref(prefs);\n    let prefs = &__peer_pref;\n" + old, 1)
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkout")
    ap.add_argument("--app", default="/app")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "tasks/russh-sib/tests/peer/russh-peer.tar.gz"))
    a = ap.parse_args()
    crate = Path(a.checkout) / "russh"
    files = {"Cargo.toml": manifest((crate / "Cargo.toml").read_text(), a.app)}
    for p in sorted((crate / "src").rglob("*")):
        if p.is_file():
            files[str(p.relative_to(crate))] = p.read_text()
    files["src/negotiation.rs"] = patch_negotiation(files["src/negotiation.rs"])
    lib = files["src/lib_inner.rs"]
    assert "pub use negotiation::{Names, Preferred};" in lib
    files["src/lib_inner.rs"] = lib.replace("pub use negotiation::{Names, Preferred};",
                                      "pub use negotiation::{Names, Preferred, KEX_OVERRIDE};", 1)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo("russh-peer/" + name)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
    out.write_bytes(buf.getvalue())
    print(f"wrote {out} ({len(files)} files, {out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
