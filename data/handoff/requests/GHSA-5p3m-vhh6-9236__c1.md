<!-- label=GHSA-5p3m-vhh6-9236 call=1 hash=d7023a9ef1 -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-5p3m-vhh6-9236
- CVE: CVE-2026-76239
- CWE: CWE-20, CWE-918
- Ecosystem / Package: PyPI / stigmem-node
- Repository: https://github.com/eidetic-labs/stigmem
- Official Summary: stigmem-node has blind SSRF via unvalidated webhook subscription delivery_address

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/node/src/stigmem_node/auth.py b/node/src/stigmem_node/auth.py
index d651a9af3ec14b6b59731e8730778c38a2bd38d7..0d05fe92f11250bece7e58e9054866d3e53146b6 100644
--- a/node/src/stigmem_node/auth.py
+++ b/node/src/stigmem_node/auth.py
@@ -322,6 +322,22 @@ def resolve_identity(
     return _apply_identity_hooks(identity, raw_credentials=creds.credentials)
 
 
+def resolve_identity_optional(
+    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(BEARER)],
+) -> Identity | None:
+    """Dependency: resolve identity from Bearer token without the auth_required gate.
+
+    Returns None when no credential is supplied or the credential is invalid/expired.
+    Used by routes that handle auth themselves (e.g. /metrics with metrics_require_auth).
+    """
+    if creds is None:
+        return None
+    identity = _lookup(creds.credentials)
+    if identity is None:
+        return None
+    return _apply_identity_hooks(identity, raw_credentials=creds.credentials)
+
+
 def _apply_identity_hooks(identity: Identity, raw_credentials: str | None) -> Identity:
     registry = get_registry()
     resolved = registry.fire_filter_chain(
diff --git a/node/src/stigmem_node/main.py b/node/src/stigmem_node/main.py
index ebd57cefe24af121190db2530a8f51153aa583cf..7d926e592bff4184e44da36f10c03d2947fa36be 100644
--- a/node/src/stigmem_node/main.py
+++ b/node/src/stigmem_node/main.py
@@ -12,11 +12,11 @@ from pathlib import Path
 from typing import Annotated, Any, cast
 
 import uvicorn
-from fastapi import Depends, FastAPI, Request, Response
+from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
 from fastapi.middleware.cors import CORSMiddleware
 from fastapi.responses import FileResponse, JSONResponse
 
-from .auth import Identity, resolve_identity
+from .auth import Identity, resolve_identity, resolve_identity_optional
 from .body_limit import BodySizeLimitMiddleware
 from .db import apply_migrations
 from .net_util import node_url_is_loopback
@@ -359,7 +359,26 @@ def create_app() -> FastAPI:
         }
 
     @app.get("/metrics", include_in_schema=False, tags=["ops"])
-    def prometheus_metrics() -> Response:
+    def prometheus_metrics(
+        identity: Annotated[Identity | None, Depends(resolve_identity_optional)],
+    ) -> Response:
+        # M11 / F-AVAIL-1: /metrics leaks per-principal labels + enables cardinality
+        # DoS, so require the admin capability by default.  Set
+        # STIGMEM_METRICS_REQUIRE_AUTH=false only where /metrics is otherwise
+        # access-controlled (e.g. a private scrape interface or sidecar proxy).
+        if settings.metrics_require_auth:
+            if identity is None:
+                raise HTTPException(
+                    status_code=status.HTTP_401_UNAUTHORIZED,
+                    detail="Authorization required to scrape /metrics",
+                    headers={"WWW-Authenticate": "Bearer"},
+                )
+            if not identity.is_admin():
+                raise HTTPException(
+                    status_code=status.HTTP_403_FORBIDDEN,
+                    detail="admin capability required to scrape /metrics",
+                )
+
         from .observability.metrics import make_metrics_response
 
         resp = make_metrics_response()
diff --git a/node/src/stigmem_node/net_util.py b/node/src/stigmem_node/net_util.py
index 14da08e93d9fbeb4e2b038387a4770a2c3c2bbab..627c27d2e5bf01797c160e973b059a2e6495e4ea 100644
--- a/node/src/stigmem_node/net_util.py
+++ b/node/src/stigmem_node/net_util.py
@@ -5,10 +5,14 @@ from __future__ import annotations
 import sys
 from typing import TYPE_CHECKING
 
-__all__ = ["assert_safe_url", "node_url_is_loopback"]
+__all__ = ["assert_safe_url", "node_url_is_loopback", "resolve_pinned_address"]
 
 if TYPE_CHECKING:
-    from .utility.net_util import assert_safe_url, node_url_is_loopback
+    from .utility.net_util import (
+        assert_safe_url,
+        node_url_is_loopback,
+        resolve_pinned_address,
+    )
 else:
     from .utility import net_util as _impl
 
diff --git a/node/src/stigmem_node/routes/subscriptions.py b/node/src/stigmem_node/routes/subscriptions.py
index 3cf284488ec5a05794c09b9cc8cc372943b04d44..fad33d18473ae8f0d31444e4730ec4090609b974 100644
--- a/node/src/stigmem_node/routes/subscriptions.py
+++ b/node/src/stigmem_node/routes/subscriptions.py
@@ -28,6 +28,7 @@ from ..models.subscriptions import (
     SubscriptionListResponse,
     SubscriptionRecord,
 )
+from ..net_util import assert_safe_url
 from ..subscription_delivery import _sanitize_payload as _sanitize_event_payload
 
 router = APIRouter(prefix="/v1/subscriptions", tags=["subscriptions"])
@@ -110,6 +111,23 @@ def create_subscription(
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="garden not found")
         require_garden_read(garden, identity)
 
+    # GHSA-5p3m-vhh6-9236: validate a webhook delivery_address BEFORE persisting,
+    # so an unsafe URL is rejected (400) rather than stored-then-blocked-at-delivery.
+    # https-only by default; http requires the explicit operator opt-in. A `wake`
+    # subscription's delivery_address is an identity URI (not a fetchable URL), so
+    # it is deliberately NOT subjected to the SSRF guard.
+    if req.on_change == "webhook":
+        try:
+            assert_safe_url(
+                req.delivery_address,
+                allow_schemes=_settings_pkg.settings.webhook_allowed_schemes,
+            )
+        except ValueError as exc:
+            raise HTTPException(
+                status_code=status.HTTP_400_BAD_REQUEST,
+                detail=f"unsafe webhook delivery_address: {exc}",
+            ) from exc
+
     # Idempotency key: return existing subscription if key matches THIS caller.
     # Scoped to subscriber and tenant to prevent cross-entity metadata leakage (R2).
     if req.idempotency_key:
diff --git a/node/src/stigmem_node/settings.py b/node/src/stigmem_node/settings.py
index 3b002cc8225b6a513209f724a5c90eb757c61f42..bfeeba2ef626aad92f956dcd99ac2bce8f61adac 100644
--- a/node/src/stigmem_node/settings.py
+++ b/node/src/stigmem_node/settings.py
@@ -31,6 +31,11 @@ class Settings(BaseSettings):
     # When True (default), every request must carry a valid Bearer token.
     # Set to False only for local development / single-operator installs.
     auth_required: bool = True
+    # /metrics (Prometheus) leaks per-principal entity_uri/tenant/peer labels and
+    # enables unbounded-cardinality DoS, so it requires the admin capability by
+    # default (M11 / F-AVAIL-1).  Set False only where /metrics is otherwise
+    # access-controlled, e.g. behind a private scrape interface or a sidecar proxy.
+    metrics_require_auth: bool = True
     # Static API-key lifecycle controls. 0 disables max-age enforcement.
     api_key_max_age_days: int = 90
     api_key_expiring_soon_days: int = 30
@@ -323,6 +328,25 @@ class Settings(BaseSettings):
     # F-AVAIL-3: cap on active subscriptions per (subscriber_identity, tenant).
     # 0 disables the cap. Default is generous; raise for high-fan-out operators.
     max_subscriptions_per_principal: int = 1000
+    # M12 / F-AVAIL-2: terminal (delivered/failed) subscription_events older than
+    # this are pruned by the delivery sweep so the table cannot grow unbounded.
+    # Clamped to >= subscription_replay_s at prune time so the replay window is
+    # never truncated.  0 disables pruning entirely.
+    subscription_event_retention_s: int = 604800  # 7 days
+    # GHSA-5p3m-vhh6-9236: webhook delivery_address must be https by default.
+    # When False (default), a webhook delivery_address is required to be https at
+    # both creation and delivery time. Set True ONLY for local/dev where http
+    # webhooks are needed — this is the advisory's explicit, operator-controlled
+    # opt-in for the insecure http scheme. https-only blocks plaintext exfil and
+    # narrows the SSRF surface.
+    webhook_allow_insecure_http: bool = False
+
+    @property
+    def webhook_allowed_schemes(self) -> frozenset[str]:
+        """Allowed schemes for webhook delivery_address (https-only by default)."""
+        if self.webhook_allow_insecure_http:
+            return frozenset({"https", "http"})
+        return frozenset({"https"})
 
     # -------------------------------------------------------------------------
     # mTLS Federation Transport — Phase 12 (spec §22.1)
diff --git a/node/src/stigmem_node/subscription_delivery.py b/node/src/stigmem_node/subscription_delivery.py
index e8365746c6c245f6e4eedec13a9b6c124c66a144..27be48f4af9afbb6ae9a9cdf5c3d818a861337fc 100644
--- a/node/src/stigmem_node/subscription_delivery.py
+++ b/node/src/stigmem_node/subscription_delivery.py
@@ -24,6 +24,7 @@ import time
 import uuid
 from datetime import UTC, datetime
 from typing import Any
+from urllib.parse import urlsplit, urlunsplit
 
 import httpx
 
@@ -33,7 +34,7 @@ from .db import db
 from .garden_acl import get_member_role
 from .lifecycle.tombstone_cache import is_tombstoned as _is_tombstoned
 from .memory_garden_acl_gate import garden_acl_enforced
-from .net_util import assert_safe_url
+from .net_util import resolve_pinned_address
 from .recall.recall_pipeline import apply_recall_pipeline
 
 logger = logging.getLogger("stigmem.subscriptions")
@@ -118,6 +119,27 @@ def deliver_pending() -> None:
         ).isoformat()
 
         with db() as conn:
+            # 0. Prune terminal events older than the retention window (M12 / F-AVAIL-2).
+            #    Only delivered/failed rows are touched — pending/delivering are never pruned.
+            #    The horizon is clamped to >= subscription_replay_s so the replay API
+            #    never loses events it is supposed to surface.
+            retention_s = _settings_pkg.settings.subscription_event_retention_s
+            if retention_s > 0:
+                effective_retention_s = max(
+                    retention_s,
+                    _settings_pkg.settings.subscription_replay_s,
+                )
+                prune_cutoff = datetime.fromtimestamp(
+                    time.time() - effective_retention_s,
+                    UTC,
+                ).isoformat()
+                conn.execute(
+                    """DELETE FROM subscription_events
+                         WHERE delivery_status IN ('delivered', 'failed')
+                           AND created_at < ?""",
+                    (prune_cutoff,),
+                )
+
             # 1. Recover stale claims left behind by a crashed worker.  We do NOT
             #    reset delivery_attempts — the next attempt counts as a retry.
             conn.execute(
@@ -276,6 +298,34 @@ def _sanitize_payload(event: Any, payload: dict[str, Any]) -> dict[str, Any] | N
         return payload
 
 
+def _build_pinned_request(address: str, pinned_ip: str) -> tuple[str, str]:
+    """Return ``(pinned_url, host_header)`` for connecting to *pinned_ip*.
+
+    The returned URL swaps the original hostname for the validated *pinned_ip*
+    literal (IPv6 bracketed) while preserving scheme/port/path/query, so the
+    socket connects to the pinned IP and cannot be re-resolved by a rebinder.
+    The ``host_header`` carries the ORIGINAL hostname (+ explicit port) so the
+    webhook receiver still sees the name it was registered under.
+
+    The caller also passes ``extensions={"sni_hostname": <hostname>}`` so the TLS
+    SNI and certificate verification run against the original hostname, NOT the
+    IP literal (proven against httpx 0.28.1 in test_webhook_dns_rebind.py).
+    """
+    parts = urlsplit(address)
+    hostname = parts.hostname or ""
+    port = parts.port
+    # Bracket IPv6 literals for a valid authority.
+    ip_authority = f"[{pinned_ip}]" if ":" in pinned_ip else pinned_ip
+    if port is not None:
+        netloc = f"{ip_authority}:{port}"
+        host_header = f"{hostname}:{port}"
+    else:
+        netloc = ip_authority
+        host_header = hostname
+    pinned_url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
+    return pinned_url, host_header
+
+
 def _deliver_webhook(event: Any, payload: dict[str, Any]) -> bool:
     sanitized = _sanitize_payload(event, payload)
     if sanitized is None:
@@ -283,10 +333,21 @@ def _deliver_webhook(event: Any, payload: dict[str, Any]) -> bool:
         _mark_delivered(event["id"], event["subscription_id"])
         return True
 
-    # SSRF guard (P-CONF-2): never POST to a private/loopback/link-local/IMDS
-    # address. Unsafe addresses can never become deliverable, so stop retrying.
+    # SSRF guard (P-CONF-2 + H9/F-SSRF-1): never POST to a private/loopback/
+    # link-local/IMDS address. Resolve the hostname ONCE and PIN the connection to
+    # that validated IP — assert_safe_url's resolved-then-reconnect pattern left a
+    # DNS-rebind TOCTOU window (httpx re-resolved the hostname at connect time).
+    # resolve_pinned_address rejects the whole URL if ANY resolved record is
+    # private (the rebinder picks which record is served) and returns one safe IP.
+    # Unsafe/unresolvable addresses can never become deliverable, so stop retrying.
+    # GHSA-5p3m-vhh6-9236: https-only by default; http requires the explicit
+    # operator opt-in (STIGMEM_WEBHOOK_ALLOW_INSECURE_HTTP).
+    address = event["delivery_address"]
     try:
-        assert_safe_url(event["delivery_address"], allow_schemes=frozenset({"https", "http"}))
+        pinned_ip = resolve_pinned_address(
+            address,
+            allow_schemes=_settings_pkg.settings.webhook_allowed_schemes,
+        )
     except ValueError as exc:
         logger.warning(
             "Webhook delivery blocked for subscription %s: unsafe delivery_address (%s)",
@@ -296,6 +357,14 @@ def _deliver_webhook(event: Any, payload: dict[str, Any]) -> bool:
         _mark_delivered(event["id"], event["subscription_id"])
         return True
 
+    # Connect to the pinned IP literal (no re-resolution) while verifying the TLS
+    # cert against the ORIGINAL hostname via the sni_hostname extension, and carry
+    # the original Host header. Proven against httpx 0.28.1 in
+    # tests/routes/test_webhook_dns_rebind.py (a real TLS handshake verifies the
+    # cert against the hostname, not the IP).
+    pinned_url, host_header = _build_pinned_request(address, pinned_ip)
+    hostname = urlsplit(address).hostname or ""
+
     body = {
         "event_id": event["id"],
         "idempotency_key": event["id"],
@@ -307,12 +376,14 @@ def _deliver_webhook(event: Any, payload: dict[str, Any]) -> bool:
     try:
         with httpx.Client(timeout=10.0, follow_redirects=False) as client:
             resp = client.post(
-                event["delivery_address"],
+                pinned_url,
                 json=body,
                 headers={
                     "Content-Type": "application/json",
                     "X-Stigmem-Event-Id": event["id"],
+                    "Host": host_header,
                 },
+                extensions={"sni_hostname": hostname},
             )
 
         if resp.status_code == 410:
diff --git a/node/src/stigmem_node/utility/net_util.py b/node/src/stigmem_node/utility/net_util.py
index 7ec12bac3a7024a13fba78703735d430b4146a8d..142baaa843f38ea6446cd77aca7ace042d8cc061 100644
--- a/node/src/stigmem_node/utility/net_util.py
+++ b/node/src/stigmem_node/utility/net_util.py
@@ -21,6 +21,11 @@ _BLOCKED_NETS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
 )
 
 
+def _ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
+    """Return True iff *ip* falls in a private/loopback/link-local/IMDS range."""
+    return any(ip in net for net in _BLOCKED_NETS)
+
+
 def node_url_is_loopback(node_url: str) -> bool:
     """Return True iff *node_url*'s host is a literal loopback host.
 
@@ -63,6 +68,56 @@ def assert_safe_url(
         raise ValueError(f"Cannot resolve hostname {hostname!r}: {exc}") from exc
     for info in infos:
         ip = ipaddress.ip_address(info[4][0])
-        for net in _BLOCKED_NETS:
-            if ip in net:
-                raise ValueError(f"Blocked private/loopback address for {hostname!r}: {ip}")
+        if _ip_is_blocked(ip):
+            raise ValueError(f"Blocked private/loopback address for {hostname!r}: {ip}")
+
+
+def resolve_pinned_address(
+    url: str,
+    *,
+    allow_schemes: frozenset[str] = frozenset({"https"}),
+) -> str:
+    """Resolve *url*'s hostname ONCE and return a single safe pinned IP literal.
+
+    Closes the DNS-rebinding TOCTOU (H9 / F-SSRF-1): ``assert_safe_url`` validates
+    the resolved addresses but then hands the *hostname* to the HTTP client, which
+    re-resolves at connect time — a TTL-0 rebind attacker can serve a public IP at
+    validation and a private/loopback/IMDS IP at connect.  Callers must instead
+    connect to the *exact* IP this returns (preserving Host header + TLS SNI +
+    cert verification against the original hostname).
+
+    Semantics:
+    - scheme must be in *allow_schemes* (https-only by default)
+    - hostname must resolve (DNS failure → ValueError)
+    - if ANY resolved A/AAAA record is private/loopback/link-local/IMDS, the WHOLE
+      url is rejected (ValueError).  A rebinder controls which record is served, so
+      we never cherry-pick a public record out of a mixed set.
+    - returns the first resolved IP (a bare literal, e.g. ``"203.0.113.7"`` or
+      ``"2001:db8::1"`` — caller is responsible for bracketing IPv6 in a URL).
+
+    All failure modes raise ValueError so the caller can fail closed.
+    """
+    parsed = urlparse(url)
+    if parsed.scheme not in allow_schemes:
+        raise ValueError(f"Disallowed URL scheme: {parsed.scheme!r}")
+    hostname = parsed.hostname or ""
+    if not hostname:
+        raise ValueError(f"URL has no hostname: {url!r}")
+    try:
+        infos = socket.getaddrinfo(hostname, None)
+    except socket.gaierror as exc:
+        raise ValueError(f"Cannot resolve hostname {hostname!r}: {exc}") from exc
+
+    pinned: str | None = None
+    for info in infos:
+        addr = str(info[4][0])
+        ip = ipaddress.ip_address(addr)
+        if _ip_is_blocked(ip):
+            # Reject the whole URL — the rebinder chooses which record is served.
+            raise ValueError(f"Blocked private/loopback address for {hostname!r}: {ip}")
+        if pinned is None:
+            pinned = addr
+
+    if pinned is None:
+        raise ValueError(f"Hostname {hostname!r} resolved to no addresses")
+    return pinned

# (9 test/doc file(s) of the upstream fix omitted here)

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### node/src/stigmem_node/auth.py
```
"""API-key authentication for the Stigmem reference node.

Auth model (spec §3.5):
  - Callers present `Authorization: Bearer <raw-key>` on every request.
  - Raw keys are never stored; only an Argon2id hash is persisted.
  - Legacy SHA-256 hex digests are accepted during the v0.9.x migration
    window and are opportunistically rehashed to Argon2id on successful use.
  - Each key maps to an entity_uri and a JSON-array of permissions:
    ["read"], ["read","write"], or ["read","write","federate"].
  - `STIGMEM_AUTH_REQUIRED` defaults to **True** — every request must
    present a valid Bearer token. Set `STIGMEM_AUTH_REQUIRED=false` to
    opt into anonymous-mode for single-operator development; this is
    NOT appropriate for any deployment that accepts requests from
    agents you don't fully control. See LIMITATIONS.md §"LLM agents
    holding admin-scope API keys" for context.

Bootstrapping the first key (single-operator install):
  $ KEY=$(openssl rand -hex 32)
  $ stigmem auth bootstrap-key --key "$KEY"
  # then use $KEY as `Authorization: Bearer $KEY` for subsequent requests.

  The system NEVER generates the key — the caller provides the value and
  retains full custody. We hash and store it. This is by design:
  removing the system as the credential-generation surface eliminates
  the "reveal channel" risk entirely. The command refuses to run when
  api_keys is non-empty (bootstrap is one-shot); after bootstrap,
  additional keys go through `POST /v1/auth/keys`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from argon2.low_level import Type
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import db
from .multi_tenant_gate import warn_if_tenant_not_isolatable
from .plugins import Deny, TenantContext, get_registry
from .settings import settings as settings
from .tenant import DEFAULT_TENANT_ID, TenantIdError, validate_tenant_id

_ARGON2_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19_456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)
_LEGACY_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _hash_key(raw: str) -> str:
    """Return the persisted hash format for newly issued API keys."""
    return _ARGON2_HASHER.hash(raw)


def _legacy_sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _is_legacy_sha256_hash(stored_hash: str) -> bool:
    return bool(_LEGACY_SHA256_HEX.fullmatch(stored_hash))


def _legacy_sha256_allowed() -> bool:
    deadline = settings.legacy_sha256_accept_until
    if deadline is None:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return datetime.now(UTC) <= deadline.astimezone(UTC)


def _raise_legacy_sha256_disabled() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Legacy API key hashes are no longer accepted; rotate the key.",
    )


def _verify_key_hash(raw_key: str, stored_hash: str) -> bool:
    """Verify *raw_key* against either current Argon2id or legacy SHA-256."""
    if stored_hash.startswith("$argon2id$"):
        try:
            return _ARGON2_HASHER.verify(stored_hash, raw_key)
        except VerifyMismatchError:
            return False
        except VerificationError:
            return False
        except InvalidHash:
            return False
    if _is_legacy_sha256_hash(stored_hash):
        if not _legacy_sha256_allowed():
            _raise_legacy_sha256_disabled()
        return hmac.compare_digest(stored_hash, _legacy_sha256(raw_key))
    return False


def _row_expired(row: Any, now: str) -> bool:
    expires_at = row["expires_at"]
    return bool(expires_at and expires_at < now)


def _parse_api_key_expiry(expires_at: str) -> datetime:
    normalized = expires_at.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalize_api_key_expiry(
    expires_at: str | None,
    *,
    created_at: datetime,
) -> str | None:
    """Apply static API-key max-age policy and return the persisted expiry."""
    max_age_days = settings.api_key_max_age_days
    if max_age_days <= 0:
        return expires_at

    max_expires_at = created_at + timedelta(days=max_age_days)
    if expires_at is None:
        return max_expires_at.isoformat()

    requested_expires_at = _parse_api_key_expiry(expires_at)
    if requested_expires_at > max_expires_at:
        raise ValueError(
            "expires_at exceeds configured static API key max age "
            f"({max_age_days} days)"
        )
    return requested_expires_at.isoformat()


def _rehash_legacy_key(conn: Any, row: Any, raw_key: str) -> None:
    """Rewrite one verified legacy SHA-256 key row to Argon2id and audit it."""
    new_hash = _hash_key(raw_key)
    conn.execute(
        "UPDATE api_keys SET key_hash = ? WHERE id = ? AND key_hash = ?",
        (new_hash, row["id"], row["key_hash"]),
    )

    from .observability.audit_event import emit

    emit(
        "api_key_rehashed",
        entity_uri=row["entity_uri"],
        tenant_id=row["tenant_id"] or "default",
        oidc_sub=row["oidc_sub"],
        source="system:auth",
        detail={
            "key_id": row["id"],
            "from": "sha256",
            "to": "argon2id",
        },
        conn=conn,
    )


def _select_key_rows(conn: Any) -> list[Any]:
    return list(
        conn.execute(
            "SELECT id, key_hash, entity_uri, permissions, expires_at, oidc_sub, tenant_id"
            " FROM api_keys"
        ).fetchall()
    )


def _find_key_row(
    raw_key: str,
    *,
    include_expired: bool = False,
    rehash_legacy: bool = False,
) -> Any | None:
    now = datetime.now(UTC).isoformat()
    with db() as conn:
        legacy_row = conn.execute(
            "SELECT id, key_hash, entity_uri, permissions, expires_at, oidc_sub, tenant_id"
            " FROM api_keys WHERE key_hash = ?",
            (_legacy_sha256(raw_key),),
        ).fetchone()
        if legacy_row is not None and (include_expired or not _row_expired(legacy_row, now)):
            if not _legacy_sha256_allowed():
                _raise_legacy_sha256_disabled()
            if rehash_legacy:
                _rehash_legacy_key(conn, legacy_row, raw_key)
                legacy_row = conn.execute(
                    "SELECT id, key_hash, entity_uri, permissions, expires_at, oidc_sub, tenant_id"
                    " FROM api_keys WHERE id = ?",
                    (legacy_row["id"],),
                ).fetchone()
            return legacy_row

        for row in _select_key_rows(conn):
            if not include_expired and _row_expired(row, now):
                continue
            if _verify_key_hash(raw_key, row["key_hash"]):
                if rehash_legacy and _is_legacy_sha256_hash(row["key_hash"]):
                    _rehash_legacy_key(conn, row, raw_key)
                    row = conn.execute(
                        "SELECT id, key_hash, entity_uri, permissions, expires_at, oidc_sub,"
                        " tenant_id FROM api_keys WHERE id = ?",
                        (row["id"],),
                    ).fetchone()
                return row
    return None


def find_api_key_id_by_raw_key(raw_key: str) -> str | None:
    """Return the stored key id for *raw_key*, including expired rows."""
    row = _find_key_row(raw_key, include_expired=True, rehash_legacy=False)
    return row["id"] if row is not None else None


def lookup_principal(raw_key: str) -> tuple[str, str, str | None] | None:
    """Return (entity_uri, tenant_id, oidc_sub) for a non-expired raw key."""
    row = _find_key_row(raw_key, include_expired=False, rehash_legacy=False)
    if row is None:
        return None
    return (row["entity_uri"], row["tenant_id"] or "default", row["oidc_sub"])


BEARER = HTTPBearer(auto_error=False)


class Identity:
    """Resolved caller identity (spec §3.5)."""

    def __init__(
        self,
        entity_uri: str,
        permissions: list[str],
        oidc_sub: str | None = None,
        tenant_id: str = "default",
    ) -> None:
        self.entity_uri = entity_uri
        self.permissions = set(permissions)
        self.oidc_sub = oidc_sub
        self.tenant_id = tenant_id

    def can_read(self) -> bool:
        return self._has_capability("read")

    def can_write(self) -> bool:
        return self._has_capability("write")

    def can_write_instruction(self) -> bool:
        return self._has_capability("instruction:write")

    def can_federate(self) -> bool:
        return self._has_capability("federate")

    def can_admin_federation(self) -> bool:
        return self._has_capability("admin:federation")

    def can_audit(self) -> bool:
        """True when the principal holds the audit.read capability (spec §22.3)."""
        return self._has_capability("audit.read")

    def is_admin(self) -> bool:
        """True when the principal holds the admin capability (spec §24.3.2)."""
        return self._has_capability("admin")

    def _has_capability(self, capability: str) -> bool:
        if capability not in self.permissions:
            return False
        decision = get_registry().fire_voting(
            "capability_check",
            identity=self,
            capability=capability,
            tenant=TenantContext(
                tenant_id=self.tenant_id,
                metadata={"tenant_context_source": "hook"},
            ),
        )
        return not isinstance(decision, Deny)


_ANON = Identity("anon:trusted", ["read", "write", "federate"], tenant_id="default")


def resolve_identity(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(BEARER)],
) -> Identity:
    """Dependency: resolve caller identity from Bearer token.

    If auth is disabled, returns a fully-trusted anonymous identity.
    If auth is enabled, the token must match a non-expired api_keys row.
    """
    if not settings.auth_required:
        if creds is not None:
            # Still try to resolve a real identity even in non-required mode
            identity = _lookup(creds.credentials)
            if identity:
                return _apply_identity_hooks(identity, raw_credentials=creds.credentials)
        return _apply_identity_hooks(_ANON, raw_credentials=None)

    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    identity = _lookup(creds.credentials)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _apply_identity_hooks(identity, raw_credentials=creds.credentials)


def _apply_identity_hooks(identity: Identity, raw_credentials: str | None) -> Identity:
    registry = get_registry()
    resolved = registry.fire_filter_chain(
        "identity_resolve",
        identity,
        raw_credentials=raw_credentials,
    )
    tenant = registry.fire_filter_chain(
        "tenant_resolve",
        TenantContext(
            tenant_id=DEFAULT_TENANT_ID,
            metadata={
                "source_tenant_id": resolved.tenant_id,
                "tenant_context_source": "hook",
            },
        ),
        identity=resolved,
    )
    try:
        resolved_tenant_id = validate_tenant_id(tenant.tenant_id)
    except TenantIdError:
        resolved_tenant_id = DEFAULT_TENANT_ID
    if resolved_tenant_id != resolved.tenant_id:
        return Identity(
            entity_uri=resolved.entity_uri,
            permissions=sorted(resolved.permissions),
            oidc_sub=resolved.oidc_sub,
            tenant_id=resolved_tenant_id,
        )
    return resolved


def _lookup(raw_key: str) -> Identity | None:
    row = _find_key_row(raw_key, include_expired=False, rehash_legacy=True)
    if row is None:
        return None
    perms: list[str] = json.loads(row["permissions"])
    return Identity(
        entity_uri=row["entity_uri"],
        permissions=perms,
        oidc_sub=row["oidc_sub"],
        tenant_id=row["tenant_id"] or "default",
    )


def register_api_key(
    raw_key: str,
    entity_uri: str,
    permissions: list[str] | None = None,
    description: str | None = None,
    expires_at: str | None = None,
    oidc_sub: str | None = None,
    tenant_id: str = "default",
) -> str:
    """Persist the hash of a caller-provided raw API key. Returns the key_id.

    The caller is responsible for generating `raw_key` (e.g., from
    `secrets.token_hex(32)` or `openssl rand -hex 32`) and for storing it
    securely. This function never touches the key after hashing.
    """
    if permissions is None:
        permissions = ["read", "write"]
    if find_api_key_id_by_raw_key(raw_key) is not None:
        raise ValueError("raw API key already exists")
    normalized_tenant_id = validate_tenant_id(tenant_id)
    # F-ID-1: a non-default tenant collapses to the default tenant without the
    # multi-tenant plugin — warn loudly rather than silently mislead the operator.
    warn_if_tenant_not_isolatable(normalized_tenant_id)
    key_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).replace(microsecond=0)
    normalized_expires_at = _normalize_api_key_expiry(
        expires_at,
        created_at=created_at,
    )
    with db() as conn:
        conn.execute(
            """INSERT INTO api_keys
               (id, key_hash, entity_uri, permissions, description,
                created_at, expires_at, oidc_sub, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                key_id,
                _hash_key(raw_key),
                entity_uri,
                json.dumps(permissions),
                description,
                created_at.isoformat(),
                normalized_expires_at,
                oidc_sub,
                normalized_tenant_id,
            ),
        )
    return key_id


def create_api_key(
    entity_uri: str,
    permissions: list[str] | None = None,
    description: str | None = None,
    expires_at: str | None = None,
    oidc_sub: str | None = None,
    tenant_id: str = "default",
) -> str:
    """Mint a new raw API key, persist its hash, and return the raw key.

    Internal/test-only convenience over `register_api_key`. Adopter-facing
    flows should require the caller to provide the key material (see
    `stigmem auth bootstrap-key`) so the system is never the credential
    generation surface.
    """
    raw = str(uuid.uuid4()).replace("-", "")  # 32-char hex
    register_api_key(
        raw_key=raw,
        entity_uri=entity_uri,
        permissions=permissions,
        description=description,
        expires_at=expires_at,
        oidc_sub=oidc_sub,
        tenant_id=tenant_id,
    )
    return raw

```

### node/src/stigmem_node/main.py
```
"""Stigmem reference node — FastAPI application factory and entrypoint."""

from __future__ import annotations

import asyncio
import logging
import signal
import ssl
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated, Any, cast

import uvicorn
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .auth import Identity, resolve_identity
from .body_limit import BodySizeLimitMiddleware
from .db import apply_migrations
from .net_util import node_url_is_loopback
from .rate_limit import RateLimitMiddleware
from .routes.admin_audit import router as admin_audit_router
from .routes.agent_keys import router as agent_keys_router
from .routes.aliases import router as aliases_router
from .routes.audit import router as audit_router
from .routes.auth import router as auth_router
from .routes.cards import router as cards_router
from .routes.cid_admin import router as cid_admin_router
from .routes.decay import router as decay_router
from .routes.facts import router as facts_router
from .routes.federation import router as federation_router
from .routes.gardens import router as gardens_router
from .routes.graph import router as graph_router
from .routes.identity import router as identity_router
from .routes.intents import router as intents_router
from .routes.lint import router as lint_router
from .routes.mcp import router as mcp_router
from .routes.quarantine import router as quarantine_router
from .routes.recall import router as recall_router
from .routes.resolver import router as resolver_router
from .routes.subscriptions import router as subscriptions_router
from .routes.synthesize import router as synthesize_router
from .routes.tombstones import router as tombstones_router
from .routes.wellknown import router as wellknown_router
from .settings import settings

_STATIC_DIR = Path(__file__).parent / "static"

logger = logging.getLogger("stigmem")

_DEV_LOCALHOST_CORS_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def _enforce_federation_transport_security() -> None:
    """Require explicit opt-in for federation without mTLS."""
    federation_active = settings.federation_enabled or settings.federation_push_enabled
    if not federation_active or settings.mtls_enabled:
        return

    if not settings.federation_insecure:
        raise RuntimeError(
            "Federation requires mTLS by default. Configure STIGMEM_TLS_CERT_PATH, "
            "STIGMEM_TLS_KEY_PATH, and STIGMEM_TLS_CA_BUNDLE, or set "
            "STIGMEM_FEDERATION_INSECURE=1 only for local/dev/test federation."
        )

    if not _node_url_is_loopback(settings.node_url) and not (
        settings.local_dev_allow_insecure_non_loopback
    ):
        raise RuntimeError(
            "STIGMEM_FEDERATION_INSECURE=1 is only permitted when node_url is "
            f"bound to 127.0.0.1 or localhost. Got node_url={settings.node_url!r}. "
            "Configure mTLS for any non-loopback deployment, or set "
            "STIGMEM_LOCAL_DEV_ALLOW_INSECURE_NON_LOOPBACK=1 only for local "
            "Docker/dev networks."
        )

    logger.warning(
        "SECURITY WARNING: federation is running without mTLS because "
        "STIGMEM_FEDERATION_INSECURE=1 is set. This is only allowed because "
        "node_url is a loopback address or "
        "STIGMEM_LOCAL_DEV_ALLOW_INSECURE_NON_LOOPBACK=1 is set. Use this only "
        "for local/dev/test."
    )


def _enforce_auth_required_in_production() -> None:
    """Refuse to run unauthenticated outside loopback."""
    if settings.auth_required:
        return
    if not _node_url_is_loopback(settings.node_url) and not (
        settings.local_dev_allow_insecure_non_loopback
    ):
        raise RuntimeError(
            "STIGMEM_AUTH_REQUIRED=false is only permitted when node_url is "
            f"bound to 127.0.0.1 or localhost. Got node_url={settings.node_url!r}. "
            "Anonymous identity has read/write/federate permissions; never expose "
            "this configuration to a network. Set "
            "STIGMEM_LOCAL_DEV_ALLOW_INSECURE_NON_LOOPBACK=1 only for local "
            "Docker/dev networks."
        )
    logger.warning(
        "SECURITY WARNING: STIGMEM_AUTH_REQUIRED=false. Anonymous identity has "
        "full read/write/federate permissions. This is only allowed because "
        "node_url is a loopback address or "
        "STIGMEM_LOCAL_DEV_ALLOW_INSECURE_NON_LOOPBACK=1 is set."
    )


def _enforce_rate_limit_kill_switch_ack() -> None:
    """Refuse boot when quota is fully disabled without an explicit acknowledgement."""
    if settings.rate_limit_write_per_hour != 0 or settings.rate_limit_read_per_hour != 0:
        return
    if not settings.rate_limit_disabled_ack:
        raise RuntimeError(
            "STIGMEM_RATE_LIMIT_WRITE_PER_HOUR=0 and "
            "STIGMEM_RATE_LIMIT_READ_PER_HOUR=0 fully disable quota enforcement. "
            "To proceed, set STIGMEM_RATE_LIMIT_DISABLED_ACK=1 to acknowledge "
            "that this node accepts unbounded read and write traffic."
        )

    logger.warning(
        "SECURITY WARNING: quota enforcement is fully disabled "
        "(write=0, read=0) with explicit operator acknowledgment via "
        "STIGMEM_RATE_LIMIT_DISABLED_ACK=1."
    )


def _warn_if_cors_dev_localhost_enabled() -> None:
    """Log the expanded development CORS posture at startup."""
    if settings.cors_dev_localhost:
        logger.warning(
            "SECURITY WARNING: STIGMEM_CORS_DEV_LOCALHOST=1 enables browser "
            "access from localhost and loopback origins. Use this only for "
            "local development."
        )


def _warn_if_backend_immutability_unenforced() -> None:
    """Warn when the storage backend lacks DB-level facts-immutability triggers.

    P-DESTROY-1 (honesty): the append-only no-UPDATE/no-DELETE triggers
    (ADR-016 L2) are implemented for SQLite only. On libsql/Postgres the facts
    table is mutable by anyone with direct database write access, so tamper
    resistance on those backends rests on the L3+ CID / hash-chain layers, not
    L2 triggers. State that loudly rather than imply uniform immutability.
    """
    backend = getattr(settings, "storage_backend", "sqlite")
    if backend == "sqlite":
        return
    logger.warning(
        "SECURITY WARNING: storage_backend=%r does NOT enforce database-level "
        "facts immutability. The append-only no-UPDATE/no-DELETE triggers "
        "(ADR-016 L2) exist for SQLite only; on %s the facts table is mutable "
        "by anyone with direct DB write access. Tamper-evidence on this backend "
        "relies on the L3+ CID / hash-chain layers, not L2 triggers.",
        backend,
        backend,
    )


def _warn_if_legacy_sha256_acceptance_unbounded() -> None:
    """Warn when legacy SHA-256 API-key hashes are accepted with no cutoff (F-ID-4).

    Unsalted SHA-256 is weaker than the Argon2id default. The acceptance window
    is a v0.9.x migration affordance; leaving it open indefinitely
    (STIGMEM_LEGACY_SHA256_ACCEPT_UNTIL unset) is a standing weakness.
    """
    if settings.legacy_sha256_accept_until is not None:
        return
    logger.warning(
        "SECURITY WARNING: legacy SHA-256 API-key hashes are accepted with no "
        "cutoff (STIGMEM_LEGACY_SHA256_ACCEPT_UNTIL is unset). Unsalted SHA-256 "
        "is weaker than the Argon2id default; set a cutoff date to bound the "
        "migration window and force rotation of any keys not yet rehashed."
    )


def _node_url_is_loopback(node_url: str) -> bool:
    """Return True iff node_url's host is a loopback address."""
    return node_url_is_loopback(node_url)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        from .plugins import get_registry, register_discovered_plugins

        if settings.trust_mode == "strict" and not settings.node_private_key:
            raise RuntimeError("STIGMEM_NODE_PRIVATE_KEY must be set when trust_mode=strict")
        _enforce_federation_transport_security()
        _enforce_auth_required_in_production()
        _enforce_rate_limit_kill_switch_ack()
        _warn_if_cors_dev_localhost_enabled()
        _warn_if_backend_immutability_unenforced()
        _warn_if_legacy_sha256_acceptance_unbounded()

        discovered_plugins = register_discovered_plugins(freeze=False)
        _include_plugin_routers(app, discovered_plugins)
        apply_migrations()
        from .memory_garden_acl_gate import warn_if_memory_garden_acl_filtering_disabled

        warn_if_memory_garden_acl_filtering_disabled(logger)
        get_registry().freeze()

        if settings.otel_enabled:
            from .observability.tracing import init_tracing

            init_tracing(
                service_name=settings.otel_service_name,
                otlp_endpoint=settings.otel_exporter_otlp_endpoint,
            )

        pull_task: asyncio.Task[None] | None = None
        if settings.federation_enabled:
            from .federation.federation_pull import pull_loop_task
            from .federation.peer_token import init_federation_keys

            init_federation_keys()
            pull_task = asyncio.create_task(pull_loop_task())
            logger.info("Federation enabled — pull %ds", settings.federation_pull_interval_s)

        from .subscription_delivery import sweep_loop as _sub_sweep_loop

        sweep_task: asyncio.Task[None] = asyncio.create_task(_sub_sweep_loop())
        logger.info(
            "Stigmem subscription sweep enabled — interval %ds",
            settings.subscription_delivery_sweep_s,
        )

        logger.info(
            "Stigmem node ready — db=%s auth=%s federation=%s",
            settings.db_path,
            settings.auth_required,
            "enabled" if settings.federation_enabled else "disabled",
        )
        yield

        sweep_task.cancel()
        with suppress(asyncio.CancelledError):
            _unused_result = await cast("asyncio.Task[object]", sweep_task)

        if pull_task is not None:
            pull_task.cancel()
            with suppress(asyncio.CancelledError):
                _unused_result = await cast("asyncio.Task[object]", pull_task)

    app = FastAPI(
        title="Stigmem Reference Node",
        version="0.9.0a10",
        description=(
            "Reference node implementing the Stigmem v0.9.0a10 HTTP API — facts, federation, "
            "gardens, recall, subscriptions, audit, identity, content-addressed fact IDs. "
            "Experimental cross-cutting behavior remains opt-in where plugin-gated; tombstone "
            "admin and federation route contracts are mounted but access-gated."
        ),
        license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
        lifespan=lifespan,
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(BodySizeLimitMiddleware)
    _cors_regex = settings.cors_allowed_origin_regex
    if settings.cors_dev_localhost:
        _cors_regex = _DEV_LOCALHOST_CORS_REGEX
    if settings.cors_allowed_origins or _cors_regex:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_origin_regex=_cors_regex,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["ETag"],
            max_age=600,
        )

    @app.middleware("http")
    async def unsigned_plugin_override_warning(
        _request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Warn every request while development unsigned-plugin override is active."""
        from .plugins import get_registry

        unsigned_plugins = get_registry().development_unsigned_plugins()
        if unsigned_plugins:
            logger.warning(
                "SECURITY WARNING: unsigned plugins active via "
                "STIGMEM_PLUGIN_SIGNING_REQUIRED=false: %s",
                ", ".join(unsigned_plugins),
            )
        return await call_next(_request)

    if settings.mtls_enabled:

        @app.middleware("http")
        async def mtls_plaintext_guard(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            """Reject plaintext federation requests when mTLS is configured (§22.1)."""
            if request.method == "OPTIONS" and not request.url.path.startswith("/v1/federation"):
                return await call_next(request)
            if request.url.path.startswith("/v1/federation") and request.url.scheme != "https":
                return JSONResponse(
                    {
                        "error": "mTLS required",
                        "detail": "Federation transport requires mutual TLS (spec §22.1). "
                        "Connect via HTTPS with a valid node certificate.",
                    },
                    status_code=421,
                )
            return await call_next(request)

    app.include_router(admin_audit_router)
    app.include_router(cid_admin_router)
    app.include_router(auth_router)
    app.include_router(agent_keys_router)
    app.include_router(audit_router)
    app.include_router(facts_router)
    app.include_router(gardens_router)
    app.include_router(graph_router)
    app.include_router(identity_router)
    app.include_router(intents_router)
    app.include_router(federation_router)
    app.include_router(quarantine_router)
    app.include_router(lint_router)
    app.include_router(synthesize_router)
    app.include_router(decay_router)
    app.include_router(aliases_router)
    app.include_router(resolver_router)
    app.include_router(cards_router)
    app.include_router(recall_router)
    app.include_router(subscriptions_router)
    app.include_router(tombstones_router)
    app.include_router(mcp_router)
    app.include_router(wellknown_router)

    @app.get("/healthz", tags=["ops"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/doctor", tags=["ops"])
    def doctor() -> dict[str, str]:
        """Return coarse node health and operator posture.

        This endpoint is unauthenticated in v0.9.0a10. The garden ACL posture
        field is accepted as ops-endpoint disclosure and intentionally avoids
        garden names, membership rows, tenant identifiers, or policy subjects.
        """
        from .memory_garden_acl_gate import memory_garden_acl_filtering_state

        return {
            "status": "ok",
            "memory_garden_acl_filtering": memory_garden_acl_filtering_state(),
        }

    @app.get("/metrics", include_in_schema=False, tags=["ops"])
    def prometheus_metrics() -> Response:
        from .observability.metrics import make_metrics_response

        resp = make_metrics_response()
        if resp is None:
            from fastapi.responses import PlainTextResponse

            return PlainTextResponse("# prometheus_client not installed\n", status_code=200)
        return resp

    @app.get("/v1/me", tags=["auth"])
    def whoami(identity: Annotated[Identity, Depends(resolve_identity)]) -> dict[str, Any]:
        return {
            "entity_uri": identity.entity_uri,
            "permissions": sorted(identity.permissions),
            "oidc_sub": identity.oidc_sub,
            "tenant_id": identity.tenant_id,
        }

    @app.get("/ui", include_in_schema=False)
    def ui_index() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html", media_type="text/html")

    return app


def _include_plugin_routers(app: FastAPI, discovered_plugins: tuple[Any, ...]) -> None:
    """Include routers declared by installed plugins once per app instance."""
    if getattr(app.state, "stigmem_plugin_routes_included", False):
        return
    for plugin in discovered_plugins:
        for router in plugin.manifest.routes:
            app.include_router(router)
    app.state.stigmem_plugin_routes_included = True


app = create_app()


def run() -> None:
    if not settings.mtls_enabled:
        uvicorn.run(
            "stigmem_node.main:app",
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level,
            reload=False,
        )
        return

    from .federation.tls import cert_watcher_task, reload_tls_cert

    # Let uvicorn build the SSL context from cert/key files, then enforce TLS 1.3
    # floor and mTLS client-cert requirement on the resulting context object.
    config = uvicorn.Config(
        "stigmem_node.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
        ssl_certfile=settings.tls_cert_path,
        ssl_keyfile=settings.tls_key_path,
        ssl_ca_certs=settings.tls_ca_bundle or None,
        ssl_cert_reqs=ssl.CERT_REQUIRED,
    )
    config.load()

    if config.ssl:
        config.ssl.minimum_version = ssl.TLSVersion.TLSv1_3
    ssl_ctx = config.ssl

    async def _serve_with_cert_watcher() -> None:
        loop = asyncio.get_running_loop()
        if ssl_ctx is not None:
            loop.add_signal_handler(
                signal.SIGHUP,
                lambda: reload_tls_cert(ssl_ctx),
            )

        server = uvicorn.Server(config)
        watcher_task: asyncio.Task[None] | None = None
        if ssl_ctx is not None:
            watcher_task = asyncio.create_task(cert_watcher_task(ssl_ctx))

        try:
            await server.serve()
        finally:
            if watcher_task is not None:
                watcher_task.cancel()
                with suppress(asyncio.CancelledError):
                    _unused_result = await cast("asyncio.Task[object]", watcher_task)

    asyncio.run(_serve_with_cert_watcher())


if __name__ == "__main__":
    run()

```

### node/src/stigmem_node/net_util.py
```
"""Compatibility alias for :mod:`stigmem_node.utility.net_util`."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

__all__ = ["assert_safe_url", "node_url_is_loopback"]

if TYPE_CHECKING:
    from .utility.net_util import assert_safe_url, node_url_is_loopback
else:
    from .utility import net_util as _impl

    sys.modules[__name__] = _impl

```

### node/src/stigmem_node/routes/subscriptions.py
```
"""Subscription CRUD and replay-window routes — spec §20.3, §20.5.

POST   /v1/subscriptions                       — create (subscriber_identity = caller; BOLA §20.3.2)
GET    /v1/subscriptions                       — list caller's subscriptions
GET    /v1/subscriptions/{id}                  — get one (BOLA: 404 if not owner)
DELETE /v1/subscriptions/{id}                  — cancel (BOLA: 404 if not owner)
GET    /v1/subscriptions/{id}/events           — replay window (§20.5)
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import settings as _settings_pkg
from ..auth import Identity, resolve_identity
from ..db import db
from ..garden_acl import get_garden_by_garden_uri, require_garden_read
from ..models.constants import VALID_SCOPES
from ..models.subscriptions import (
    SubscriptionCreateRequest,
    SubscriptionEventRecord,
    SubscriptionEventsResponse,
    SubscriptionListResponse,
    SubscriptionRecord,
)
from ..subscription_delivery import _sanitize_payload as _sanitize_event_payload

router = APIRouter(prefix="/v1/subscriptions", tags=["subscriptions"])


def _target_kind(target: str) -> str:
    return "scope" if target in VALID_SCOPES else "entity"


def _row_to_record(row: Any) -> SubscriptionRecord:
    return SubscriptionRecord(
        id=row["id"],
        subscriber_identity=row["subscriber_identity"],
        target=row["target"],
        target_kind=row["target_kind"],
        on_change=row["on_change"],
        delivery_address=row["delivery_address"],
        idempotency_key=row["idempotency_key"],
        created_at=row["created_at"],
        last_delivered_at=row["last_delivered_at"],
        circuit_open=bool(row["circuit_open"]),
        consecutive_failures=row["consecutive_failures"],
    )


def _event_row_to_record(row: Any) -> SubscriptionEventRecord:
    return SubscriptionEventRecord(
        id=row["id"],
        subscription_id=row["subscription_id"],
        event_type=row["event_type"],
        entity_uri=row["entity_uri"],
        fact_id=row["fact_id"],
        payload=json.loads(row["payload"]),
        created_at=row["created_at"],
        delivered_at=row["delivered_at"],
        delivery_status=row["delivery_status"],
        delivery_attempts=row["delivery_attempts"],
    )


def _event_row_to_record_with_payload(row: Any, payload_json: str) -> SubscriptionEventRecord:
    """Like _event_row_to_record but substitutes a pre-sanitized payload JSON string."""
    return SubscriptionEventRecord(
        id=row["id"],
        subscription_id=row["subscription_id"],
        event_type=row["event_type"],
        entity_uri=row["entity_uri"],
        fact_id=row["fact_id"],
        payload=json.loads(payload_json),
        created_at=row["created_at"],
        delivered_at=row["delivered_at"],
        delivery_status=row["delivery_status"],
        delivery_attempts=row["delivery_attempts"],
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=SubscriptionRecord, status_code=status.HTTP_201_CREATED)
def create_subscription(
    req: SubscriptionCreateRequest,
    identity: Annotated[Identity, Depends(resolve_identity)],
) -> SubscriptionRecord:
    """Create a subscription (Spec-X7-Subscriptions).

    subscriber_identity is always the caller (BOLA).
    """
    if not identity.can_read():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="read permission required"
        )

    # §17 garden ACL: if target is a garden URI, caller must be a member
    if req.target.startswith("stigmem://") and "/garden/" in req.target:
        garden = get_garden_by_garden_uri(req.target, tenant_id=identity.tenant_id)
        if garden is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="garden not found")
        require_garden_read(garden, identity)

    # Idempotency key: return existing subscription if key matches THIS caller.
    # Scoped to subscriber and tenant to prevent cross-entity metadata leakage (R2).
    if req.idempotency_key:
        with db() as conn:
            existing = conn.execute(
                """SELECT * FROM subscriptions
                   WHERE idempotency_key=? AND tenant_id=? AND subscriber_identity=?""",
                (req.idempotency_key, identity.tenant_id, identity.entity_uri),
            ).fetchone()
        if existing is not None:
            return _row_to_record(existing)

    # Natural dedup: same (subscriber, target, on_change, delivery_address) → return existing
    with db() as conn:
        dupe = conn.execute(
            """SELECT * FROM subscriptions
               WHERE subscriber_identity=? AND target=? AND on_change=?
                 AND delivery_address=? AND tenant_id=?""",
            (
                identity.entity_uri,
                req.target,
                req.on_change,
                req.delivery_address,
                identity.tenant_id,
            ),
        ).fetchone()
        if dupe is not None:
            return _row_to_record(dupe)

    # F-AVAIL-3: cap active subscriptions per principal to bound fan-out/DoS.
    _sub_cap = _settings_pkg.settings.max_subscriptions_per_principal
    if _sub_cap > 0:
        with db() as conn:
            held = conn.execute(
                "SELECT COUNT(*) AS n FROM subscriptions "
                "WHERE subscriber_identity=? AND tenant_id=?",
                (identity.entity_uri, identity.tenant_id),
            ).fetchone()["n"]
        if held >= _sub_cap:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"subscription limit reached ({_sub_cap})",
            )

    sub_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    target_kind = _target_kind(req.target)

    with db() as conn:
        conn.execute(
            """INSERT INTO subscriptions
               (id, subscriber_identity, target, target_kind, on_change,
                delivery_address, idempotency_key, created_at, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                sub_id,
                identity.entity_uri,
                req.target,
                target_kind,
                req.on_change,
                req.delivery_address,
                req.idempotency_key,
                now,
                identity.tenant_id,
            ),
        )
        row = conn.execute("SELECT * FROM subscriptions WHERE id=?", (sub_id,)).fetchone()

    return _row_to_record(row)


@router.get("", response_model=SubscriptionListResponse)
def list_subscriptions(
    identity: Annotated[Identity, Depends(resolve_identity)],
) -> SubscriptionListResponse:
    """List the authenticated caller's subscriptions (BOLA: own only)."""
    if not identity.can_read():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="read permission required"
        )

    with db() as conn:
        rows = conn.execute(
            """SELECT * FROM subscriptions
               WHERE subscriber_identity=? AND tenant_id=?
               ORDER BY created_at DESC""",
            (identity.entity_uri, identity.tenant_id),
        ).fetchall()

    return SubscriptionListResponse(
        subscriptions=[_row_to_record(r) for r in rows],
        total=len(rows),
    )


@router.get("/{subscription_id}", response_model=SubscriptionRecord)
def get_subscription(
    subscription_id: str,
    identity: Annotated[Identity, Depends(resolve_identity)],
) -> SubscriptionRecord:
    """Get a subscription by ID (BOLA: returns 404 if caller does not own it)."""
    if not identity.can_read():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="read permission required"
        )

    with db() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE id=? AND tenant_id=?",
            (subscription_id, identity.tenant_id),
        ).fetchone()

    if row is None or row["subscriber_identity"] != identity.entity_uri:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")

    return _row_to_record(row)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: str,
    identity: Annotated[Identity, Depends(resolve_identity)],
) -> None:
    """Cancel a subscription (BOLA: only the owner may delete)."""
    if not identity.can_read():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="read permission required"
        )

    with db() as conn:
        row = conn.execute(
            "SELECT id, subscriber_identity FROM subscriptions WHERE id=? AND tenant_id=?",
            (subscription_id, identity.tenant_id),
        ).fetchone()

    if row is None or row["subscriber_identity"] != identity.entity_uri:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")

    with db() as conn:
        conn.execute("DELETE FROM subscriptions WHERE id=?", (subscription_id,))


# ---------------------------------------------------------------------------
# Replay window
# ---------------------------------------------------------------------------


@router.get("/{subscription_id}/events", response_model=SubscriptionEventsResponse)
def list_subscription_events(
    subscription_id: str,
    identity: Annotated[Identity, Depends(resolve_identity)],
    since: str | None = Query(
        None,
        description="ISO 8601 timestamp; return events created at or after this time",
    ),
    cursor: str | None = Query(None, description="Opaque pagination cursor (event id)"),
    limit: int = Query(50, ge=1, le=500),
) -> SubscriptionEventsResponse:
    """Replay window: return delivery events for a subscription (Spec-X7-Subscriptions).

    Results are bounded to the configured replay window (default 24 h).
    """
    if not identity.can_read():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="read permission required"
        )

    with db() as conn:
        sub_row = conn.execute(
            "SELECT id, subscriber_identity FROM subscriptions WHERE id=? AND tenant_id=?",
            (subscription_id, identity.tenant_id),
        ).fetchone()

    if sub_row is None or sub_row["subscriber_identity"] != identity.entity_uri:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")

    replay_s = _settings_pkg.settings.subscription_replay_s
    window_cutoff = (datetime.now(UTC) - timedelta(seconds=replay_s)).isoformat()
    effective_since = max(since, window_cutoff) if since is not None else window_cutoff

    if cursor:
        sql = (
            "SELECT rowid, * FROM subscription_events "
            "WHERE subscription_id = ? AND created_at >= ? AND rowid > ? "
            "ORDER BY rowid ASC LIMIT ?"
        )
        params: list[Any] = [subscription_id, effective_since, int(cursor)]
    else:
        sql = (
            "SELECT rowid, * FROM subscription_events "
            "WHERE subscription_id = ? AND created_at >= ? "
            "ORDER BY rowid ASC LIMIT ?"
        )
        params = [subscription_id, effective_since]
    params.append(limit + 1)

    with db() as conn:
        rows = conn.execute(sql, params).fetchall()

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = str(rows[-1]["rowid"]) if has_more and rows else None

    # S3 fix: re-apply §17 garden ACL and §19 sanitizer at replay time.
    # subscription_events.payload stores the raw pre-delivery payload; without this
    # re-check a subscriber could retrieve garden-scoped facts they've since been
    # removed from, or sanitizer-redacted content, via the replay window.
    event_ctx = {
        "subscriber_identity": sub_row["subscriber_identity"],
        "tenant_id": identity.tenant_id,
    }
    safe_events: list[SubscriptionEventRecord] = []
    for r in rows:
        raw_payload = json.loads(r["payload"])
        sanitized = _sanitize_event_payload(event_ctx, raw_payload)
        if sanitized is None:
            # ACL/sanitizer blocked — return redacted placeholder
            safe_payload = json.dumps({"fact_id": raw_payload.get("id"), "redacted": True})
        else:
            safe_payload = json.dumps(sanitized)
        safe_events.append(_event_row_to_record_with_payload(r, safe_payload))

    return SubscriptionEventsResponse(
        events=safe_events,
        total=len(safe_events),
        cursor=next_cursor,
    )

```

### node/src/stigmem_node/settings.py
```
from datetime import datetime
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STIGMEM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: str = "stigmem.db"
    host: str = "0.0.0.0"  # noqa: S104  # nosec B104 — overridable via STIGMEM_HOST
    port: int = 8765
    # Optional stable node identity for deterministic local/CI federation fixtures.
    # When unset, the node creates and persists a stigmem:node:<uuid> identity.
    node_id: str = ""
    node_url: str = "http://localhost:8765"
    # The node's own org identity URI (Phase 2a). Empty → derived from node_url.
    entity_uri: str = ""
    log_level: str = "info"
    cors_allowed_origins: Annotated[list[str], NoDecode] = []
    cors_allowed_origin_regex: str | None = None
    cors_allow_credentials: bool = True
    cors_dev_localhost: bool = False

    # When True (default), every request must carry a valid Bearer token.
    # Set to False only for local development / single-operator installs.
    auth_required: bool = True
    # Static API-key lifecycle controls. 0 disables max-age enforcement.
    api_key_max_age_days: int = 90
    api_key_expiring_soon_days: int = 30
    legacy_sha256_accept_until: datetime | None = None

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_allowed_origins(cls, v: object) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return v  # type: ignore[return-value]

    # Federation — Phase 3 (spec §6)
    federation_enabled: bool = False
    # Base64url Ed25519 keypair. If both are empty, auto-generated and stored in node_meta.
    federation_pubkey: str = ""
    federation_privkey: str = ""
    # Pull replication interval in seconds (spec §6.3); advisory pull_interval_s
    # from peer overrides this.
    federation_pull_interval_s: int = 30
    federation_push_enabled: bool = False
    # Explicit dev/test escape hatch for federation without mTLS. Production
    # federation should leave this false and configure STIGMEM_TLS_* instead.
    federation_insecure: bool = False
    # Additional acknowledgement for local Docker/dev networks whose service DNS
    # names are not loopback. Never set in production.
    local_dev_allow_insecure_non_loopback: bool = False
    # Nonce window: how long (seconds) a nonce is kept to detect replays
    # (spec §6.6, default 5 min).
    federation_nonce_window_s: int = 300
    # Clock-skew leeway for peer-token exp/iat/nbf claim checks.
    peer_token_leeway_s: int = 30
    # Maximum accepted remote HLC skew for federated fact ingest. Future skew is
    # strict by default because it can advance local logical time; past skew is a
    # wider archival bound and may be set to 0 for one-off historical backfills.
    federation_hlc_max_future_skew_s: int = 300
    federation_hlc_max_past_skew_s: int = 2_592_000
    # Dual-trust grace window (hours) for an origin's PRIOR (retired) signing key.
    # After a key rotation, the retiring key is accepted alongside the current key
    # only while now - rotation_event.rotated_at <= this window; past it the prior
    # key is DROPPED (a stale/compromised retired key can no longer forge origin
    # signatures, direct or relayed). Generous 7-day default so legitimate
    # in-progress rotations are never disrupted; the current key is always accepted.
    federation_key_rotation_grace_hours: int = 168
    # Allow team-scoped facts to cross federation boundaries
    # (must be explicitly enabled; audit-logged).
    federation_allow_team: bool = False
    # Relay re-federates inbound facts only when ON, subject to origin
    # scope/tenant propagation (Phase 2c). Default OFF = today's behaviour.
    federation_relay_enabled: bool = False

    # Decay sweeper (Phase 6, spec §decay)
    # 0 = disabled; positive = decay non-expiring facts older than N seconds
    # when sweep runs without explicit ttl_seconds
    decay_ttl_seconds: int = 0
    # 0.0 = disabled; positive = decay facts below this confidence when sweep
    # runs without explicit min_confidence
    decay_min_confidence: float = 0.0

    # Track C / C1: require Ed25519 attestation on all fact assertions.
    # When True, POST /v1/facts must include a valid attestation token.
    # Defaults to False for backward compatibility.
    attestation_required: bool = False

    # OIDC bridge (Track B / B3): human identity → scoped API keys.
    # Set oidc_enabled=true and configure the remaining fields to activate.
    oidc_enabled: bool = False
    # IdP issuer URL; discovery doc fetched from {issuer_url}/.well-known/openid-configuration
    oidc_issuer_url: str = ""
    # client_id expected in the id_token's "aud" claim
    oidc_audience: str = ""
    # lifetime of issued API keys in hours (default 8 h working-day session)
    oidc_token_ttl_hours: int = 8
    # Accepted OIDC id_token signing algorithms. Operators can narrow this list.
    oidc_id_token_algorithms: list[str] = ["RS256", "ES256", "PS256", "EdDSA"]
    # comma-separated list of allowed email domains; empty = allow any
    oidc_allowed_domains: str = ""

    # Async job threshold (spec §14.5 / §15.4): scopes with more facts than this
    # trigger the async 202 path. Override in tests to force async path at small scale.
    async_job_threshold: int = 100_000

    # Source attestation mode (legacy compatibility field).
    # Source-attestation runtime behavior is gated by the experimental
    # stigmem-plugin-source-attestation package. Default installs keep this off.
    source_attestation_mode: str = "off"

    # P-INJ-1: source ↔ identity binding, graduated to core. The `attested` flag
    # is always evaluated (a fact's source is attested when it matches the writing
    # principal). When this is true, an unattested source is REJECTED at write;
    # default false flags it (attested=False) but allows the write. Enforce belongs
    # in the hardened profile — it breaks writing facts sourced from elsewhere.
    source_attestation_enforce: bool = False

    # F-CONF-1: garden ACL recall filtering, graduated to core and ON by default.
    # Restricts tenant-wide recall/query/graph/subscription results to gardens the
    # caller is a member of. Facts with garden_id=NULL (single-tenant installs) are
    # unaffected. Set false only to intentionally accept tenant-wide garden visibility.
    memory_garden_acl_recall_filter: bool = True

    # Garden-membership-derived OIDC permission ceiling, graduated to core.
    # Off by default: enabling it caps OIDC-issued permissions to what the user's
    # garden memberships grant, which downgrades non-member sessions — a hardened
    # least-privilege posture, not a safe universal default. Belongs in the
    # hardened profile.
    oidc_permission_ceiling: bool = False

    # Rate limiting for hosted offering (per API key, sliding 1-hour window).
    # 0 = disabled.
    rate_limit_write_per_hour: int = 1000
    rate_limit_read_per_hour: int = 5000
    rate_limit_disabled_ack: bool = False

    # F-AVAIL-1: ingest size caps (DoS protection). 0 disables the cap.
    max_request_body_bytes: int = 1_048_576  # 1 MiB hard cap on any request body
    max_fact_value_bytes: int = 262_144  # 256 KiB cap on a single fact value

    # Storage backend (Phase 8 / 11).
    # "sqlite"   (default) — local SQLite file at db_path.
    # "libsql"             — libSQL / Turso; uses db_path as the local replica
    #                        file; set libsql_url + libsql_auth_token for
    #                        embedded-replica sync with Turso.
    # "postgres"           — PostgreSQL; set pg_dsn to a libpq connection string.
    storage_backend: str = "sqlite"
    # Turso database endpoint, e.g. "libsql://my-db.turso.io"
    libsql_url: str = ""
    # Turso auth token (from `turso db tokens create`)
    libsql_auth_token: str = ""
    # PostgreSQL connection string, e.g. "postgresql://user:pw@localhost/stigmem"
    pg_dsn: str = ""
    # DATABASE_URL alias (Heroku / PaaS convention); also read from bare DATABASE_URL env var.
    database_url: str = ""
    # PostgreSQL schema for all tables (default: "public").  Use a unique
    # per-test schema to achieve row-level isolation without separate databases.
    pg_schema: str = "public"
    # Connection pool bounds for the Postgres backend.
    postgres_pool_min: int = 2
    postgres_pool_max: int = 10

    # Encryption at rest (Phase 8).
    # "off" (default) — no encryption; plaintext DB (dev-friendly default).
    # "on"            — SQLCipher for SQLite backend; native encryption for libSQL.
    # When "on", exactly one of at_rest_key_passphrase_env / at_rest_key_kms_uri
    # must be set — the node refuses to start otherwise.
    at_rest_encryption: str = "off"
    # Name of the env var whose value is the passphrase (not the passphrase itself).
    # e.g. STIGMEM_AT_REST_KEY_PASSPHRASE_ENV=MY_DB_PASSPHRASE
    at_rest_key_passphrase_env: str = ""
    # KMS URI for raw 32-byte key material. "env://VAR" reads a hex-encoded key
    # from env var VAR. Future schemes: "aws-kms://...", "gcp-kms://...".
    at_rest_key_kms_uri: str = ""

    @field_validator("at_rest_encryption")
    @classmethod
    def _validate_encryption_mode(cls, v: str) -> str:
        if v not in ("on", "off"):
            raise ValueError(f"at_rest_encryption must be 'on' or 'off'; got {v!r}")
        return v

    # Federation Trust — Phase 8 (spec §19)
    # trust_mode controls source-trust scoring and quarantine routing:
    #   "strict"  — trust is computed for all inbound facts; t < 0.2 → quarantine.
    #   "relaxed" — trust is computed but quarantine is not auto-triggered (default).
    #   "off"     — trust not computed; source_trust is null on all facts.
    trust_mode: str = "relaxed"

    # Sanitizer mode (§19.7) applied at recall time:
    #   "block"     — fact excluded, placeholder returned.
    #   "quarantine"— fact moved to quarantine garden.
    #   "warn"      — fact returned with sanitizer_warnings (default).
    #   "off"       — no check (implied by trust_mode=off).
    sanitizer_mode: str = "warn"

    # UUID of the node's designated quarantine garden.
    # Required in strict mode; facts below threshold are rejected with 403 if unset.
    quarantine_garden_id: str = ""

    # Source-trust score weights (§19.4.2).  Must sum to 1.0; deviations are not
    # validated at startup — set incorrectly and t will be out of [0,1] range.
    trust_weight_identity: float = 0.35
    trust_weight_peer_history: float = 0.30
    trust_weight_scope_authority: float = 0.25
    trust_weight_attestation_mode: float = 0.10

    # Path to a newline-delimited file of extra sanitizer regex patterns (§19.7.2).
    sanitizer_extra_patterns_file: str = ""

    # Path to YAML file defining operator auto-trust rules (always_trust / never_trust).
    trust_rules_file: str = ""

    # Plugin signing gate (ADR-011 / PR 4-INF.3).
    # When true, installed entry-point plugins must pass signing verification
    # before registration. Set false only for local development; unsigned plugin
    # loading remains warning- and audit-visible.
    plugin_signing_required: bool = True
    # Required literal acknowledgement before unsigned-plugin loading is allowed.
    plugin_unsigned_ack: str = ""
    # Disable installed entry-point plugin discovery for test and smoke
    # environments that intentionally exercise the default no-plugin node.
    plugin_auto_discovery_enabled: bool = True
    # Comma-separated Sigstore signing identities accepted for production plugin
    # registration when plugin_signing_required=true.
    plugin_trusted_publishers: str = ""
    # Comma-separated signing identities accepted through explicit operator
    # override. Overrides remain audit-visible and are not a substitute for the
    # trusted-publisher allowlist.
    plugin_trust_override_publishers: str = ""

    # Transparency log backend (§19.2.3):
    #   "local"  — append-only JSONL file with hash chain (default, no external deps).
    #   "rekor"  — Sigstore Rekor REST API.
    #   "off"    — no TL submission; inclusion proofs are never verified.
    tl_backend: str = "local"
    tl_local_path: str = "stigmem_tl.jsonl"
    tl_rekor_url: str = "https://rekor.sigstore.dev"
    fact_chain_checkpoint_interval: int = 1000
    fact_chain_checkpoint_max_age_s: int = 60
    fact_chain_checkpoint_retry_s: int = 60

    # Capability token signing — spec §19.3.2 (C-SEC-1).
    # Base64url-encoded raw 32-byte Ed25519 seed used to sign capability tokens and
    # revocation events. If empty, token signing is skipped and verify_token() will
    # reject all tokens (dev/test nodes that don't participate in trust federation).
    node_private_key: str = ""

    @field_validator("node_private_key")
    @classmethod
    def _validate_node_private_key(cls, v: str) -> str:
        if not v:
            return v
        import base64

        padded = v + "=" * (-len(v) % 4)
        try:
            raw = base64.urlsafe_b64decode(padded)
        except Exception as exc:
            raise ValueError(f"node_private_key is not valid base64url: {exc}") from exc
        if len(raw) != 32:
            raise ValueError(f"node_private_key must decode to exactly 32 bytes; got {len(raw)}")
        return v

    # -------------------------------------------------------------------------
    # Embeddings — Phase 9 (spec §20 / design memo §2)
    # -------------------------------------------------------------------------
    # Set embed_enabled=true to activate sqlite-vec integration.
    # When false (default), no extension is loaded and no embeddings are stored.
    embed_enabled: bool = False

    # "local"  — Ollama HTTP API (default); requires a running Ollama instance.
    # "openai" — OpenAI embeddings API; requires OPENAI_API_KEY (or the env var
    #            named by embed_openai_api_key_env).
    # "stub"   — deterministic test stub; no external dependencies.
    embed_model_provider: str = "local"

    # Model identifier passed to the provider.
    # Local default:  "nomic-embed-text-v1.5" (768-dim, Apache-2.0, runs on laptop).
    # OpenAI default: "text-embedding-3-small" (1536-dim).
    embed_model_id: str = "nomic-embed-text-v1.5"

    # Output dimensionality.  MUST match the model; changing this after the first
    # embedding requires running `stigmem embed reindex` (migration tool).
    embed_dimension: int = 768

    # Ollama base URL (local provider only).
    embed_ollama_url: str = "http://localhost:11434"

    # Name of the env var holding the OpenAI API key (openai provider only).
    embed_openai_api_key_env: str = "OPENAI_API_KEY"

    # Facts with confidence below this threshold have their vec_facts entry
    # deleted during the decay sweep (design memo §2 "Decay interaction").
    embed_tombstone_threshold: float = 0.1

    # Subscription primitive (Phase 9, spec §20)
    # How long (seconds) the replay window extends back from now (default 24 h).
    subscription_replay_s: int = 86400
    # How often (seconds) the background sweep retries pending/failed delivery.
    subscription_delivery_sweep_s: int = 30
    # Consecutive delivery failures before the circuit breaker opens on a subscription.
    subscription_circuit_threshold: int = 10
    # How long (seconds) an event may remain in 'delivering' state before the next
    # ``deliver_pending`` invocation reverts it to 'pending' for redelivery.
    # Guards against crashed workers stranding events.  Must be larger than the
    # worst-case webhook timeout (10 s) by a comfortable margin.
    subscription_claim_timeout_s: int = 300
    # F-AVAIL-3: cap on active subscriptions per (subscriber_identity, tenant).
    # 0 disables the cap. Default is generous; raise for high-fan-out operators.
    max_subscriptions_per_principal: int = 1000

    # -------------------------------------------------------------------------
    # mTLS Federation Transport — Phase 12 (spec §22.1)
    # -------------------------------------------------------------------------
    # Path to the node's PEM-encoded X.509 certificate for mTLS federation.
    # When tls_cert_path + tls_key_path are both set, mTLS is activated:
    # the uvicorn server requires client certs and the pull client presents this
    # cert to peers.  Opt-out is only permitted for localhost deployments
    # (set host to "localhost" / "127.0.0.1" / "::1" and leave paths empty).
    tls_cert_path: str = ""
    # Path to the node's PEM-encoded private key corresponding to tls_cert_path.
    tls_key_path: str = ""
    # Path to a PEM CA bundle used to verify peer certificates.
    # Required when tls_cert_path + tls_key_path are configured.
    tls_ca_bundle: str = ""

    @model_validator(mode="after")
    def _require_ca_bundle_for_mtls(self) -> "Settings":
        if self.tls_cert_path and self.tls_key_path and not self.tls_ca_bundle:
            raise ValueError(
                "STIGMEM_TLS_CA_BUNDLE is required when mTLS is enabled "
                "(STIGMEM_TLS_CERT_PATH + STIGMEM_TLS_KEY_PATH are set). "
                "Without it, peer certs fall back to the system CA store instead "
                "of the closed federation trust bundle (spec §22.1.2.2)."
            )
        return self

    @property
    def mtls_enabled(self) -> bool:
        """True when mTLS cert + key are configured (non-localhost deployments)."""
        return bool(self.tls_cert_path and self.tls_key_path)

    # -------------------------------------------------------------------------
    # Observability — Phase 13 (spec §23)
    # -------------------------------------------------------------------------
    # Set otel_enabled=true to activate OpenTelemetry tracing.
    # Requires stigmem-node[observability] (opentelemetry-sdk + OTLP exporter).
    otel_enabled: bool = False

    # Service name reported in OTel resource attributes.
    otel_service_name: str = "stigmem-node"

    # OTLP collector base URL (HTTP protocol).
    # e.g. "http://localhost:4318" for a local OpenTelemetry Collector or Tempo.
    # Leave empty to disable OTLP export (spans collected locally only).
    otel_exporter_otlp_endpoint: str = ""

    # -------------------------------------------------------------------------
    # Time-travel / as_of — Phase 13 (spec §24.2.2)
    # -------------------------------------------------------------------------
    # Minimum allowed as_of timestamp (ISO 8601 UTC). Queries before this floor
    # return 400 as_of_before_retention_floor. Empty string = no floor enforced.
    as_of_retention_floor: str = ""


settings = Settings()

```

### node/src/stigmem_node/subscription_delivery.py
```
"""Subscription delivery engine — spec §20.4.

Responsibilities:
1. ``fan_out`` — when a fact is written, find matching subscriptions and insert
   pending ``subscription_events`` rows (fast; called synchronously on every write).
2. ``deliver_pending`` — sweep: attempt delivery for all pending/due-for-retry events.
3. ``sweep_loop`` — asyncio task run in the app lifespan; calls deliver_pending periodically.

Delivery types:
- ``webhook`` — HTTP POST to delivery_address with exponential backoff (1 s, 2 s, 4 s … ≤ 300 s).
- ``wake``    — structured JSON emitted to stderr; platform-specific integration hook.

Garden ACL (§17) and content sanitizer (§19) are applied at delivery time.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from . import settings as _settings_pkg
from .auth import Identity
from .db import db
from .garden_acl import get_member_role
from .lifecycle.tombstone_cache import is_tombstoned as _is_tombstoned
from .memory_garden_acl_gate import garden_acl_enforced
from .net_util import assert_safe_url
from .recall.recall_pipeline import apply_recall_pipeline

logger = logging.getLogger("stigmem.subscriptions")
_DELIVER_PENDING_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Fan-out — called from routes/facts.py after each successful fact write
# ---------------------------------------------------------------------------


def fan_out(
    fact_id: str,
    entity: str,
    scope: str,
    garden_id: str | None,
    tenant_id: str,
    fact_payload_json: str,
) -> None:
    """Find subscriptions matching this fact and create pending delivery events."""
    now = datetime.now(UTC).isoformat()

    with db() as conn:
        scope_subs = conn.execute(
            """SELECT * FROM subscriptions
               WHERE target_kind='scope' AND target=? AND tenant_id=? AND circuit_open=0""",
            (scope, tenant_id),
        ).fetchall()

        entity_subs = conn.execute(
            """SELECT * FROM subscriptions
               WHERE target_kind='entity' AND target=? AND tenant_id=? AND circuit_open=0""",
            (entity, tenant_id),
        ).fetchall()

        for sub in list(scope_subs) + list(entity_subs):
            event_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO subscription_events
                   (id, subscription_id, event_type, entity_uri, fact_id,
                    payload, created_at, delivery_status)
                   VALUES (?,?,?,?,?,?,?,'pending')""",
                (event_id, sub["id"], "fact_asserted", entity, fact_id, fact_payload_json, now),
            )


# ---------------------------------------------------------------------------
# Delivery sweep — called by sweep_loop every N seconds
# ---------------------------------------------------------------------------


def deliver_pending() -> None:
    """Attempt delivery for all pending events that are due.

    Uses an atomic claim (``pending → delivering``) so that the background
    ``sweep_loop`` and any concurrent caller (admin replay endpoints,
    tests, future per-tenant workers) cannot deliver the same event twice.
    See issue #47 and migration 028 for the rationale.

    Concurrency model
    -----------------
    1. Recover stale claims: any row in ``delivering`` with
       ``claimed_at`` older than ``subscription_claim_timeout_s`` is reset
       to ``pending`` so a crashed worker cannot strand events.
    2. Atomically claim up to 100 due rows via
       ``UPDATE … WHERE id IN (SELECT … LIMIT 100) RETURNING …`` — SQLite
       serializes writes, so concurrent claimers see disjoint row sets.
    3. For each claimed row, attempt delivery and transition to
       ``delivered`` (success) or back to ``pending`` with a fresh
       ``next_retry_at`` (failure).
    """
    if not _DELIVER_PENDING_LOCK.acquire(blocking=False):
        logger.debug("subscription delivery already in progress; skipping concurrent drain")
        return

    try:
        now = datetime.now(UTC).isoformat()
        claim_timeout_s = _settings_pkg.settings.subscription_claim_timeout_s
        stale_cutoff = datetime.fromtimestamp(
            time.time() - claim_timeout_s,
            UTC,
        ).isoformat()

        with db() as conn:
            # 1. Recover stale claims left behind by a crashed worker.  We do NOT
            #    reset delivery_attempts — the next attempt counts as a retry.
            conn.execute(
                """UPDATE subscription_events
                      SET delivery_status='pending', claimed_at=NULL
                    WHERE delivery_status='delivering'
                      AND claimed_at IS NOT NULL
                      AND claimed_at < ?""",
                (stale_cutoff,),
            )

            # 2. Atomic claim.  The inner SELECT is the same predicate the old
            #    non-atomic path used, joined to subscriptions for circuit-open
            #    filtering.  The outer UPDATE … RETURNING gives us the claimed
            #    rows in a single round-trip; no other caller can claim them
            #    until we release them.
            claimed = conn.execute(
                """UPDATE subscription_events
                      SET delivery_status='delivering', claimed_at=?
                    WHERE id IN (
                        SELECT e.id
                          FROM subscription_events e
                          JOIN subscriptions s ON e.subscription_id = s.id
                         WHERE e.delivery_status = 'pending'
                           AND s.circuit_open = 0
                           AND (e.next_retry_at IS NULL OR e.next_retry_at <= ?)
                         ORDER BY e.created_at ASC
                         LIMIT 100
                    )
                    RETURNING id""",
                (now, now),
            ).fetchall()

            if not claimed:
                return

            claimed_ids = [row["id"] for row in claimed]
            # ``placeholders`` is a fixed "?,?,?…" string whose length comes from
            # ``claimed_ids`` (UUIDs we just emitted into our own table) — no user
            # input flows into the SQL text, so the f-string interpolation is safe.
            placeholders = ",".join("?" * len(claimed_ids))
            _base = (
                "SELECT e.id, e.subscription_id, e.event_type, e.entity_uri, e.fact_id,"
                " e.payload, e.created_at, e.delivery_attempts,"
                " s.on_change, s.delivery_address, s.subscriber_identity, s.tenant_id,"
                " s.circuit_open"
                " FROM subscription_events e"
                " JOIN subscriptions s ON e.subscription_id = s.id"
                " WHERE e.id IN ("
            )
            select_sql = _base + placeholders + ")"  # noqa: S608 — fixed "?,…" string
            events = conn.execute(select_sql, claimed_ids).fetchall()

        for event in events:
            try:
                payload = json.loads(event["payload"])
                success = _deliver_one(event, payload)
            except Exception as exc:
                logger.error("Delivery error for event %s: %s", event["id"], exc)
                success = False

            _record_result(event, success)
    finally:
        _DELIVER_PENDING_LOCK.release()


# ---------------------------------------------------------------------------
# Delivery helpers
# ---------------------------------------------------------------------------


def _deliver_one(event: Any, payload: dict[str, Any]) -> bool:
    on_change = event["on_change"]
    if on_change == "webhook":
        return _deliver_webhook(event, payload)
    if on_change == "wake":
        return _deliver_wake(event, payload)
    logger.error("Unknown on_change %r for event %s", on_change, event["id"])
    return False


def _subscriber_identity(entity_uri: str, tenant_id: str) -> Identity:
    return Identity(entity_uri=entity_uri, permissions=["read"], tenant_id=tenant_id)


def _subscriber_has_active_key(entity_uri: str, tenant_id: str) -> bool:
    """Return True if at least one non-expired API key exists for this identity.

    Only consulted when STIGMEM_AUTH_REQUIRED=true so that single-operator
    (auth-disabled) nodes are not affected.
    """
    from . import settings as _sp

    if not _sp.settings.auth_required:
        return True
    now = datetime.now(UTC).isoformat()
    with db() as conn:
        row = conn.execute(
            "SELECT id FROM api_keys WHERE entity_uri=? AND tenant_id=?"
            " AND (expires_at IS NULL OR expires_at > ?) LIMIT 1",
            (entity_uri, tenant_id, now),
        ).fetchone()
    return row is not None


def _sanitize_payload(event: Any, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Apply §17 garden ACL and §19 sanitizer.  Returns None to suppress delivery."""
    from .models.facts import FactRecord, FactValue

    subscriber = event["subscriber_identity"]
    tenant_id = event["tenant_id"]

    # S2 fix: re-check that the subscriber still holds an active read credential.
    # Prevents continued delivery after API key revocation for scope/entity subscriptions.
    if not _subscriber_has_active_key(subscriber, tenant_id):
        return None

    # §17 garden ACL re-check: skip delivery if subscriber no longer a member
    garden_uuid = payload.get("garden_id")
    if garden_uuid and garden_acl_enforced():
        role = get_member_role(garden_uuid, subscriber)
        if role is None:
            return None

    # §23.3.3 r.2: drop event immediately when entity has an active tombstone.
    # Uses the in-process cache (§23.3.3 r.4); 60-second leak window is acceptable.
    entity_for_tombstone = payload.get("entity")
    if entity_for_tombstone and _is_tombstoned(entity_for_tombstone, tenant_id):
        return None

    try:
        record = FactRecord(
            id=payload["id"],
            entity=payload["entity"],
            relation=payload["relation"],
            value=FactValue(type=payload["value_type"], v=payload.get("value_v")),
            source=payload["source"],
            timestamp=payload["timestamp"],
            confidence=float(payload.get("confidence", 1.0)),
            scope=payload.get("scope", "local"),
        )
        identity = _subscriber_identity(subscriber, tenant_id)
        results = apply_recall_pipeline([record], identity=identity, include_low_trust=True)
        if not results:
            return None
        sanitized = results[0]
        if sanitized.sanitizer_redacted:
            return {"fact_id": payload["id"], "redacted": True}
        out = dict(payload)
        out["value_v"] = str(sanitized.value.v) if sanitized.value.v is not None else None
        if sanitized.sanitizer_warnings:
            out["sanitizer_warnings"] = sanitized.sanitizer_warnings
        return out
    except Exception as exc:
        logger.warning("Sanitizer error for fact %s: %s", payload.get("id"), exc)
        return payload


def _deliver_webhook(event: Any, payload: dict[str, Any]) -> bool:
    sanitized = _sanitize_payload(event, payload)
    if sanitized is None:
        # ACL/sanitizer blocked — mark delivered, don't retry
        _mark_delivered(event["id"], event["subscription_id"])
        return True

    # SSRF guard (P-CONF-2): never POST to a private/loopback/link-local/IMDS
    # address. Unsafe addresses can never become deliverable, so stop retrying.
    try:
        assert_safe_url(event["delivery_address"], allow_schemes=frozenset({"https", "http"}))
    except ValueError as exc:
        logger.warning(
            "Webhook delivery blocked for subscription %s: unsafe delivery_address (%s)",
            event["subscription_id"],
            exc,
        )
        _mark_delivered(event["id"], event["subscription_id"])
        return True

    body = {
        "event_id": event["id"],
        "idempotency_key": event["id"],
        "subscription_id": event["subscription_id"],
        "event_type": event["event_type"],
        "fact": sanitized,
    }

    try:
        with httpx.Client(timeout=10.0, follow_redirects=False) as client:
            resp = client.post(
                event["delivery_address"],
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Stigmem-Event-Id": event["id"],
                },
            )

        if resp.status_code == 410:
            # Webhook endpoint gone — cancel the subscription
            with db() as conn:
                conn.execute("DELETE FROM subscriptions WHERE id=?", (event["subscription_id"],))
            logger.info("Subscription %s cancelled (410 Gone)", event["subscription_id"])
            return True

        # 5xx / 429 → retry; 2xx/3xx → success; 4xx (except 429) → permanent failure, don't retry
        if resp.status_code >= 500 or resp.status_code == 429:
            return False
        return resp.status_code < 400

    except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError):
        return False


def _deliver_wake(event: Any, payload: dict[str, Any]) -> bool:
    sanitized = _sanitize_payload(event, payload)
    if sanitized is None:
        return True  # ACL blocked; mark delivered

    # P1 note: wake delivery writes sanitized fact payloads to stderr for
    # operator/platform pickup.  Any process with stderr access sees ALL wake
    # events from ALL subscribers.  This is intentional for the operator
    # integration use-case but means the platform operator is implicitly
    # trusted with the content of every wake-delivered fact.  Operators that
    # need per-subscriber isolation should run one node per subscriber.
    print(
        json.dumps(
            {
                "stigmem_wake": {
                    "event_id": event["id"],
                    "subscription_id": event["subscription_id"],
                    "subscriber_identity": event["subscriber_identity"],
                    "delivery_address": event["delivery_address"],
                    "event_type": event["event_type"],
                    "fact": sanitized,
                    "ts": datetime.now(UTC).isoformat(),
                }
            }
        ),
        file=sys.stderr,
    )
    return True


def _record_result(event: Any, success: bool) -> None:
    now = datetime.now(UTC).isoformat()
    new_attempts = (event["delivery_attempts"] or 0) + 1

    if success:
        with db() as conn:
            conn.execute(
                """UPDATE subscription_events
                   SET delivered_at=?, delivery_status='delivered',
                       delivery_attempts=?, claimed_at=NULL
                   WHERE id=?""",
                (now, new_attempts, event["id"]),
            )
            conn.execute(
                "UPDATE subscriptions SET last_delivered_at=?, consecutive_failures=0 WHERE id=?",
                (now, event["subscription_id"]),
            )
        return

    backoff_s = min(2**new_attempts, 300)
    next_retry = datetime.fromtimestamp(time.time() + backoff_s, UTC).isoformat()

    with db() as conn:
        # Release the claim back to 'pending' so the next sweep can retry it.
        # Circuit-breaker logic below may override to 'failed'.
        conn.execute(
            """UPDATE subscription_events
                  SET delivery_status='pending', claimed_at=NULL,
                      delivery_attempts=?, next_retry_at=?
                WHERE id=?""",
            (new_attempts, next_retry, event["id"]),
        )
        conn.execute(
            "UPDATE subscriptions SET consecutive_failures=consecutive_failures+1 WHERE id=?",
            (event["subscription_id"],),
        )
        sub = conn.execute(
            "SELECT consecutive_failures FROM subscriptions WHERE id=?",
            (event["subscription_id"],),
        ).fetchone()
        threshold = _settings_pkg.settings.subscription_circuit_threshold
        if sub and sub["consecutive_failures"] >= threshold:
            conn.execute(
                "UPDATE subscriptions SET circuit_open=1 WHERE id=?",
                (event["subscription_id"],),
            )
            conn.execute(
                "UPDATE subscription_events SET delivery_status='failed' WHERE id=?",
                (event["id"],),
            )
            logger.warning("Circuit breaker opened for subscription %s", event["subscription_id"])


def _mark_delivered(event_id: str, subscription_id: str) -> None:
    now = datetime.now(UTC).isoformat()
    with db() as conn:
        conn.execute(
            """UPDATE subscription_events
               SET delivered_at=?,
                   delivery_status='delivered',
                   delivery_attempts=delivery_attempts+1,
                   claimed_at=NULL
               WHERE id=?""",
            (now, event_id),
        )
        conn.execute(
            "UPDATE subscriptions SET last_delivered_at=?, consecutive_failures=0 WHERE id=?",
            (now, subscription_id),
        )


# ---------------------------------------------------------------------------
# Background sweep loop
# ---------------------------------------------------------------------------


async def sweep_loop() -> None:
    """Long-running asyncio task: runs deliver_pending() every N seconds."""
    while True:
        await asyncio.sleep(_settings_pkg.settings.subscription_delivery_sweep_s)
        try:
            await asyncio.to_thread(deliver_pending)
        except Exception as exc:
            logger.exception("subscription delivery sweep failed: %s", exc)

```

### node/src/stigmem_node/utility/net_util.py
```
"""Outbound HTTP safety utilities — SSRF guard (H-SEC-1)."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# RFC 1918, loopback, link-local, and IPv6 equivalents.
# Cloud IMDS (169.254.169.254) is covered by 169.254.0.0/16.
_BLOCKED_NETS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


def node_url_is_loopback(node_url: str) -> bool:
    """Return True iff *node_url*'s host is a literal loopback host.

    Shared by the startup bind-safety check and the federation approval-time
    SSRF-skip gate so the loopback host set lives in exactly one place.
    """
    try:
        parsed = urlparse(node_url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return False
    return host in {"localhost", "127.0.0.1", "::1"}


def assert_safe_url(
    url: str,
    *,
    allow_schemes: frozenset[str] = frozenset({"https"}),
) -> None:
    """Raise ValueError if *url* is unsafe to fetch.

    Checks:
    - scheme is in *allow_schemes*
    - hostname resolves (DNS failure → ValueError)
    - no resolved address falls in RFC 1918, loopback, or link-local ranges

    Residual risk: DNS rebinding window between this check and the actual
    connection. Callers MUST also set follow_redirects=False so redirects
    cannot send the connection to a private address after validation.
    """
    parsed = urlparse(url)
    if parsed.scheme not in allow_schemes:
        raise ValueError(f"Disallowed URL scheme: {parsed.scheme!r}")
    hostname = parsed.hostname or ""
    if not hostname:
        raise ValueError(f"URL has no hostname: {url!r}")
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve hostname {hostname!r}: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        for net in _BLOCKED_NETS:
            if ip in net:
                raise ValueError(f"Blocked private/loopback address for {hostname!r}: {ip}")

```
Callers & Entry Points (How public input reaches the modified code)
### node/src/stigmem_node/source_trust.py
```
"""Source-trust score computation — spec §19.4.

Exported surface:
    compute_source_trust(source_uri, scope, identity) -> float
    get_cached_trust(source_uri) -> float | None
    bust_trust_cache(source_uri) -> None
    is_blocklisted(source_uri) -> bool

The score is in [0.0, 1.0].  A source with no computable score defaults to 0.5.
Admin-blocklisted sources always return 0.0.

Per §19.4.4, implementations SHOULD cache per-source trust scores with a TTL of
at least 60 seconds.  We use a simple time-based in-process cache; each worker
process maintains its own cache (acceptable for single-process deployments).
"""

from __future__ import annotations

import logging
import os
import time
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .auth import Identity

logger = logging.getLogger("stigmem.source_trust")

# Cache: { source_uri: (score: float, expires_at: float) }
_TRUST_CACHE: dict[str, tuple[float, float]] = {}
_CACHE_TTL_S: float = 60.0

# Cached cutoff for peer-history lookups. Refreshing this once per cache window
# keeps the rolling 30-day window accurate enough for source-trust scoring
# without recalculating the timestamp on every fresh trust computation.
_PEER_HISTORY_CUTOFF_REFRESH_S: float = 60.0


@lru_cache(maxsize=2)
def _peer_history_cutoff_iso_for_bucket(_bucket: int) -> str:
    from datetime import UTC, datetime, timedelta

    return (datetime.now(UTC) - timedelta(days=30)).isoformat()


def _peer_history_cutoff_iso() -> str:
    refresh_bucket = int(time.monotonic() // _PEER_HISTORY_CUTOFF_REFRESH_S)
    return _peer_history_cutoff_iso_for_bucket(refresh_bucket)


def get_cached_trust(source_uri: str) -> float | None:
    entry = _TRUST_CACHE.get(source_uri)
    if entry is None:
        return None
    score, expires_at = entry
    if time.monotonic() > expires_at:
        del _TRUST_CACHE[source_uri]
        return None
    return score


def _set_cache(source_uri: str, score: float) -> None:
    _TRUST_CACHE[source_uri] = (score, time.monotonic() + _CACHE_TTL_S)


def bust_trust_cache(source_uri: str) -> None:
    _TRUST_CACHE.pop(source_uri, None)


def compute_source_trust(
    source_uri: str,
    scope: str,
    identity: Identity | None = None,
    *,
    identity_strength_override: float | None = None,
) -> float:
    """Return the source-trust score for *source_uri* asserting a fact at *scope*.

    Uses cached value if available (TTL 60 s).  Caches the freshly computed value.
    When *identity_strength_override* is set the cache is bypassed so the
    override is always honoured (spec §19.4.2 capability-token boost).
    """
    if identity_strength_override is None:
        cached = get_cached_trust(source_uri)
        if cached is not None:
            return cached

    score = _compute_fresh(
        source_uri, scope, identity, identity_strength_override=identity_strength_override
    )
    if identity_strength_override is None:
        _set_cache(source_uri, score)
    return score


def _compute_fresh(
    source_uri: str,
    scope: str,
    identity: Identity | None,
    *,
    identity_strength_override: float | None = None,
) -> float:
    from .settings import settings

    trust_mode = settings.trust_mode
    if trust_mode == "off":
        return 0.5  # not computed; return neutral default

    # Check blocklist first — always returns 0.0 regardless (§19.4.5)
    if is_blocklisted(source_uri):
        return 0.0

    # Check auto-rules (operator always_trust / never_trust)
    from .trust_rules import evaluate_auto_rules

    override = evaluate_auto_rules(source_uri, scope)
    if override is not None:
        return override

    w_i = settings.trust_weight_identity
    w_p = settings.trust_weight_peer_history
    w_s = settings.trust_weight_scope_authority
    w_a = settings.trust_weight_attestation_mode

    i_s = (
        identity_strength_override
        if identity_strength_override is not None
        else _identity_strength(source_uri)
    )
    p_h = _peer_history(source_uri)
    s_a = _scope_authority(source_uri, scope, identity)
    a_m = _attestation_mode_factor()

    raw = w_i * i_s + w_p * p_h + w_s * s_a + w_a * a_m
    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------------------
# Component functions (§19.4.2)
# ---------------------------------------------------------------------------


def _identity_strength(source_uri: str) -> float:
    """Score [0,1] measuring how strongly the source is identified."""
    if not source_uri:
        return 0.0

    from .db import db

    with db() as conn:
        # Source has a valid org manifest (§19.1)?
        manifest_row = conn.execute(
            "SELECT log_entry_json FROM federation_manifests WHERE entity_uri = ?",
            (source_uri,),
        ).fetchone()
        if manifest_row is not None:
            has_log_proof = manifest_row["log_entry_json"] is not None
            return 1.0 if has_log_proof else 0.7

        # Source is a registered local API key?
        key_row = conn.execute(
            "SELECT id FROM agent_keys WHERE entity_uri = ? AND status = 'active'",
            (source_uri,),
        ).fetchone()
        if key_row is not None:
            return 0.4

    # Syntactically valid URI (has a scheme)?
    if "://" in source_uri or source_uri.startswith("stigmem:"):
        return 0.1

    return 0.0


def _peer_history(source_uri: str) -> float:
    """Score [0,1] derived from interaction history over the past 30 days."""
    from .db import db

    cutoff = _peer_history_cutoff_iso()

    with db() as conn:
        row = conn.execute(
            """SELECT
                 COUNT(*) AS total,
                 SUM(CASE WHEN attested = 0 THEN 1 ELSE 0 END) AS failures
               FROM facts
               WHERE source = ? AND timestamp >= ?""",
            (source_uri, cutoff),
        ).fetchone()

    if row is None:
        return 0.5  # no history → neutral (§19.4.2)

    total = row["total"] or 0
    failures = row["failures"] or 0

    if total < 10:
        return 0.5  # new source
    failure_rate = failures / total
    if total >= 100 and failure_rate == 0.0:
        return 1.0
    if failure_rate >= 0.05:
        return 0.3
    return 0.7  # ≥ 10 facts, < 5% failures


def _scope_authority(source_uri: str, scope: str, identity: Identity | None) -> float:
    """Score [0,1] measuring whether source has authority to write at this scope."""
    if identity is not None and identity.entity_uri == source_uri and identity.can_write():
        return 0.9

    from .settings import settings

    # Source entity prefix matches node authority
    try:
        from urllib.parse import urlparse

        parsed = urlparse(settings.node_url)
        authority = parsed.netloc or parsed.path
        if source_uri.startswith(f"stigmem://{authority}"):
            return 0.7
    except Exception:
        logger.exception("Failed to parse node_url while scoring source authority")

    # External entity without explicit scope authority
    if scope in ("public", "team"):
        return 0.5  # treat as external with federate-level access

    return 0.2


def _attestation_mode_factor() -> float:
    """Score based on source-attestation mode only when the plugin is enabled."""
    from .settings import settings

    if not _source_attestation_plugin_enabled():
        return 0.2

    mode = settings.source_attestation_mode
    if mode == "enforce":
        return 1.0
    if mode == "warn":
        return 0.6
    return 0.2  # "off"


def _source_attestation_plugin_enabled() -> bool:
    from .plugins import get_registry

    if "stigmem-plugin-source-attestation" not in get_registry().registered_plugins():
        return False
    raw = os.environ.get("STIGMEM_SOURCE_ATTESTATION_ENABLED", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_blocklisted(source_uri: str) -> bool:
    """Return True if source_uri has been admin-blocklisted (peer_history = 0.0 rule)."""
    from .db import db

    with db() as conn:
        row = conn.execute(
            "SELECT id FROM quarantine_rules WHERE rule_type = 'never_trust' AND org_uri = ?",
            (source_uri,),
        ).fetchone()
    return row is not None

```

### node/src/stigmem_node/recall/recall_pipeline.py
```
"""Recall-time processing pipeline — spec §19.4.4, §19.7.

Pipeline order (§19.7.5):
    Storage layer
    → Scope/garden ACL (done in facts.py)
    → Source-trust multiplier applied to effective_confidence  ← here
    → Content sanitizer                                        ← here
    → API response serializer

Exported surface:
    apply_recall_pipeline(records, identity, include_low_trust) -> list[FactRecord]
    run_sanitizer(record) -> FactRecord  (exposed for tests)
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..auth import Identity
    from ..models.facts import FactRecord

logger = logging.getLogger("stigmem.recall")

# ---------------------------------------------------------------------------
# Sentinel patterns (§19.7.2) — compiled once at module load
# ---------------------------------------------------------------------------

_DEFAULT_PATTERNS: list[str] = [
    r"\bignore\s+(all\s+)?previous\s+instructions?\b",
    r"\bdisregard\s+(all\s+)?previous\s+(prompt|instructions?)\b",
    r"\byou\s+are\s+now\s+(?:in\s+)?(?:a\s+)?(?:different|new)\s+mode\b",
    r"\bact\s+as\s+(?:an?\s+)?(?:evil|unfiltered|uncensored|dan\b)",
    r"\bsystem\s+prompt\s*:\s*",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[\/INST\]",
    r"\bHuman:\s*",
    r"\bAssistant:\s*",
    r'\{\s*"__proto__"\s*:',
    r'\{\s*"constructor"\s*:',
]

# Invisible / bidi control characters to strip (§19.7.2)
_BIDI_CONTROLS = frozenset(
    chr(c)
    for c in [
        0x200F,
        0x200E,
        *range(0x202A, 0x202F),
        *range(0x2066, 0x206A),
        *range(0x200B, 0x200E),
        0xFEFF,
    ]
)

# Control characters forbidden in string/text output (§19.7.3)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def _load_compiled_patterns() -> list[re.Pattern[str]]:
    from ..settings import settings

    patterns = list(_DEFAULT_PATTERNS)

    extra_file = settings.sanitizer_extra_patterns_file
    if extra_file:
        try:
            with open(extra_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except FileNotFoundError:
            logger.warning("sanitizer_extra_patterns_file not found: %s", extra_file)
        except Exception as exc:
            logger.error("Failed to read sanitizer_extra_patterns_file: %s", exc)

    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Lazy-load compiled patterns; reset if settings change.
_compiled_patterns: list[re.Pattern[str]] | None = None


def _get_patterns() -> list[re.Pattern[str]]:
    global _compiled_patterns
    if _compiled_patterns is None:
        _compiled_patterns = _load_compiled_patterns()
    return _compiled_patterns


def reset_pattern_cache() -> None:
    global _compiled_patterns
    _compiled_patterns = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_recall_pipeline(
    records: list[FactRecord],
    identity: Identity | None = None,
    include_low_trust: bool = False,
) -> list[FactRecord]:
    """Apply trust multiplier and content sanitizer to a list of FactRecords.

    Returns a filtered/annotated list.  Records that should be fully excluded
    (block mode) are replaced with a placeholder FactRecord with sanitizer_redacted=True.
    """
    from ..settings import settings

    trust_mode = settings.trust_mode
    sanitizer_mode = settings.sanitizer_mode

    if trust_mode == "off":
        sanitizer_mode = "off"

    result: list[FactRecord] = []

    for record in records:
        # Skip quarantined facts from normal recall results (§19.5.2)
        # (rejected facts have confidence=0 and are caught by min_confidence filter)
        if record.quarantine_status == "pending":
            continue

        # 1. Source-trust multiplier (§19.4.4)
        eff_conf = record.confidence
        if trust_mode != "off":
            from ..source_trust import compute_source_trust

            t = compute_source_trust(record.source, record.scope, identity)
            eff_conf = record.confidence * t
            record = record.model_copy(update={"effective_confidence": eff_conf, "source_trust": t})

            # In strict mode, filter facts below 0.3 effective confidence unless
            # caller opts in (§19.4.4). In relaxed mode, MUST NOT filter based
            # solely on a low score (§19.4.3).
            if trust_mode == "strict" and eff_conf < 0.3 and not include_low_trust:
                continue

        # 2. Content sanitizer (§19.7)
        if sanitizer_mode != "off":
            record = _run_sanitizer(record, sanitizer_mode, eff_conf)

        result.append(record)

    return result


def _run_sanitizer(record: FactRecord, mode: str, effective_confidence: float) -> FactRecord:
    """Run content sanitizer on one fact record.  Returns possibly-modified record."""
    from ..models.facts import FactValue

    value = record.value
    if value.type not in ("string", "text"):
        # Schema type enforcement for non-string types (§19.7.3)
        return _enforce_schema_types(record)

    # Normalize to NFKC, strip bidi controls (§19.7.2)
    raw_v = str(value.v) if value.v is not None else ""
    normalized = unicodedata.normalize("NFKC", raw_v)
    stripped = "".join(c for c in normalized if c not in _BIDI_CONTROLS)
    # Strip control chars (§19.7.3)
    cleaned = _CONTROL_CHARS_RE.sub("", stripped)

    # Pattern matching
    matched_patterns: list[str] = []
    for pat in _get_patterns():
        if pat.search(cleaned):
            matched_patterns.append(pat.pattern)

    if not matched_patterns:
        # No sentinel match; apply cleaned value if content was modified
        if cleaned != raw_v:
            return record.model_copy(update={"value": FactValue(type=value.type, v=cleaned)})
        return record

    # Sentinel matched — apply enforcement mode
    if mode == "warn":
        return record.model_copy(
            update={
                "sanitizer_warnings": matched_patterns,
                "value": FactValue(type=value.type, v=cleaned),
            }
        )

    if mode == "block":
        logger.debug("Sanitizer blocked fact %s (matched: %s)", record.id, matched_patterns[0])
        return record.model_copy(
            update={
                "sanitizer_redacted": True,
                "sanitizer_warnings": matched_patterns,
                "value": FactValue(type=value.type, v=None),
            }
        )

    if mode == "quarantine":
        _quarantine_via_sanitizer(record.id, matched_patterns[0])
        logger.info("Sanitizer quarantined fact %s", record.id)
        # Return redacted record for this response
        return record.model_copy(
            update={
                "sanitizer_redacted": True,
                "sanitizer_warnings": matched_patterns,
                "value": FactValue(type=value.type, v=None),
            }
        )

    return record


def _enforce_schema_types(record: FactRecord) -> FactRecord:
    """Enforce schema correctness for non-string FactValue types (§19.7.3)."""
    import math

    from ..models.facts import FactValue

    v = record.value

    if v.type == "number" and (
        v.v is None or (isinstance(v.v, float) and (math.isnan(v.v) or math.isinf(v.v)))
    ):
        return record.model_copy(
            update={"value": FactValue(type="number", v=None), "sanitizer_redacted": True}
        )

    if v.type == "ref":
        raw = str(v.v) if v.v is not None else ""
        if "://" not in raw and not raw.startswith("urn:"):
            return record.model_copy(
                update={"value": FactValue(type="ref", v=None), "sanitizer_redacted": True}
            )

    return record


def _quarantine_via_sanitizer(fact_id: str, matched_pattern: str) -> None:
    """Move a fact to the node's quarantine garden (sanitizer quarantine mode)."""
    from datetime import UTC, datetime

    from ..db import db
    from ..lifecycle.immutability import set_fact_quarantine_status
    from ..observability.audit_event import (
        INSTRUCTION_QUARANTINED,
        emit_instruction_event_if_applicable,
    )
    from ..settings import settings

    qg_id = settings.quarantine_garden_id
    if not qg_id:
        logger.warning(
            "Sanitizer quarantine mode set but quarantine_garden_id not configured; "
            "fact %s will not be quarantined",
            fact_id,
        )
        return

    now = datetime.now(UTC).isoformat()

    try:
        with db() as conn:
            # Resolve garden UUID
            qg_row = conn.execute(
                "SELECT id FROM gardens WHERE (id = ? OR slug = ?) AND quarantine = 1",
                (qg_id, qg_id),
            ).fetchone()
            if qg_row is None:
                logger.warning(
                    "Quarantine garden %s not found; skipping sanitizer quarantine", qg_id
                )
                return
            fact_row = conn.execute(
                "SELECT entity, relation FROM facts WHERE id = ?",
                (fact_id,),
            ).fetchone()

            set_fact_quarantine_status(
                conn,
                fact_id=fact_id,
                quarantine_garden_id=qg_row["id"],
                quarantine_status="pending",
                quarantine_reason=f"sanitizer: {matched_pattern}",
            )

            # Audit (§19.7.6)
            import uuid

            audit_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO fact_audit_log
                   (id, fact_id, event_type, entity_uri, oidc_sub, source, attested_key_id, ts)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    audit_id,
                    fact_id,
                    "sanitizer_quarantine",
                    "system:stigmem",
                    None,
                    "system:stigmem",
                    None,
                    now,
                ),
            )
            emit_instruction_event_if_applicable(
                INSTRUCTION_QUARANTINED,
                fact_id=fact_id,
                fact_entity=fact_row["entity"] if fact_row is not None else None,
                fact_relation=fact_row["relation"] if fact_row is not None else None,
                actor_uri="system:stigmem",
                source="system:stigmem",
                detail={
                    "reason": "sanitizer_quarantine",
                    "matched_pattern": matched_pattern,
                },
                conn=conn,
            )
    except Exception as exc:
        logger.error("Failed to quarantine fact %s via sanitizer: %s", fact_id, exc)

```

### node/src/stigmem_node/cli_admin_handlers.py
```
"""Admin / migration / audit CLI handlers extracted from cli.py.

These handlers are imported back into ``stigmem_node.cli`` so that the public
import surface (``from stigmem_node.cli import _cmd_backfill_cids`` etc.) is
preserved.  No behavioural changes — code was moved verbatim from cli.py.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logger = logging.getLogger("stigmem.cli")


def _write_owner_only_text(path: str, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
        file_obj = os.fdopen(fd, "w")
        fd = -1
        with file_obj as f:
            f.write(text)
    finally:
        if fd != -1:
            os.close(fd)
    os.chmod(path, 0o600)


def _resolve_scope_prefix_and_label(
    args: argparse.Namespace,
    deployment: str,
    agent_id: str,
) -> tuple[str, str]:
    """Pick the role/skill scope-prefix builder and produce a human-readable label."""
    from .instruction_migrate import scope_prefix_for_role, scope_prefix_for_skill

    if args.role:
        return scope_prefix_for_role(deployment, agent_id), f"role:{args.role}  agent:{agent_id}"
    return scope_prefix_for_skill(deployment, args.skill), f"skill:{args.skill}  agent:{agent_id}"


def _load_existing_state_from_db(
    db_path: str,
    stub_diff_uris: set[str],
    agent_id: str,
) -> tuple[dict[str, str], set[str]]:
    """Best-effort: read existing fact values + prior manifest entry names from local SQLite."""
    import json as _json
    import sqlite3

    existing_content: dict[str, str] = {}
    prev_names: set[str] = set()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        for uri in stub_diff_uris:
            row = conn.execute(
                "SELECT value_v FROM facts WHERE entity = ? ORDER BY timestamp DESC LIMIT 1",
                (uri,),
            ).fetchone()
            if row:
                existing_content[uri] = str(row["value_v"])
        row = conn.execute(
            "SELECT body FROM instruction_manifests"
            " WHERE agent_id = ? AND superseded_at IS NULL"
            " ORDER BY created_at DESC LIMIT 1",
            (agent_id,),
        ).fetchone()
        if row:
            prev_names = {e["name"] for e in _json.loads(row["body"])}
        conn.close()
    except Exception as exc:
        print(f"warning: db query failed: {exc}", file=sys.stderr)
    return existing_content, prev_names


def _load_existing_state_from_api(
    node_url: str,
    api_key: str,
    stub_diff_uris: set[str],
    agent_id: str,
) -> tuple[dict[str, str], set[str]]:
    """Best-effort: fetch existing facts + manifest entries via HTTP."""
    try:
        import httpx
    except ImportError:
        print("warning: httpx not installed — skipping idempotency checks", file=sys.stderr)
        return {}, set()

    existing_content: dict[str, str] = {}
    prev_names: set[str] = set()
    headers = {"Authorization": f"Bearer {api_key}"}
    base = node_url.rstrip("/")

    for uri in stub_diff_uris:
        try:
            r = httpx.get(
                f"{base}/v1/facts",
                params={"entity": uri, "limit": 1},
                headers=headers,
                timeout=10.0,
            )
            if r.status_code == 200:
                facts = r.json().get("facts", [])
                if facts:
                    existing_content[uri] = str(facts[0]["value"]["v"])
        except Exception as exc:  # nosec B110 — best-effort pre-flight
            logger.debug("instruction migrate pre-flight fact fetch failed: %s", exc)
    try:
        r = httpx.get(
            f"{base}/v1/agents/{agent_id}/instruction-manifest",
            headers=headers,
            timeout=10.0,
        )
        if r.status_code == 200:
            prev_names = {e["name"] for e in r.json().get("entries", [])}
    except Exception as exc:  # nosec B110 — best-effort pre-flight
        logger.debug("instruction migrate pre-flight manifest fetch failed: %s", exc)
    return existing_content, prev_names


def _load_existing_state(
    args: argparse.Namespace,
    node_url: str,
    api_key: str,
    stub_diff_uris: set[str],
    agent_id: str,
) -> tuple[dict[str, str], set[str]]:
    """Dispatch to the DB-backed or HTTP-backed pre-flight loader, or return empty."""
    if args.db:
        return _load_existing_state_from_db(args.db, stub_diff_uris, agent_id)
    if api_key:
        return _load_existing_state_from_api(node_url, api_key, stub_diff_uris, agent_id)
    return {}, set()


def _confirm_proceed() -> bool:
    """Interactive [y/N] confirmation. Returns False on abort or non-y answer."""
    try:
        answer = input("Proceed? [y/N] ")
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return False
    if answer.lower() not in ("y", "yes"):
        print("Aborted.")
        return False
    return True


def _cmd_instruction_migrate(args: argparse.Namespace) -> int:
    """Migrate markdown instruction files to stigmem facts and publish manifest."""
    import os
    import time
    from pathlib import Path

    from .instruction_migrate import (
        build_fact_uri,
        compute_diff,
        format_preview,
        parse_instruction_chunks,
        publish_manifest,
        write_facts,
    )

    path = Path(args.path)
    if not path.exists():
        print(f"error: path '{args.path}' does not exist", file=sys.stderr)
        return 1

    api_key = args.api_key or os.environ.get("STIGMEM_API_KEY", "")
    node_url = args.node_url
    deployment = args.deployment
    version = args.version
    agent_id = args.agent_id

    scope_prefix, scope_label = _resolve_scope_prefix_and_label(args, deployment, agent_id)

    chunks = parse_instruction_chunks(path)
    if not chunks:
        print(
            "No instruction chunks found. Check that the path contains .md files.",
            file=sys.stderr,
        )
        return 0

    # Idempotency pre-flight: load existing fact content + prior manifest entry names.
    stub_diff_uris = {build_fact_uri(scope_prefix, c.slug, version) for c in chunks}
    existing_content, prev_names = _load_existing_state(
        args,
        node_url,
        api_key,
        stub_diff_uris,
        agent_id,
    )

    diff = compute_diff(chunks, scope_prefix, version, existing_content, prev_names)
    print(format_preview(diff, scope_label, path, version))

    if args.dry_run:
        print("Dry-run mode — no changes written.")
        return 0

    work = [d for d in diff if d.action in ("CREATE", "UPDATE", "TOMBSTONE")]
    if not work:
        print("Nothing to do.")
        return 0

    if not args.yes and not _confirm_proceed():
        return 1

    if not api_key:
        print(
            "error: --api-key or STIGMEM_API_KEY env var required to write facts",
            file=sys.stderr,
        )
        return 1

    written, failed = write_facts(diff, node_url, api_key)
    if failed > 0:
        print(
            f"\n{failed} fact(s) failed to write. Manifest will NOT be published.",
            file=sys.stderr,
        )
        return 1

    # Unique manifest version per run (timestamp suffix)
    manifest_version = f"{version}-{int(time.time())}"
    if not publish_manifest(agent_id, diff, manifest_version, node_url, api_key):
        return 1

    print(f"\nDone. {written} fact(s) written, manifest published as version '{manifest_version}'.")
    print(f"Verify: stigmem recall-instruction via POST /v1/agents/{agent_id}/recall-instruction")
    return 0


def _cmd_instruction_manifest_generate(args: argparse.Namespace) -> int:
    """Generate an instruction manifest JSON from a directory of markdown files."""
    import json
    import re
    from pathlib import Path

    path = Path(args.path)
    if not path.is_dir():
        print(f"error: '{args.path}' is not a directory", file=sys.stderr)
        return 1

    entries = []
    md_files = sorted(path.glob("*.md")) + sorted(path.glob("**/*.md"))

    for md_file in md_files:
        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"warning: skipping {md_file}: {exc}", file=sys.stderr)
            continue

        # Split at H2/H3 boundaries
        sections = re.split(r"(?m)^(#{2,3}\s+.+)$", text)

        # Merge heading with following content
        chunks: list[tuple[str, str]] = []
        i = 0
        while i < len(sections):
            if re.match(r"^#{2,3}\s+", sections[i].strip()):
                heading = sections[i].strip()
                body = sections[i + 1].strip() if i + 1 < len(sections) else ""
                chunks.append((heading, body))
                i += 2
            else:
                if sections[i].strip():
                    chunks.append(
                        ("# " + md_file.stem.replace("-", " ").title(), sections[i].strip())
                    )
                i += 1

        if not chunks:
            chunks = [("# " + md_file.stem.replace("-", " ").title(), text.strip())]

        for heading, body in chunks:
            heading_text = re.sub(r"^#{2,3}\s+", "", heading).strip()
            slug = re.sub(r"[^a-z0-9]+", "-", heading_text.lower()).strip("-")
            if not slug:
                slug = md_file.stem
            unit_name = f"{md_file.stem}-{slug}" if md_file.stem not in slug else slug

            keywords = list(
                {
                    w.lower()
                    for w in re.findall(r"\b[a-zA-Z]{4,}\b", heading_text + " " + body[:200])
                }
            )[:8]
            token_est = max(1, len(body) // 4)
            fact_uri = (
                f"instruction:{args.deployment}/agent/{args.agent_id}/{unit_name}/{args.version}"
            )

            entries.append(
                {
                    "name": unit_name,
                    "description": heading_text[:120],
                    "required_by_task_types": [],
                    "guarantee_load": False,
                    "load_triggers": {
                        "intents": [heading_text.lower()],
                        "keywords": keywords,
                        "task_types": [],
                    },
                    "fact_uri": fact_uri,
                    "path": str(md_file),
                    "token_estimate": token_est,
                }
            )

    result = {
        "version": args.version,
        "agent_id": args.agent_id,
        "deployment": args.deployment,
        "generated_from": str(path),
        "entries": entries,
    }
    output = json.dumps(result, indent=2)

    if args.out:
        _write_owner_only_text(args.out, output)
        print(f"Wrote {len(entries)} entries to {args.out}")
    else:
        print(output)

    return 0


def _cmd_audit_discovery(args: argparse.Namespace) -> int:
    """Print discovery audit metrics from the local database."""
    import json
    import sqlite3
    from datetime import UTC, datetime, timedelta

    from .settings import settings

    db_path = args.db or settings.db_path

    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
        except ValueError:
            print(f"error: invalid --since date: {args.since}", file=sys.stderr)
            return 1
    else:
        since_dt = datetime.now(UTC) - timedelta(days=7)
    since_ms = int(since_dt.timestamp() * 1000)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except Exception as exc:
        print(f"error: cannot open database {db_path}: {exc}", file=sys.stderr)
        return 1

    agent_filter = args.agent
    rows = conn.execute(
        "SELECT * FROM instruction_audit WHERE agent_id LIKE ? AND session_start >= ?",
        (f"%{agent_filter}%", since_ms),
    ).fetchall()

    if not rows:
        pr
... [truncated]
```

### node/src/stigmem_node/fact_chain.py
```
"""ADR-016 L4 local hash chain for fact insert sequence integrity."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

_HASH_PREFIX = "sha256:"
_CHECKPOINT_PAYLOAD_KIND = "stigmem.fact_chain_checkpoint"
_CHECKPOINT_PAYLOAD_VERSION = 1


@dataclass(frozen=True)
class FactChainVerification:
    """Result of verifying a tenant's local fact chain."""

    valid: bool
    checked_entries: int
    mismatch_reason: str | None = None
    fact_id: str | None = None
    chain_seq: int | None = None


class FactChainIntegrityError(ValueError):
    """Raised when a fact chain cannot be verified."""

    def __init__(self, result: FactChainVerification) -> None:
        super().__init__(result.mismatch_reason or "fact_chain_invalid")
        self.result = result


def _sha256_json(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"{_HASH_PREFIX}{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def compute_fact_chain_event_hash(row: Any) -> str:
    """Hash the fact fields that define the local insert event."""
    return _sha256_json(
        {
            "cid": row["cid"],
            "confidence": float(row["confidence"]),
            "entity": row["entity"],
            "fact_id": row["id"],
            "relation": row["relation"],
            "scope": row["scope"],
            "source": row["source"],
            "tenant_id": row["tenant_id"],
            "value_type": row["value_type"],
            "value_v": row["value_v"] or "",
        }
    )


def compute_fact_chain_hash(
    *,
    tenant_id: str,
    chain_seq: int,
    fact_id: str,
    event_hash: str,
    previous_hash: str | None,
    created_at: str,
) -> str:
    """Hash one chain link from its event hash and predecessor."""
    return _sha256_json(
        {
            "chain_seq": chain_seq,
            "created_at": created_at,
            "event_hash": event_hash,
            "fact_id": fact_id,
            "previous_hash": previous_hash,
            "tenant_id": tenant_id,
        }
    )


def append_fact_chain_entry(conn: Any, row: Any) -> None:
    """Append a local L4 chain entry for a newly inserted fact row."""
    tenant_id = row["tenant_id"]
    existing = conn.execute(
        "SELECT 1 FROM fact_chain WHERE tenant_id = ? AND fact_id = ?",
        (tenant_id, row["id"]),
    ).fetchone()
    if existing is not None:
        return

    previous = conn.execute(
        "SELECT chain_seq, chain_hash FROM fact_chain "
        "WHERE tenant_id = ? ORDER BY chain_seq DESC LIMIT 1",
        (tenant_id,),
    ).fetchone()
    chain_seq = 1 if previous is None else int(previous["chain_seq"]) + 1
    previous_hash = None if previous is None else previous["chain_hash"]
    event_hash = compute_fact_chain_event_hash(row)
    created_at = datetime.now(UTC).isoformat()
    chain_hash = compute_fact_chain_hash(
        tenant_id=tenant_id,
        chain_seq=chain_seq,
        fact_id=row["id"],
        event_hash=event_hash,
        previous_hash=previous_hash,
        created_at=created_at,
    )
    conn.execute(
        """
        INSERT INTO fact_chain
            (id, tenant_id, chain_seq, fact_id, event_hash, previous_hash, chain_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"chain_{uuid.uuid4().hex}",
            tenant_id,
            chain_seq,
            row["id"],
            event_hash,
            previous_hash,
            chain_hash,
            created_at,
        ),
    )
    submit_due_fact_chain_checkpoints(conn, tenant_id=tenant_id)


def verify_fact_chain(conn: Any, tenant_id: str = "default") -> FactChainVerification:
    """Verify chain sequence, fact event hashes, and link hashes for one tenant."""
    rows = conn.execute(
        """
        SELECT
            fc.*,
            f.id AS stored_fact_id,
            f.entity,
            f.relation,
            f.value_type,
            f.value_v,
            f.source,
            f.confidence,
            f.scope,
            f.tenant_id AS fact_tenant_id,
            f.cid
        FROM fact_chain fc
        LEFT JOIN facts f ON f.id = fc.fact_id AND f.tenant_id = fc.tenant_id
        WHERE fc.tenant_id = ?
        ORDER BY fc.chain_seq ASC
        """,
        (tenant_id,),
    ).fetchall()

    previous_hash: str | None = None
    expected_seq = 1
    for row in rows:
        chain_seq = int(row["chain_seq"])
        if chain_seq != expected_seq:
            return FactChainVerification(
                valid=False,
                checked_entries=expected_seq - 1,
                mismatch_reason="chain_seq_gap",
                fact_id=row["fact_id"],
                chain_seq=chain_seq,
            )
        if row["previous_hash"] != previous_hash:
            return FactChainVerification(
                valid=False,
                checked_entries=expected_seq - 1,
                mismatch_reason="previous_hash_mismatch",
                fact_id=row["fact_id"],
                chain_seq=chain_seq,
            )
        if row["stored_fact_id"] is None:
            return FactChainVerification(
                valid=False,
                checked_entries=expected_seq - 1,
                mismatch_reason="fact_missing",
                fact_id=row["fact_id"],
                chain_seq=chain_seq,
            )

        fact_row = {
            "cid": row["cid"],
            "confidence": row["confidence"],
            "entity": row["entity"],
            "id": row["fact_id"],
            "relation": row["relation"],
            "scope": row["scope"],
            "source": row["source"],
            "tenant_id": row["fact_tenant_id"],
            "value_type": row["value_type"],
            "value_v": row["value_v"],
        }
        expected_event_hash = compute_fact_chain_event_hash(fact_row)
        if row["event_hash"] != expected_event_hash:
            return FactChainVerification(
                valid=False,
                checked_entries=expected_seq - 1,
                mismatch_reason="event_hash_mismatch",
                fact_id=row["fact_id"],
                chain_seq=chain_seq,
            )

        expected_chain_hash = compute_fact_chain_hash(
            tenant_id=row["tenant_id"],
            chain_seq=chain_seq,
            fact_id=row["fact_id"],
            event_hash=row["event_hash"],
            previous_hash=row["previous_hash"],
            created_at=row["created_at"],
        )
        if row["chain_hash"] != expected_chain_hash:
            return FactChainVerification(
                valid=False,
                checked_entries=expected_seq - 1,
                mismatch_reason="chain_hash_mismatch",
                fact_id=row["fact_id"],
                chain_seq=chain_seq,
            )

        previous_hash = row["chain_hash"]
        expected_seq += 1

    return FactChainVerification(valid=True, checked_entries=len(rows))


def build_fact_chain_proof(conn: Any, tenant_id: str = "default") -> dict[str, Any]:
    """Return a compact proof over the current tenant-local chain head."""
    verification = verify_fact_chain(conn, tenant_id=tenant_id)
    if not verification.valid:
        raise FactChainIntegrityError(verification)
    head = conn.execute(
        "SELECT chain_hash FROM fact_chain WHERE tenant_id = ? ORDER BY chain_seq DESC LIMIT 1",
        (tenant_id,),
    ).fetchone()
    return {
        "tenant_id": tenant_id,
        "checked_entries": verification.checked_entries,
        "head_hash": None if head is None else head["chain_hash"],
        "checkpoint": latest_fact_chain_checkpoint(conn, tenant_id=tenant_id),
    }


def _json_dumps(body: dict[str, Any]) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _row_to_checkpoint(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "covered_chain_seq": int(row["covered_chain_seq"]),
        "chain_hash": row["chain_hash"],
        "status": row["status"],
        "attempt_count": int(row["attempt_count"]),
        "created_at": row["created_at"],
        "submitted_at": row["submitted_at"],
        "last_error": row["last_error"],
        "tl_backend": row["tl_backend"],
        "tl_log_id": row["tl_log_id"],
        "tl_leaf_hash": row["tl_leaf_hash"],
        "tl_log_index": row["tl_log_index"],
        "tl_integrated_time": row["tl_integrated_time"],
        "tl_inclusion_proof": json.loads(row["tl_inclusion_proof"] or "{}"),
        "tl_raw": json.loads(row["tl_raw"] or "{}"),
    }


def _checkpoint_payload(row: Any, created_at: str) -> dict[str, Any]:
    return {
        "kind": _CHECKPOINT_PAYLOAD_KIND,
        "version": _CHECKPOINT_PAYLOAD_VERSION,
        "tenant_id": row["tenant_id"],
        "covered_chain_seq": int(row["chain_seq"]),
        "chain_hash": row["chain_hash"],
        "created_at": created_at,
    }


def _latest_checkpoint_row(conn: Any, tenant_id: str) -> Any | None:
    return conn.execute(
        """
        SELECT *
        FROM fact_chain_checkpoints
        WHERE tenant_id = ?
        ORDER BY covered_chain_seq DESC
        LIMIT 1
        """,
        (tenant_id,),
    ).fetchone()


def latest_fact_chain_checkpoint(conn: Any, tenant_id: str = "default") -> dict[str, Any] | None:
    """Return the latest local L5 checkpoint metadata for a tenant."""
    row = _latest_checkpoint_row(conn, tenant_id)
    return None if row is None else _row_to_checkpoint(row)


def _next_pending_checkpoint(conn: Any, tenant_id: str, now: datetime) -> Any | None:
    return conn.execute(
        """
        SELECT *
        FROM fact_chain_checkpoints
        WHERE tenant_id = ?
          AND status = 'pending'
          AND (next_retry_at IS NULL OR next_retry_at <= ?)
        ORDER BY covered_chain_seq ASC
        LIMIT 1
        """,
        (tenant_id, now.isoformat()),
    ).fetchone()


def _submit_checkpoint_row(conn: Any, row: Any, now: datetime) -> None:
    from .identity.transparency_log import make_transparency_log
    from .settings import settings

    attempt_count = int(row["attempt_count"]) + 1
    try:
        entry = make_transparency_log().submit(json.loads(row["payload"]))
    except Exception as exc:
        retry_s = max(1, settings.fact_chain_checkpoint_retry_s)
        next_retry_at = (now + timedelta(seconds=retry_s)).isoformat()
        conn.execute(
            """
            UPDATE fact_chain_checkpoints
            SET attempt_count = ?,
                next_retry_at = ?,
                last_error = ?,
                status = 'pending'
            WHERE id = ?
            """,
            (attempt_count, next_retry_at, str(exc), row["id"]),
        )
        return

    conn.execute(
        """
        UPDATE fact_chain_checkpoints
        SET status = 'submitted',
            attempt_count = ?,
            submitted_at = ?,
            next_retry_at = NULL,
            last_error = NULL,
            tl_log_id = ?,
            tl_leaf_hash = ?,
            tl_log_index = ?,
            tl_integrated_time = ?,
            tl_inclusion_proof = ?,
            tl_raw = ?
        WHERE id = ?
        """,
        (
            attempt_count,
            now.isoformat(),
            entry.log_id,
            entry.leaf_hash,
            entry.log_index,
            entry.integrated_time,
            _json_dumps(entry.inclusion_proof),
            _json_dumps(entry.raw),
            row["id"],
        ),
    )


def _checkpoint_due(conn: Any, tenant_id: str, head: Any, now: datetime) -> bool:

... [truncated]
```

### node/src/stigmem_node/routes/_facts_assert.py
```
"""Implementation of POST /v1/facts (assert_fact) extracted from routes/facts.py.

Imported back into ``routes.facts``; the route stub there delegates to this
function inside its tracing span.  Helper symbols are imported lazily inside
the function to keep the module-level import graph acyclic.
No behavioural changes — code was moved verbatim from facts.py.
"""

from __future__ import annotations

import logging
import sys
import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from ..auth import Identity
from ..billing import BillingEvent, get_hook_bus
from ..cid import compute_cid
from ..db import db
from ..entity_normalizer import NormalizationError, is_informal, normalize_entity_uri
from ..garden_acl import (
    get_garden_by_garden_uri,
    require_garden_write,
)
from ..hlc import node_hlc
from ..lifecycle.immutability import set_embedding_status, write_fact_journal
from ..metrics import CONTRADICTION, FACT_WRITE
from ..models.facts import AssertRequest, FactRecord, row_to_record
from ..plugins import TenantContext, get_registry
from ..recall.fuzzy_resolver import resolve_entity
from ..session_graph import encode_derived_from, ensure_write_allowed, record_write_scope
from ..settings import settings as _settings  # noqa: F401  — kept for parity


def _live_settings() -> Any:
    """Return the live Settings singleton.

    Uses sys.modules directly because some test fixtures replace
    `stigmem_node.settings` (the module attribute on the parent package) with
    a Settings instance. `from .. import settings` and `import x.y` both go
    through that patched attribute and would return the instance instead of
    the module — sys.modules['stigmem_node.settings'] is the only path that
    reliably reaches the original module so we can read its `.settings`
    singleton (which IS what tests intend to swap).
    """
    return sys.modules["stigmem_node.settings"].settings


logger = logging.getLogger("stigmem.facts")


def _verify_or_require_attestation(req: AssertRequest, identity: Identity) -> str | None:
    """C1: verify the attestation token (when supplied) or fail-closed if required."""
    from .facts import _encode_v

    if req.attestation is not None:
        from .agent_keys import verify_attestation

        value_v_for_sig = _encode_v(req.value.type, req.value.v)
        canonical = (
            f"{req.entity}\n{req.relation}\n{req.value.type}\n{value_v_for_sig}\n{req.source}"
        ).encode()
        return verify_attestation(
            key_id=req.attestation.key_id,
            signature_b64=req.attestation.signature,
            canonical_message=canonical,
            caller_entity_uri=identity.entity_uri,
        )
    if _live_settings().attestation_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="attestation required; register an agent key at POST /v1/auth/agent-keys",
        )
    return None


def _normalise_and_alias_uris(req: AssertRequest, tenant_id: str) -> tuple[str, str]:
    """Layer-1 strict normalisation + Layer-2 alias lookup. Emits deprecation warnings."""
    try:
        entity = normalize_entity_uri(req.entity)
        source = normalize_entity_uri(req.source)
    except NormalizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid_entity_uri: {exc}",
        ) from exc

    # Deprecation warning for informal URIs (spec §2.5)
    if is_informal(req.entity):
        print(
            f"[stigmem] DEPRECATED: informal entity URI {req.entity!r} — "
            f"use stigmem://authority/type/id format (spec §2.5)",
            file=sys.stderr,
        )
    if is_informal(req.source):
        print(
            f"[stigmem] DEPRECATED: informal source URI {req.source!r} — "
            f"use stigmem://authority/type/id format (spec §2.5)",
            file=sys.stderr,
        )

    # Layer 2: resolve user-defined semantic aliases (spec §2.6.6) on canonical
    # forms, scoped to the caller's tenant.
    with db() as _alias_conn:
        return (
            resolve_entity(_alias_conn, entity, tenant_id),
            resolve_entity(_alias_conn, source, tenant_id),
        )


def _resolve_garden_for_assert(req: AssertRequest, identity: Identity) -> Any:
    """Spec §17.3: resolve garden_id, enforce scope match + write ACL. Returns row or None."""
    if req.garden_id is None:
        return None
    garden = get_garden_by_garden_uri(req.garden_id, tenant_id=identity.tenant_id)
    if garden is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="garden not found")
    if garden["scope"] != req.scope:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"scope mismatch: garden scope is '{garden['scope']}' "
                f"but fact scope is '{req.scope}'"
            ),
        )
    require_garden_write(garden, identity)
    return garden


def _existing_record_for_cid(
    conn: Any,
    fact_cid: str,
    tenant_id: str,
) -> FactRecord | None:
    """Return the existing record for ``fact_cid``, or None when no alias exists yet."""
    existing_alias = conn.execute(
        "SELECT fact_id FROM fact_cid_aliases WHERE cid = ?", (fact_cid,)
    ).fetchone()
    if existing_alias is None:
        return None
    existing_row = conn.execute(
        "SELECT * FROM facts WHERE id = ? AND tenant_id = ?",
        (existing_alias["fact_id"], tenant_id),
    ).fetchone()
    return row_to_record(existing_row, contradicted=False) if existing_row is not None else None


def _require_interpretation_write(identity: Identity, interpret_as: str) -> None:
    if interpret_as != "instruction":
        return
    if identity.can_write_instruction():
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "instruction_write_required",
            "message": "writing instruction-typed facts requires instruction:write permission",
        },
    )


def _detect_and_record_contradictions(
    conn: Any,
    fact_id: str,
    entity: str,
    req: AssertRequest,
    identity: Identity,
) -> bool:
    """Spec §9.1: skip system facts; else find siblings sharing (entity, relation, scope)."""
    from .facts import _SYSTEM_RELATION_PREFIX, _record_contradictions

    is_system = (
        entity.startswith(_SYSTEM_RELATION_PREFIX) and not entity.startswith("stigmem://")
    ) or (
        req.relation.startswith(_SYSTEM_RELATION_PREFIX)
        and not req.relation.startswith("stigmem://")
    )
    if is_system:
        return False
    siblings = conn.execute(
        """SELECT id FROM facts
           WHERE entity=? AND relation=? AND scope=? AND id!=? AND confidence>0.0
             AND tenant_id=?""",
        (entity, req.relation, req.scope, fact_id, identity.tenant_id),
    ).fetchall()
    if not siblings:
        return False
    _record_contradictions(
        conn,
        fact_id,
        entity,
        req.relation,
        req.scope,
        siblings,
        identity.tenant_id,
    )
    print(
        f"[stigmem] WARN: collision — entity={entity!r} relation={req.relation!r} "
        f"scope={req.scope!r}: fact {fact_id!r} contradicts {len(siblings)} existing "
        f"fact(s); verify relation namespacing (see relation-convention.md)",
        file=sys.stderr,
    )
    return True


def _emit_post_write_hooks(
    *,
    fact_id: str,
    entity: str,
    source: str,
    req: AssertRequest,
    identity: Identity,
    value_v: str | None,
    garden_uuid: str | None,
    now: str,
    contradicted: bool,
    _span: object,
) -> None:
    """Card-stale + background embed + billing + subscription fan-out + metrics + span attrs."""
    from .facts import _embed_fact_background

    # Phase 9: mark entity's memory card stale on every write (ACM-214)
    try:
        from ..card_materializer import mark_entity_stale as _mark_stale

        _mark_stale(entity, req.scope, identity.tenant_id)
    except Exception as _card_exc:
        logger.warning("card mark_stale failed for %r: %s", entity, _card_exc)

    # Phase 9 §2: write-time embedding (background thread, graceful fallback)
    if _live_settings().embed_enabled:
        threading.Thread(
            target=_embed_fact_background,
            args=(fact_id, entity, req.relation, req.value.type, value_v or ""),
            daemon=True,
        ).start()

    get_hook_bus().emit(
        BillingEvent(
            event_type="fact_written",
            tenant_id=identity.tenant_id,
            entity_uri=identity.entity_uri,
            fact_id=fact_id,
        )
    )

    # §20: fan out to subscribers (fast DB insert only; delivery happens in sweep loop)
    try:
        import json as _json

        from ..subscription_delivery import fan_out as _subscription_fan_out

        _subscription_fan_out(
            fact_id=fact_id,
            entity=entity,
            scope=req.scope,
            garden_id=garden_uuid,
            tenant_id=identity.tenant_id,
            fact_payload_json=_json.dumps(
                {
                    "id": fact_id,
                    "entity": entity,
                    "relation": req.relation,
                    "value_type": req.value.type,
                    "value_v": value_v,
                    "source": source,
                    "timestamp": now,
                    "scope": req.scope,
                    "confidence": req.confidence,
                    "garden_id": garden_uuid,
                }
            ),
        )
    except Exception as _sub_exc:
        print(f"[stigmem] WARN: subscription fan_out failed: {_sub_exc}", file=sys.stderr)

    FACT_WRITE.labels(principal=identity.entity_uri, tenant=identity.tenant_id).inc()
    if contradicted:
        CONTRADICTION.labels(tenant=identity.tenant_id).inc()
    try:
        _span.set_attribute("stigmem.fact_id", fact_id)  # type: ignore[attr-defined]
        _span.set_attribute("stigmem.contradicted", contradicted)  # type: ignore[attr-defined]
    except AttributeError as _span_exc:
        logger.debug("span attribute set skipped: %s", _span_exc)


def assert_fact_impl(
    req: AssertRequest,
    identity: Identity,
    _span: object,
    *,
    request_id: str,
    tenant: TenantContext,
    session_id: str | None = None,
) -> FactRecord:
    # Lazy imports of sibling helpers to avoid circular import with .facts
    from .facts import (
        _encode_v,
        _is_valid_entity_uri,
        _validate_relation,
    )

    if not identity.can_write():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="write permission required",
        )

    attested_key_id = _verify_or_require_attestation(req, identity)
    entity, source = _normalise_and_alias_uris(req, identity.tenant_id)

    # P-INJ-1: a fact's source is attested when it matches the writing principal.
    # Mismatches are flagged (attested=False); enforce mode rejects them.
    from ..source_attestation import (
        evaluate_source_attested,
        source_attestation_enforce_enabled,
    )

    attested = evaluate_source_attested(source, identity)
    if attested is False and source_attestation_enforce_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "source_attestation_failed: declared source does not match the "
                "authenticated principal"
            ),
        )
    garden = _resolve_garden_for_assert(req, identity)

    garden_uuid = garden["id"] if garden is not None else None
    attested_int = None if attested is None else (1 if attested else 0)

    # Relation namespacing convention check (see relation-convention.md)
    relation_warnings = _validate_relation(req.relation)
    for w in re
... [truncated]
```

### node/src/stigmem_node/routes/auth.py
```
"""Track B / B3 + C2 — OIDC → scoped API-key exchange bridge.

POST /v1/auth/oidc/exchange   validate id_token, mint/refresh a scoped key
POST /v1/auth/keys            register a caller-provided static API key (admin)
GET  /v1/auth/keys            list caller's own keys
DELETE /v1/auth/keys/{key_id} revoke a specific key

C2 addition: when the experimental memory-garden advanced ACL plugin and its
explicit OIDC ceiling gate are enabled, permissions are capped by the caller's
garden membership role. admin/writer in any garden → up to ["read","write"];
reader/no membership → ["read"].

``POST /v1/auth/keys`` is the supported post-bootstrap path for minting
additional static (non-OIDC) keys.  It mirrors the bootstrap CLI's
caller-generated-key posture: the caller supplies the raw key material;
the node hashes and stores it.  The endpoint requires the caller to
hold the ``admin`` capability.  Spec §3.5.  Closes issue #135.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..audit_event import emit as audit_emit
from ..auth import (
    Identity,
    create_api_key,
    find_api_key_id_by_raw_key,
    register_api_key,
    resolve_identity,
)
from ..db import db
from ..memory_garden_acl_gate import oidc_permission_ceiling_enabled
from ..models.auth import (
    ExchangeRequest,
    ExchangeResponse,
    ExpiringKeyInfo,
    KeyInfo,
    RegisterKeyRequest,
    RegisterKeyResponse,
)
from ..net_util import assert_safe_url
from ..settings import settings
from ..tenant import TenantIdError

logger = logging.getLogger("stigmem.auth")
router = APIRouter(prefix="/v1/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# JWKS cache — keyed by issuer URL, value = (jwks_client, fetched_at_unix)
# ---------------------------------------------------------------------------
_JWKS_CACHE: dict[str, tuple[jwt.PyJWKClient, float]] = {}
_JWKS_CACHE_TTL = 600  # 10 minutes


def _get_jwks_client(issuer_url: str) -> jwt.PyJWKClient:
    entry = _JWKS_CACHE.get(issuer_url)
    now = time.monotonic()
    if entry and (now - entry[1]) < _JWKS_CACHE_TTL:
        return entry[0]

    # Discover JWKS URI from OIDC metadata document
    disco_url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    try:
        assert_safe_url(disco_url, allow_schemes=frozenset({"https"}))
        resp = httpx.get(disco_url, timeout=5.0, follow_redirects=False)
        resp.raise_for_status()
        jwks_uri: str = resp.json()["jwks_uri"]
        assert_safe_url(jwks_uri, allow_schemes=frozenset({"https"}))
    except Exception as exc:
        logger.warning("OIDC discovery failed for %s: %s", issuer_url, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC provider discovery failed",
        ) from exc

    client = jwt.PyJWKClient(jwks_uri)
    _JWKS_CACHE[issuer_url] = (client, now)
    return client


def _verify_id_token(id_token: str) -> dict[str, Any]:
    """Validate the id_token and return decoded claims. Raises HTTPException on failure."""
    jwks_client = _get_jwks_client(settings.oidc_issuer_url)
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        claims: dict[str, Any] = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=settings.oidc_id_token_algorithms,
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer_url,
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="id_token expired",
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="id_token audience mismatch",
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"id_token invalid: {exc}",
        ) from exc
    return claims


def _check_domain(email: str | None) -> None:
    """Enforce oidc_allowed_domains if configured."""
    if not settings.oidc_allowed_domains or not email:
        return
    allowed = {d.strip().lower() for d in settings.oidc_allowed_domains.split(",") if d.strip()}
    if not allowed:
        return
    domain = email.split("@", 1)[-1].lower()
    if domain not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Email domain '{domain}' is not permitted",
        )


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

_ALLOWED_PERMISSIONS = {"read", "write"}
_PERM_ORDER = ["read", "write"]


def _derive_permission_ceiling(entity_uri: str) -> set[str]:
    """Return the max permissions the entity is entitled to via garden membership.

    admin/writer role in any garden → {"read","write"}
    reader role only, or no membership → {"read"}
    """
    with db() as conn:
        rows = conn.execute(
            "SELECT role FROM garden_members WHERE entity_uri = ?",
            (entity_uri,),
        ).fetchall()
    roles = {r["role"] for r in rows}
    if "admin" in roles or "writer" in roles:
        return {"read", "write"}
    return {"read"}


# ---------------------------------------------------------------------------
# Static key registration (POST /v1/auth/keys) — issue #135
#
# Permission vocabulary kept narrow to the §3.5 set the auth module already
# defines.  Source-attestation-specific fields (``allowed_source_entities``,
# attestation-mode binding) are deferred to §18 per ADR-002 and are NOT
# accepted here.  See spec/EVOLUTION.md § §18 for the deferred surface.
# ---------------------------------------------------------------------------

_STATIC_KEY_ALLOWED_PERMISSIONS: frozenset[str] = frozenset(
    {"read", "write", "instruction:write", "federate", "admin", "audit.read"}
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/oidc/exchange", response_model=ExchangeResponse)
def oidc_exchange(body: ExchangeRequest) -> ExchangeResponse:
    """Exchange an OIDC id_token for a scoped stigmem API key."""
    if not settings.oidc_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not enabled on this node",
        )

    claims = _verify_id_token(body.id_token)
    sub: str = claims["sub"]
    email: str | None = claims.get("email")
    _check_domain(email)

    entity_uri = f"oidc:{sub}"

    # Experimental memory-garden advanced ACL: cap permissions by garden membership
    # only when the plugin and its explicit OIDC ceiling gate are enabled.
    requested = {p for p in body.permissions if p in _ALLOWED_PERMISSIONS}
    if oidc_permission_ceiling_enabled():
        requested &= _derive_permission_ceiling(entity_uri)
    if not requested:
        requested = {"read"}
    permissions = sorted(requested, key=lambda p: _PERM_ORDER.index(p))

    expires_at = (datetime.now(UTC) + timedelta(hours=settings.oidc_token_ttl_hours)).isoformat()

    # Rotate: revoke all previous OIDC-issued keys for this sub before minting
    # a new one.  This ensures a single valid session per sub so that IdP
    # session-termination (logout, account suspension) immediately invalidates
    # access — offboarding comes for free from the IdP.
    with db() as conn:
        conn.execute("DELETE FROM api_keys WHERE oidc_sub = ?", (sub,))

    raw_key = create_api_key(
        entity_uri=entity_uri,
        permissions=permissions,
        description=f"OIDC session for {email or sub}",
        expires_at=expires_at,
        oidc_sub=sub,
    )

    logger.info("OIDC exchange: sub=%s entity_uri=%s perms=%s", sub, entity_uri, permissions)
    return ExchangeResponse(
        api_key=raw_key,
        entity_uri=entity_uri,
        permissions=permissions,
        expires_at=expires_at,
    )


@router.post(
    "/keys",
    response_model=RegisterKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a caller-provided static API key (admin only).",
)
def register_static_key(
    body: RegisterKeyRequest,
    identity: Annotated[Identity, Depends(resolve_identity)],
) -> RegisterKeyResponse:
    """Register a caller-provided raw API key.

    Mirrors the bootstrap CLI's posture: the caller supplies the raw key
    material; the node hashes and stores it.  The endpoint requires the
    caller to hold the ``admin`` capability — typically the bootstrap
    key, or a previously-minted admin-scoped key.

    The response NEVER echoes the raw key; the caller already has it.
    """
    if not identity.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin permission required to mint API keys",
        )

    # Validate the permission set.  Reject unknown vocabulary up front so a
    # typo (`"writes"`) doesn't silently create an unintentionally-scoped key.
    requested_perms = set(body.permissions)
    invalid = requested_perms - _STATIC_KEY_ALLOWED_PERMISSIONS
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"unknown permissions: {sorted(invalid)}; "
                f"allowed: {sorted(_STATIC_KEY_ALLOWED_PERMISSIONS)}"
            ),
        )
    if not requested_perms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="permissions list must be non-empty",
        )

    # Refuse duplicate raw credentials before hashing. Argon2id uses a fresh
    # salt for each hash, so duplicate detection must verify existing rows
    # rather than relying on the key_hash unique constraint.
    if find_api_key_id_by_raw_key(body.raw_key) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="raw_key already exists; generate a new key value",
        )

    # Minting a key in a tenant other than the caller's own is a cross-tenant
    # privilege escalation (audit M2): a tenant-scoped admin could otherwise mint
    # an admin key in any other tenant. Require the elevated cross-cutting
    # admin:federation capability to cross the tenant boundary; default same-tenant.
    target_tenant = body.tenant_id or identity.tenant_id
    if target_tenant != identity.tenant_id and not identity.can_admin_federation():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="cannot mint keys in a tenant other than your own",
        )

    # Persist via the existing helper.  Caller-provided raw_key, never
    # auto-generated.
    permissions_sorted = sorted(requested_perms)
    # ``registered_id`` is the UUID bookkeeping handle for the new row, NOT
    # credential material.  The raw key value never enters this scope —
    # ``register_api_key`` hashes it inside the helper.  Naming hygiene
    # here keeps CodeQL's ``py/clear-text-logging-sensitive-data`` name
    # heuristic (which matches any variable containing ``key``) from
    # false-flagging the audit log below.  Same precedent as PR #106.
    try:
        registered_id = register_api_key(
            raw_key=body.raw_key,
            entity_uri=body.entity_uri,
            permissions=permissions_sorted,
            description=body.description,
            expires_at=body.expires_at,
            tenant_id=target_tenant,
        )
    except Tena
... [truncated]
```

(+88 more files reference the changed code)
Repository Map
node/src/stigmem_node/__init__.py
node/src/stigmem_node/audit_event.py
node/src/stigmem_node/auth.py
node/src/stigmem_node/billing.py
node/src/stigmem_node/body_limit.py
node/src/stigmem_node/card_materializer.py
node/src/stigmem_node/cid.py
node/src/stigmem_node/cli_admin_handlers.py
node/src/stigmem_node/cli_federation_handlers.py
node/src/stigmem_node/db.py
node/src/stigmem_node/decay.py
node/src/stigmem_node/entity_normalizer.py
node/src/stigmem_node/entity_resolver.py
node/src/stigmem_node/fact_chain.py
node/src/stigmem_node/fact_visibility.py
node/src/stigmem_node/federation_ingest.py
node/src/stigmem_node/federation_pull.py
node/src/stigmem_node/fuzzy_resolver.py
node/src/stigmem_node/garden_acl.py
node/src/stigmem_node/graph.py
node/src/stigmem_node/graph_index.py
node/src/stigmem_node/hlc.py
node/src/stigmem_node/immutability.py
node/src/stigmem_node/instruction_migrate.py
node/src/stigmem_node/jobs.py
node/src/stigmem_node/main.py
node/src/stigmem_node/memory_garden_acl_gate.py
node/src/stigmem_node/metrics.py
node/src/stigmem_node/migrate.py
node/src/stigmem_node/multi_tenant_gate.py
node/src/stigmem_node/net_util.py
node/src/stigmem_node/peer_auth.py
node/src/stigmem_node/peer_token.py
node/src/stigmem_node/plugin_migrations.py
node/src/stigmem_node/rate_limit.py
node/src/stigmem_node/recall_pipeline.py
node/src/stigmem_node/routes/__init__.py
node/src/stigmem_node/routes/_facts_assert.py
node/src/stigmem_node/routes/_federation_impl.py
node/src/stigmem_node/routes/admin_audit.py
node/src/stigmem_node/routes/agent_keys.py
node/src/stigmem_node/routes/aliases.py
node/src/stigmem_node/routes/audit.py
node/src/stigmem_node/routes/auth.py
node/src/stigmem_node/routes/cards.py
node/src/stigmem_node/routes/cid_admin.py
node/src/stigmem_node/routes/cid_integrity.py
node/src/stigmem_node/routes/decay.py
node/src/stigmem_node/routes/gardens.py
node/src/stigmem_node/routes/graph.py
node/src/stigmem_node/routes/identity.py
node/src/stigmem_node/routes/instruction.py
node/src/stigmem_node/routes/intents.py
node/src/stigmem_node/routes/lint.py
node/src/stigmem_node/routes/mcp.py
node/src/stigmem_node/routes/quarantine.py
node/src/stigmem_node/routes/resolver.py
node/src/stigmem_node/routes/subscriptions.py
node/src/stigmem_node/routes/synthesize.py
node/src/stigmem_node/routes/time_travel_gate.py
node/src/stigmem_node/routes/tombstones.py
node/src/stigmem_node/routes/wellknown.py
node/src/stigmem_node/session_graph.py
node/src/stigmem_node/settings.py
node/src/stigmem_node/snapshot.py
node/src/stigmem_node/source_attestation.py
node/src/stigmem_node/source_trust.py
node/src/stigmem_node/subscription_delivery.py
node/src/stigmem_node/tenant.py
node/src/stigmem_node/tls.py
node/src/stigmem_node/tombstone_cache.py
node/src/stigmem_node/tombstone_gate.py
node/src/stigmem_node/tombstone_signing.py
node/src/stigmem_node/tombstones.py
node/src/stigmem_node/tracing.py
node/src/stigmem_node/trust_rules.py
node/src/stigmem_node/utility/__init__.py
node/src/stigmem_node/utility/entity_normalizer.py
node/src/stigmem_node/utility/net_util.py
node/src/stigmem_node/vector_search.py
node/tests/conftest.py
node/tests/observability/__init__.py
node/tests/observability/test_audit_enriched.py
node/tests/observability/test_billing_hooks.py
node/tests/observability/test_failure_modes.py
node/tests/observability/test_observability.py
node/tests/observability/test_quota.py
node/tests/observability/test_rate_limit.py
node/tests/observability/test_tracing.py
node/tests/routes/__init__.py
node/tests/routes/test_admin_audit.py
node/tests/routes/test_cards.py
node/tests/routes/test_facts.py
node/tests/routes/test_facts_garden_acl.py
node/tests/routes/test_gardens.py
node/tests/routes/test_graph.py
node/tests/routes/test_ingest_size_caps.py
node/tests/routes/test_intents.py
node/tests/routes/test_mcp_routes.py
node/tests/routes/test_multi_tenant.py
node/tests/routes/test_quarantine.py
node/tests/routes/test_ratelimit_and_sub_cap.py
node/tests/routes/test_subscription_delivery_race.py
node/tests/routes/test_subscription_delivery_ssrf.py
node/tests/routes/test_subscriptions.py
node/tests/test_cors.py
node/tests/test_tenant_context_metadata.py
node/tests/test_tenant_validation.py
./  (1 files)
adapters/  (1 files)
adapters/mcp/  (2 files)
adapters/openclaw/  (9 files)
docs/  (3 files)
docs/archive/  (2 files)
docs/docs/  (1 files)
docs/plugins/  (3 files)
docs/scripts/  (3 files)
docs/src/  (8 files)
eval/  (4 files)
eval/federation/  (12 files)
eval/harness/  (4 files)
eval/soak/  (4 files)
experimental/cognee-adapter/  (6 files)
experimental/dashboard/  (43 files)
experimental/gemini-adapter/  (5 files)
experimental/lazy-instruction-discovery/  (5 files)
experimental/letta-adapter/  (5 files)
experimental/memory-garden-acl/  (4 files)
experimental/multi-tenant/  (4 files)
experimental/obsidian-adapter/  (24 files)
experimental/openai-tools-adapter/  (5 files)
experimental/paperclip-adapter/  (1 files)
experimental/source-attestation/  (4 files)
experimental/time-travel/  (4 files)
experimental/tombstones/  (4 files)
experimental/zep-adapter/  (6 files)
node/src/  (121 files)
node/tests/  (176 files)
scripts/  (50 files)
sdks/stigmem-py/  (7 files)
sdks/stigmem-ts/  (6 files)
site/assets/  (1 files)
tests/  (1 files)
... (647 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "stigmem",
  "private": true,
  "version": "0.9.0-alpha.10",
  "description": "Stigmem — federated knowledge fabric for AI agents",
  "workspaces": [
    "adapters/mcp",
    "apps/dashboard",
    "sdks/stigmem-ts"
  ],
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev",
    "lint": "turbo run lint",
    "type-check": "turbo run type-check",
    "test": "turbo run test",
    "grade:duplication": "jscpd --reporters console,json --output .jscpd --ignore \"**/node_modules/**,**/.venv/**,**/.git/**,**/build/**,**/dist/**,**/.next/**,**/.turbo/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/.jscpd/**,**/coverage/**\" --noTips node/src node/tests scripts adapters eval experimental sdks",
    "clean": "turbo run clean"
  },
  "devDependencies": {
    "jscpd": "^4.2.2",
    "turbo": "^2.9.14",
    "typescript": "^5.4.0"
  },
  "engines": {
    "node": ">=24",
    "pnpm": ">=9"
  },
  "packageManager": "pnpm@9.10.0",
  "pnpm": {
    "overrides": {
      "postcss": ">=8.5.11",
      "ip-address": ">=10.1.1",
      "fast-uri": ">=3.1.2",
      "hono": ">=4.12.23",
      "qs": "6.15.2"
    }
  }
}

```

### pyproject.toml
```
[project]
name = "stigmem"
version = "0.9.0a10"
description = "Stigmem — federated knowledge fabric for AI agents (meta-package)"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
authors = [
  { name = "Eidetic Labs", email = "oss@eidetic-labs.ai" },
]
keywords = ["stigmem", "federation", "memory", "ai", "agents"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: Apache Software License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

# `pip install stigmem` → installs the Python SDK (most common adopter path).
# Operators self-hosting a node use `pip install stigmem[node]` or
# `pip install stigmem-node` directly. See the install table below for extras.
dependencies = [
  "stigmem-py>=0.9.0a10,<1.0.0",
]

[project.optional-dependencies]
# pip install stigmem[node] → SDK + reference node service
node = ["stigmem-node>=0.9.0a10,<1.0.0"]
# pip install stigmem[openclaw] → SDK + OpenClaw adapter
openclaw = ["stigmem-openclaw>=0.9.0a10,<1.0.0"]
# pip install stigmem[<feature>] → SDK + one published experimental plugin
cognee-adapter = [
  "stigmem-plugin-cognee-adapter>=0.1.0,<2.0.0",
]
gemini-adapter = [
  "stigmem-plugin-gemini-adapter>=0.1.0,<2.0.0",
]
letta-adapter = [
  "stigmem-plugin-letta-adapter>=0.1.0,<2.0.0",
]
openai-tools-adapter = [
  "stigmem-plugin-openai-tools-adapter>=0.1.0,<2.0.0",
]
zep-adapter = [
  "stigmem-plugin-zep-adapter>=0.1.0,<2.0.0",
]
# pip install stigmem[adapters] -> SDK + host-application adapter plugins
adapters = [
  "stigmem-plugin-cognee-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-gemini-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-letta-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-openai-tools-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-zep-adapter>=0.1.0,<2.0.0",
]
lazy-instruction-discovery = [
  "stigmem-plugin-lazy-instruction-discovery>=0.1.0,<2.0.0",
]
memory-garden-acl = [
  "stigmem-plugin-memory-garden-acl>=0.1.0,<2.0.0",
]
multi-tenant = [
  "stigmem-plugin-multi-tenant>=0.1.0,<2.0.0",
]
source-attestation = [
  "stigmem-plugin-source-attestation>=0.1.0,<2.0.0",
]
time-travel = [
  "stigmem-plugin-time-travel>=0.1.0,<2.0.0",
]
tombstones = [
  "stigmem-plugin-tombstones>=0.1.0,<2.0.0",
]
# pip install stigmem[plugins-all] → SDK + all currently published experimental plugins
plugins-all = [
  "stigmem-plugin-cognee-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-gemini-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-letta-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-openai-tools-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-zep-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-lazy-instruction-discovery>=0.1.0,<2.0.0",
  "stigmem-plugin-memory-garden-acl>=0.1.0,<2.0.0",
  "stigmem-plugin-multi-tenant>=0.1.0,<2.0.0",
  "stigmem-plugin-source-attestation>=0.1.0,<2.0.0",
  "stigmem-plugin-time-travel>=0.1.0,<2.0.0",
  "stigmem-plugin-tombstones>=0.1.0,<2.0.0",
]
# pip install stigmem[all] → everything published from this monorepo
all = [
  "stigmem-node>=0.9.0a10,<1.0.0",
  "stigmem-openclaw>=0.9.0a10,<1.0.0",
  "stigmem-plugin-cognee-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-gemini-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-letta-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-openai-tools-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-zep-adapter>=0.1.0,<2.0.0",
  "stigmem-plugin-lazy-instruction-discovery>=0.1.0,<2.0.0",
  "stigmem-plugin-memory-garden-acl>=0.1.0,<2.0.0",
  "stigmem-plugin-multi-tenant>=0.1.0,<2.0.0",
  "stigmem-plugin-source-attestation>=0.1.0,<2.0.0",
  "stigmem-plugin-time-travel>=0.1.0,<2.0.0",
  "stigmem-plugin-tombstones>=0.1.0,<2.0.0",
]

[project.urls]
Homepage = "https://github.com/eidetic-labs/stigmem"
Documentation = "https://docs.stigmem.dev"
Repository = "https://github.com/eidetic-labs/stigmem"
Issues = "https://github.com/eidetic-labs/stigmem/issues"
Changelog = "https://github.com/eidetic-labs/stigmem/blob/main/CHANGELOG.md"

# stigmem is a meta-package: it carries no Python code of its own.
# `[tool.setuptools] packages = []` tells setuptools "no Python packages to
# bundle" — the wheel is intentionally empty. The point of this distribution
# is to claim the canonical `stigmem` name on PyPI and make `pip install stigmem`
# resolve to the right collection of real packages via dependencies + extras.
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = []

[tool.uv.workspace]
# Per ADR-002 v1 critical-path scope + ADR-020 repository contracts: only critical-path
# packages in the default workspace. Only explicitly listed experimental
# packages are included here, so default `uv sync` does not pull deferred
# experimental depen
```
Context & Existing Test Patterns
Existing test files touched by the patch: node/tests/conftest.py, node/tests/observability/test_observability.py, node/tests/routes/test_metrics_auth.py, node/tests/routes/test_multi_tenant.py, node/tests/routes/test_subscription_delivery_ssrf.py, node/tests/routes/test_subscription_event_retention.py, node/tests/routes/test_subscription_webhook_ssrf_creation.py, node/tests/routes/test_subscriptions.py, node/tests/routes/test_webhook_dns_rebind.py
Repository top-level entries: .env.example, .github, .gitignore, .gitleaks.toml, .mcp.json, .python-version, .readthedocs.yaml, CHANGELOG.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, LICENSE, LIMITATIONS.md, LOG.md, MAINTAINERS.md, Makefile, OPERATING.md, README.md, ROADMAP.md, SECURITY.md, adapters, archive, cliff.toml, conftest.py, data, deploy, docker-compose.observability.yml, docker-compose.yml, docs, eval, experimental, features, node, package.json, pnpm-lock.yaml, pnpm-workspace.yaml, pyproject.toml, release, release-notes, scripts, sdks, site, spec, tests, turbo.json, uv.lock
Project's own test patterns and conventions:
### adapters/conftest.py
```
"""Top-level conftest for adapters/ test isolation.

Several adapters expose their implementation as ``from adapter import ...`` and
also keep tests under same-named ``tests/`` directories. During aggregate test
collection, pytest would otherwise reuse the first imported ``adapter`` module
for subsequent adapter suites. The hook below resets that shared import and
promotes the correct adapter directory on ``sys.path`` before each adapter test
module is imported.
"""

import sys
from contextlib import suppress


def pytest_collect_file(parent, file_path):
    """Ensure each adapter test file sees its own adapter.py."""
    if file_path.suffix != ".py" or not file_path.name.startswith("test_"):
        return None

    # adapter tests live at adapters/<adapter>/tests/test_*.py
    tests_dir = file_path.parent
    adapter_dir = tests_dir.parent
    if tests_dir.name != "tests" or adapter_dir.parent.name != "adapters":
        return None

    adapter_str = str(adapter_dir)

    # Drop any cached 'adapter' module from a previous adapter's collection
    sys.modules.pop("adapter", None)

    # Promote this adapter's directory to the front of sys.path so the
    # subsequent module import resolves to the right adapter.py
    with suppress(ValueError):
        sys.path.remove(adapter_str)
    sys.path.insert(0, adapter_str)

    return None

```

### adapters/openclaw/tests/conftest.py
```
"""conftest.py — add the adapter and SDK src directories to sys.path."""

import sys
from pathlib import Path

_HERE = Path(__file__).parent
_ADAPTER_ROOT = _HERE.parent

# src/stigmem_openclaw — importable as stigmem_openclaw (installed package layout)
sys.path.insert(0, str(_ADAPTER_ROOT / "src"))

# adapters/openclaw/ — allows `from adapter import ...` via the compat shim
sys.path.insert(0, str(_ADAPTER_ROOT))

# sdks/stigmem-py/src — import stigmem SDK without a pip install
_REPO_ROOT = _ADAPTER_ROOT.parent.parent  # openclaw/ -> adapters/ -> repo root
sys.path.insert(0, str(_REPO_ROOT / "sdks" / "stigmem-py" / "src"))

```

### node/tests/routes/test_subscriptions.py
```
"""Tests for the Phase 9 subscription primitive — spec §20.

Coverage:
- CRUD: create, list, get, delete
- BOLA: each caller only sees own subscriptions
- Idempotency key dedup
- Natural dedup (same target/on_change/delivery_address)
- fan_out: writing a fact creates pending events for matching subscriptions
- Webhook delivery (mocked httpx.Client)
- Retry backoff and circuit-breaker
- Replay window (GET /v1/subscriptions/{id}/events?since=...)
- §17 garden ACL enforcement at delivery time
- §19 sanitizer at delivery time
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import stigmem_node.auth as auth_mod
import stigmem_node.settings as settings_module
import stigmem_node.subscription_delivery as delivery_mod
from stigmem_node.main import create_app
from stigmem_node.plugins import PluginManifest
from stigmem_node.plugins.testing import stigmem_plugins

Settings = settings_module.Settings
create_api_key = auth_mod.create_api_key
_MEMORY_GARDEN_ACL_SRC = (
    Path(__file__).resolve().parents[3] / "experimental" / "memory-garden-acl" / "src"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _memory_garden_acl_manifest() -> PluginManifest:
    if str(_MEMORY_GARDEN_ACL_SRC) not in sys.path:
        sys.path.insert(0, str(_MEMORY_GARDEN_ACL_SRC))
    import importlib

    plugin = importlib.import_module("stigmem_plugin_memory_garden_acl")
    return plugin.plugin_manifest()


def _enable_acl_recall_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STIGMEM_MEMORY_GARDEN_ACL_ENABLED", "true")
    monkeypatch.setenv("STIGMEM_MEMORY_GARDEN_ACL_APPLY_RECALL_FILTER", "true")


def _assert_fact(
    client: TestClient, entity: str = "stigmem://test/agent/alice", scope: str = "local"
) -> dict:
    resp = client.post(
        "/v1/facts",
        json={
            "entity": entity,
            "relation": "test:name",
            "value": {"type": "string", "v": "Alice"},
            "source": entity,
            "scope": scope,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_subscription(
    client: TestClient,
    target: str = "local",
    on_change: str = "webhook",
    delivery_address: str = "https://example.com/hook",
    idempotency_key: str | None = None,
) -> dict:
    body: dict = {"target": target, "on_change": on_change, "delivery_address": delivery_address}
    if idempotency_key is not None:
        body["idempotency_key"] = idempotency_key
    resp = client.post("/v1/subscriptions", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _wait_for_delivery_lock_idle(timeout_s: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if delivery_mod._DELIVER_PENDING_LOCK.acquire(blocking=False):  # noqa: SLF001
            delivery_mod._DELIVER_PENDING_LOCK.release()  # noqa: SLF001
            return
        time.sleep(0.01)
    raise AssertionError("subscription delivery lock did not become idle")


def _wait_for_subscription_event(
    event_id: str,
    predicate: Callable[[dict], bool],
    timeout_s: float = 5.0,
) -> dict:
    """Drive production delivery until a specific event matches a predicate."""
    import stigmem_node.db as db_mod

    deadline = time.monotonic() + timeout_s
    last_event: dict | None = None
    while time.monotonic() < deadline:
        with db_mod.db() as conn:
            event = conn.execute(
                "SELECT * FROM subscription_events WHERE id=?", (event_id,)
            ).fetchone()
        if event is None:
            raise AssertionError(f"subscription event {event_id} was not found")
        last_event = dict(event)
        if predicate(last_event):
            return last_event
        _wait_for_delivery_lock_idle(timeout_s=max(0.1, deadline - time.monotonic()))
        delivery_mod.deliver_pending()
        time.sleep(0.01)
    raise AssertionError(f"subscription event {event_id} did not match predicate: {last_event}")


def _subscription_event_id(subscription_id: str) -> str:
    import stigmem_node.db as db_mod

    with db_mod.db() as conn:
        event = conn.execute(
            "SELECT id FROM subscription_events WHERE subscription_id=?", (subscription_id,)
        ).fetchone()
    if event is None:
        raise AssertionError(f"subscription {subscription_id} has no event")
    return event["id"]


def _drain_subscription_event(event_id: str, timeout_s: float = 5.0) -> str:
    event = _wait_for_subscription_event(
        event_id,
        lambda row: row["delivery_status"] in {"delivered", "failed"},
        timeout_s=timeout_s,
    )
    return event["delivery_status"]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_create_subscription(client: TestClient) -> None:
    sub = _create_subscription(client)
    assert sub["target"] == "local"
    assert sub["target_kind"] == "scope"
    assert sub["on_change"] == "webhook"
    assert sub["delivery_address"] == "https://example.com/hook"
    assert sub["circuit_open"] is False
    assert sub["consecutive_failures"] == 0


def test_create_subscription_entity_target(client: TestClient) -> None:
    sub = _create_subscription(client, target="stigmem://test/agent/alice")
    assert sub["target_kind"] == "entity"


def test_create_subscription_validation(client: TestClient) -> None:
    resp = client.post(
        "/v1/subscriptions",
        json={"target": "local", "on_change": "invalid", "delivery_address": "https://x.com"},
    )
    assert resp.status_code == 422


def test_list_subscriptions(client: TestClient) -> None:
    _create_subscription(client, target="local")
    _create_subscription(client, target="team", delivery_address="https://b.com/hook")
    resp = client.get("/v1/subscriptions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["subscriptions"]) == 2


def test_get_subscription(client: TestClient) -> None:
    sub = _create_subscription(client)
    resp = client.get(f"/v1/subscriptions/{sub['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sub["id"]


def test_get_subscription_not_found(client: TestClient) -> None:
    resp = client.get(f"/v1/subscriptions/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_subscription(client: TestClient) -> None:
    sub = _create_subscription(client)
    resp = client.delete(f"/v1/subscriptions/{sub['id']}")
    assert resp.status_code == 204

    resp2 = client.get(f"/v1/subscriptions/{sub['id']}")
    assert resp2.status_code == 404


def test_delete_subscription_not_found(client: TestClient) -> None:
    resp = client.delete(f"/v1/subscriptions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Dedup / idempotency
# ---------------------------------------------------------------------------


def test_idempotency_key_returns_existing(client: TestClient) -> None:
    key = str(uuid.uuid4())
    sub_a = _create_subscription(client, idempotency_key=key)
    sub_b = _create_subscription(client, target="team", idempotency_key=key)
    assert sub_a["id"] == sub_b["id"]


def test_natural_dedup(client: TestClient) -> None:
    sub_a = _create_subscription(client)
    sub_b = _create_subscription(client)  # same target/on_change/address
    assert sub_a["id"] == sub_b["id"]


# ---------------------------------------------------------------------------
# BOLA guard
# ---------------------------------------------------------------------------


@pytest.fixture()
def two_authed_clients(tmp_db: str, backend: str, encrypt: str) -> Generator:
    """Two authed clients with different entity URIs."""
    import importlib

    import stigmem_node.db as db_mod
    import stigmem_node.routes.wellknown as wk_mod

    _PATCHABLE = [
        "stigmem_node.federation_pull",
        "stigmem_node.peer_token",
        "stigmem_node.federation_ingest",
        "stigmem_node.routes.federation",
        "stigmem_node.routes.identity",
        "stigmem_node.identity.trust_store",
        "stigmem_node.decay",
        "stigmem_node.routes.decay",
        "stigmem_node.routes.lint",
        "stigmem_node.routes.synthesize",
        "stigmem_node.rate_limit",
    ]
    extra = [importlib.import_module(n) for n in _PATCHABLE if importlib.util.find_spec(n)]

    original = settings_module.settings
    test_settings = Settings(
        db_path=tmp_db,
        storage_backend=backend,
        auth_required=True,
        node_url="http://testnode",
    )
    settings_module.settings = test_settings  # type: ignore[assignment]
    auth_mod.settings = test_settings  # type: ignore[assignment]
    db_mod.settings = test_settings  # type: ignore[assignment]
    wk_mod.settings = test_settings  # type: ignore[assignment]
    for mod in extra:
        if hasattr(mod, "settings"):
            mod.settings = test_settings

    key_a = create_api_key("stigmem://test/agent/alice", ["read", "write"])
    key_b = create_api_key("stigmem://test/agent/bob", ["read", "write"])

    app = create_app()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield (
            c,
            {"Authorization": f"Bearer {key_a}"},
            {"Authorization": f"Bearer {key_b}"},
        )

    settings_module.settings = original  # type: ignore[assignment]
    auth_mod.settings = original  # type: ignore[assignment]
    db_mod.settings = original  # type: ignore
```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

