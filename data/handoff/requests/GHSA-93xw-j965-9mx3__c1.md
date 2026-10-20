<!-- label=GHSA-93xw-j965-9mx3 call=1 hash=c1c04856a6 -->
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
- OSV ID: GHSA-93xw-j965-9mx3
- CVE: CVE-2026-77258
- CWE: CWE-22
- Ecosystem / Package: PyPI / mcp-atlassian
- Repository: https://github.com/sooperset/mcp-atlassian
- Official Summary: MCP Atlassian: Arbitrary file read/exfiltration via upload_attachment missing validate_safe_path()

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/pyproject.toml b/pyproject.toml
index 5bf15ef1137f476d2dd803fcecdc2be695e55149..ef0602f3ae1a47d10222bcbe12c8cefa87c5afe0 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -65,6 +65,7 @@ markers = [
     "integration: mark test as requiring integration with real services",
     "dc_e2e: mark test as requiring DC instances (Jira DC + Confluence DC)",
     "cloud_e2e: mark test as requiring Cloud instances (Jira Cloud + Confluence Cloud)",
+    "security_regression: SP5 security regression test (xfail-strict until the Phase B root fix lands; see plan)",
 ]
 
 [tool.ruff]
diff --git a/src/mcp_atlassian/confluence/attachments.py b/src/mcp_atlassian/confluence/attachments.py
index 4d585c59dbbb20b83e7ef1a49b2005c0723f4d49..82781ce29b985a298c008ae28567fb460b688e63 100644
--- a/src/mcp_atlassian/confluence/attachments.py
+++ b/src/mcp_atlassian/confluence/attachments.py
@@ -149,9 +149,10 @@ class AttachmentsMixin(ConfluenceClient, AttachmentsOperationsProto):
             return {"success": False, "error": "No file path provided"}
 
         try:
-            # Convert to absolute path if relative
-            if not os.path.isabs(file_path):
-                file_path = os.path.abspath(file_path)
+            # Confine the upload source to the workspace before it is read: reject
+            # traversal/absolute paths that escape CWD (arbitrary file read /
+            # exfiltration via a caller-supplied file_path).
+            file_path = str(validate_safe_path(file_path))
 
             # Check if file exists
             if not os.path.exists(file_path):
diff --git a/src/mcp_atlassian/confluence/client.py b/src/mcp_atlassian/confluence/client.py
index 97b33dad9d5d7b8a841d19a70cc44bf100906cdf..3880b64e56ae9b3afb0d2af06dfdee4d11346cc6 100644
--- a/src/mcp_atlassian/confluence/client.py
+++ b/src/mcp_atlassian/confluence/client.py
@@ -17,6 +17,8 @@ from ..utils.http import (
 from ..utils.logging import get_masked_session_headers, log_config_param, mask_sensitive
 from ..utils.oauth import configure_oauth_session
 from ..utils.ssl import configure_ssl_verification
+from ..utils.ssrf_adapter import mount_ssrf_pinning
+from ..utils.urls import make_ssrf_redirect_hook
 from ..utils.user_agent import get_default_user_agent
 from .config import ConfluenceConfig
 
@@ -130,8 +132,18 @@ class ConfluenceClient:
             client_key_password=self.config.client_key_password,
         )
 
-        # Apply opt-in HTTP hardening after SSL setup so SSLIgnoreAdapter, if
-        # mounted, also picks up the configured behavior.
+        # Validate redirects for SSRF on every outbound call from this session
+        # (covers direct _session.get() paths and global/stdio fetchers, not just
+        # the per-user HTTP path).
+        self.confluence._session.hooks["response"].append(make_ssrf_redirect_hook())
+        # Pin DNS resolution against rebinding: resolve+validate once and connect
+        # to that address, closing the validate→reconnect TOCTOU. Preserves TLS SNI.
+        mount_ssrf_pinning(self.confluence._session)
+
+        # Apply opt-in HTTP hardening after SSL setup and after the pinning
+        # adapter is mounted: these wrappers patch send() in place on whatever
+        # adapters are mounted now, so mounting the pinning adapter later would
+        # silently drop them.
         configure_retry(self.confluence._session, service="Confluence")
         configure_concurrency(self.confluence._session, service="Confluence")
         configure_rate_limit(self.confluence._session, service="Confluence")
diff --git a/src/mcp_atlassian/confluence/search.py b/src/mcp_atlassian/confluence/search.py
index 73a23b4deebd7c71800f0306172b2a230eeb1658..9dbc8283b7a328d5ee0f343fa4148050e6ba8a0c 100644
--- a/src/mcp_atlassian/confluence/search.py
+++ b/src/mcp_atlassian/confluence/search.py
@@ -23,6 +23,29 @@ logger = logging.getLogger("mcp-atlassian")
 class SearchMixin(ConfluenceClient):
     """Mixin for Confluence search operations."""
 
+    def _and_spaces_filter(self, cql: str, filter_to_use: str) -> str:
+        """AND a single comma-separated spaces allowlist into ``cql``.
+
+        Always ANDs the allowlist, even when the caller's CQL already names a
+        space, so a caller-supplied ``space = X`` cannot escape it.
+        """
+        spaces = [s.strip() for s in filter_to_use.split(",")]
+        space_query = " OR ".join(
+            [f"space = {quote_cql_identifier_if_needed(space)}" for space in spaces]
+        )
+        if not cql:
+            return space_query
+        # Extract a trailing ORDER BY so the AND does not produce invalid CQL.
+        order_match = re.search(r"\s+(ORDER\s+BY\s+.*)$", cql, re.IGNORECASE)
+        if order_match:
+            order_clause = order_match.group(1)
+            cql_without_order = cql[: order_match.start()]
+            cql = f"({cql_without_order}) AND ({space_query}) {order_clause}"
+        else:
+            cql = f"({cql}) AND ({space_query})"
+        logger.info(f"Applied spaces filter to query: {cql}")
+        return cql
+
     @handle_atlassian_api_errors("Confluence API")
     def search(
         self, cql: str, limit: int = 10, spaces_filter: str | None = None
@@ -33,8 +56,9 @@ class SearchMixin(ConfluenceClient):
         Args:
             cql: Confluence Query Language string
             limit: Maximum number of results to return
-            spaces_filter: Optional comma-separated list of space keys to filter by,
-                overrides config
+            spaces_filter: Optional comma-separated list of space keys to narrow
+                results within the configured allowlist (ANDed with config,
+                never replaces it)
 
         Returns:
             List of ConfluencePage models containing search results
@@ -45,27 +69,13 @@ class SearchMixin(ConfluenceClient):
         """
         limit = clamp_limit(limit, context="confluence.search")
 
-        # Use spaces_filter parameter if provided, otherwise fall back to config
-        filter_to_use = spaces_filter or self.config.spaces_filter
-
-        # Apply spaces filter if present
-        if filter_to_use:
-            # Split spaces filter by commas and handle possible whitespace
-            spaces = [s.strip() for s in filter_to_use.split(",")]
-
-            # Build the space filter query part using proper quoting for each space key
-            space_query = " OR ".join(
-                [f"space = {quote_cql_identifier_if_needed(space)}" for space in spaces]
-            )
-
-            # Add the space filter to existing query with parentheses
-            if cql and space_query:
-                if "space = " not in cql:  # Only add if not already filtering by space
-                    cql = f"({cql}) AND ({space_query})"
-            else:
-                cql = space_query
-
-            logger.info(f"Applied spaces filter to query: {cql}")
+        # config.spaces_filter is a hard boundary and is always applied; a
+        # caller-supplied spaces_filter may only *narrow* within it (both ANDed),
+        # never replace it — otherwise the tool argument would defeat the
+        # operator's allowlist in shared-credential deployments.
+        for filter_str in (self.config.spaces_filter, spaces_filter):
+            if filter_str:
+                cql = self._and_spaces_filter(cql, filter_str)
 
         # Execute the CQL search query
         results = self.confluence.cql(cql=cql, limit=limit)
diff --git a/src/mcp_atlassian/jira/attachments.py b/src/mcp_atlassian/jira/attachments.py
index 94a256433359a9bea9f3d12fe732544a8b0f0f13..2b2334dc97fee590e7962e4e18593c362ca29d4c 100644
--- a/src/mcp_atlassian/jira/attachments.py
+++ b/src/mcp_atlassian/jira/attachments.py
@@ -42,6 +42,17 @@ class AttachmentsMixin(JiraClient, AttachmentsOperationsProto):
             # Guard against path traversal (resolves symlinks)
             validate_safe_path(target_path)
 
+            # Do not write into the working-directory root itself: that is where
+            # Python resolves imports first, so a download landing there could
+            # overwrite an importable module and gain code execution (GHSA-6vmq).
+            # Attachments must be saved into a subdirectory.
+            resolved = Path(target_path).resolve()
+            if resolved.parent == Path(os.getcwd()).resolve():
+                logger.error(
+                    f"Refusing to download into the working-directory root: {target_path}"
+                )
+                return False
+
             logger.info(f"Downloading attachment from {url} to {target_path}")
 
             # Create the directory if it doesn't exist
@@ -370,9 +381,10 @@ class AttachmentsMixin(JiraClient, AttachmentsOperationsProto):
             return {"success": False, "error": "No file path provided"}
 
         try:
-            # Convert to absolute path if relative
-            if not os.path.isabs(file_path):
-                file_path = os.path.abspath(file_path)
+            # Confine the upload source to the workspace before it is read: reject
+            # traversal/absolute paths that escape CWD (arbitrary file read /
+            # exfiltration via a caller-supplied file_path).
+            file_path = str(validate_safe_path(file_path))
 
             # Check if file exists
             if not os.path.exists(file_path):
diff --git a/src/mcp_atlassian/jira/client.py b/src/mcp_atlassian/jira/client.py
index e091ff766901728d4a647f1f75b542808cc20db6..bcb54446ff658d3283e0e1c8b125d2865c178a91 100644
--- a/src/mcp_atlassian/jira/client.py
+++ b/src/mcp_atlassian/jira/client.py
@@ -23,6 +23,8 @@ from mcp_atlassian.utils.logging import (
 )
 from mcp_atlassian.utils.oauth import configure_oauth_session
 from mcp_atlassian.utils.ssl import configure_ssl_verification
+from mcp_atlassian.utils.ssrf_adapter import mount_ssrf_pinning
+from mcp_atlassian.utils.urls import make_ssrf_redirect_hook
 from mcp_atlassian.utils.user_agent import get_default_user_agent
 
 from ..models.jira.adf import markdown_to_adf
@@ -143,8 +145,18 @@ class JiraClient:
             client_key_password=self.config.client_key_password,
         )
 
-        # Apply opt-in HTTP hardening after SSL setup so SSLIgnoreAdapter, if
-        # mounted, also picks up the configured behavior.
+        # Validate redirects for SSRF on every outbound call from this session
+        # (covers direct _session.get() paths and global/stdio fetchers, not just
+        # the per-user HTTP path).
+        self.jira._session.hooks["response"].append(make_ssrf_redirect_hook())
+        # Pin DNS resolution against rebinding: resolve+validate once and connect
+        # to that address, closing the validate→reconnect TOCTOU. Preserves TLS SNI.
+        mount_ssrf_pinning(self.jira._session)
+
+        # Apply opt-in HTTP hardening after SSL setup and after the pinning
+        # adapter is mounted: these wrappers patch send() in place on whatever
+        # adapters are mounted now, so mounting the pinning adapter later would
+        # silently drop them.
         configure_retry(self.jira._session, service="Jira")
         configure_concurrency(self.jira._session, service="Jira")
         configure_rate_limit(self.jira._session, service="Jira")
diff --git a/src/mcp_atlassian/jira/search.py b/src/mcp_atlassian/jira/search.py
index 49d169e4a097d733bd3e33532de836a25d700d82..ca72b2accca49d6c2785bfdced76f17cbfe1fba7 100644
--- a/src/mcp_atlassian/jira/search.py
+++ b/src/mcp_atlassian/jira/search.py
@@ -21,6 +21,57 @@ logger = logging.getLogger("mcp-jira")
 class SearchMixin(JiraClient, IssueOperationsProto):
     """Mixin for Jira search operations."""
 
+    def _apply_projects_filter(
+        self, jql: str, projects_filter: str | None = None
+    ) -> str:
+        """Constrain a JQL query to the allowed projects (JIRA_PROJECTS_FILTER).
+
+        Every JQL-issuing path routes through here so none can escape the project
+        allowlist. ``config.projects_filter`` is a hard boundary and is always
+        applied; a caller-supplied ``projects_filter`` may only *narrow* within it
+        (both are ANDed), never replace it — otherwise the tool argument would
+        defeat the operator's allowlist in shared-credential deployments.
+        """
+        for filter_str in (self.config.projects_filter, projects_filter):
+            if filter_str:
+                jql = self._and_projects_filter(jql, filter_str)
+        return jql
+
+    def _and_projects_filter(self, jql: str, filter_to_use: str) -> str:
+        """AND a single comma-separated project allowlist into ``jql``."""
+        # Split by commas, and escape backslashes before double-quotes to prevent
+        # JQL-injection bypass of the quoting below.
+        projects = [p.strip() for p in filter_to_use.split(",")]
+        projects = [p.replace("\\", "\\\\").replace('"', '\\"') for p in projects]
+
+        if len(projects) == 1:
+            quoted = quote_jql_identifier_if_needed(projects[0])
+            project_query = f"project = {quoted}"
+        else:
+            quoted_projects = [quote_jql_identifier_if_needed(p) for p in projects]
+            projects_list = ", ".join(quoted_projects)
+            project_query = f"project IN ({projects_list})"
+
+        if not jql:
+            jql = project_query
+        elif jql.strip().upper().startswith("ORDER BY"):
+            jql = f"{project_query} {jql}"
+        else:
+            # Always AND the allowlist, even when the caller's query already names a
+            # project: a caller-supplied `project = X` must not be able to escape the
+            # configured allowlist (out-of-allowlist queries then return empty).
+            # Extract a trailing ORDER BY so the AND does not produce invalid JQL.
+            order_match = re.search(r"\s+(ORDER\s+BY\s+.*)$", jql, re.IGNORECASE)
+            if order_match:
+                order_clause = order_match.group(1)
+                jql_without_order = jql[: order_match.start()]
+                jql = f"({jql_without_order}) AND {project_query} {order_clause}"
+            else:
+                jql = f"({jql}) AND {project_query}"
+
+        logger.info(f"Applied projects filter to query: {jql}")
+        return jql
+
     @handle_auth_errors("Jira API")
     def search_issues(
         self,
@@ -43,7 +94,9 @@ class SearchMixin(JiraClient, IssueOperationsProto):
                   start from the first page.
             limit: Maximum issues to return
             expand: Optional items to expand (comma-separated)
-            projects_filter: Optional comma-separated list of project keys to filter by, overrides config
+            projects_filter: Optional comma-separated list of project keys to narrow
+                results within the configured allowlist (ANDed with config, never
+                replaces it)
             page_token: Optional pagination token from a previous search result.
                   Cloud only — Server/DC uses start for pagination.
 
@@ -60,56 +113,8 @@ class SearchMixin(JiraClient, IssueOperationsProto):
             # Sanitize JQL reserved words in project key values
             jql = sanitize_jql_reserved_words(jql)
 
-            # Use projects_filter parameter if provided, otherwise fall back to config
-            filter_to_use = projects_filter or self.config.projects_filter
-
-            # Apply projects filter if present
-            if filter_to_use:
-                # Split projects filter by commas and handle possible whitespace
-                projects = [p.strip() for p in filter_to_use.split(",")]
-
-                # Build the project filter query part
-                # Sanitize project names to prevent JQL injection
-                # Escape backslashes before double-quotes to prevent bypass
-                projects = [
-                    p.replace("\\", "\\\\").replace('"', '\\"') for p in projects
-                ]
-
-                if len(projects) == 1:
-                    quoted = quote_jql_identifier_if_needed(projects[0])
-                    project_query = f"project = {quoted}"
-                else:
-                    quoted_projects = [
-                        quote_jql_identifier_if_needed(p) for p in projects
-                    ]
-                    projects_list = ", ".join(quoted_projects)
-                    project_query = f"project IN ({projects_list})"
-
-                # Add the project filter to existing query
-                if not jql:
-                    # Empty JQL - just use project filter
-                    jql = project_query
-                elif jql.strip().upper().startswith("ORDER BY"):
-                    # JQL starts with ORDER BY - prepend project filter
-                    jql = f"{project_query} {jql}"
-                elif (
-                    "project = " not in jql.lower() and "project in" not in jql.lower()
-                ):
-                    # Only add if not already filtering by project
-                    # Extract ORDER BY clause if present to avoid invalid JQL
-                    order_match = re.search(
-                        r"\s+(ORDER\s+BY\s+.*)$", jql, re.IGNORECASE
-                    )
-                    if order_match:
-                        order_clause = order_match.group(1)
-                        jql_without_order = jql[: order_match.start()]
-                        jql = (
-                            f"({jql_without_order}) AND {project_query} {order_clause}"
-                        )
-                    else:
-                        jql = f"({jql}) AND {project_query}"
-
-                logger.info(f"Applied projects filter to query: {jql}")
+            # Constrain to the allowed projects (JIRA_PROJECTS_FILTER)
+            jql = self._apply_projects_filter(jql, projects_filter)
 
             # Convert fields to proper format if it's a list/tuple/set
             fields_param: str | None
@@ -240,6 +245,9 @@ class SearchMixin(JiraClient, IssueOperationsProto):
             # Sanitize JQL reserved words in project key values
             jql = sanitize_jql_reserved_words(jql) or jql
 
+            # Constrain board issues to the allowed projects (JIRA_PROJECTS_FILTER)
+            jql = self._apply_projects_filter(jql)
+
             # Determine fields_param
             fields_param = fields
             if fields_param is None:
@@ -298,11 +306,20 @@ class SearchMixin(JiraClient, IssueOperationsProto):
         Raises:
             Exception: If there is an error getting sprint issues
         """
+        # sprint_id is interpolated into JQL; require an integer to prevent
+        # JQL injection via a crafted non-numeric value.
+        try:
+            sprint_id_int = int(str(sprint_id).strip())
+        except (TypeError, ValueError) as e:
+            raise ValueError(
+                f"Invalid sprint_id {sprint_id!r}: must be an integer"
+            ) from e
+
         try:
             limit = clamp_limit(limit, context="jira.get_sprint_issues")
 
             # Use JQL search to get sprint issues with proper fields filtering
-            jql = f"sprint = {sprint_id}"
+            jql = f"sprint = {sprint_id_int}"
             return self.search_issues(
                 jql=jql,
                 fields=fields,
diff --git a/src/mcp_atlassian/servers/confluence.py b/src/mcp_atlassian/servers/confluence.py
index 3e78b79d1689472dd865a297fc97d488c06f2327..ff1c3e8f6b44f5e85f8437edf2c3a01462ee57f7 100644
--- a/src/mcp_atlassian/servers/confluence.py
+++ b/src/mcp_atlassian/servers/confluence.py
@@ -20,6 +20,7 @@ from mcp_atlassian.servers.dependencies import get_confluence_fetcher
 from mcp_atlassian.utils.decorators import (
     check_write_access,
 )
+from mcp_atlassian.utils.io import validate_safe_path
 from mcp_atlassian.utils.media import (
     ATTACHMENT_MAX_BYTES,
     fetch_and_encode_attachment,
@@ -124,15 +125,17 @@ def _resolve_page_content(content: str | None, content_file: str | None) -> str:
 
     Args:
         content: Inline page body (any supported content_format).
-        content_file: Absolute or relative filesystem path to read the body from.
-            Read as UTF-8.
+        content_file: Filesystem path to read the body from (UTF-8). Must
+            resolve inside the current working directory (workspace), the same
+            confinement contract as attachment paths.
 
     Returns:
         The resolved page body as a string.
 
     Raises:
-        ValueError: If neither or both arguments are supplied, or if the file does
-            not exist / is not a regular file.
+        ValueError: If neither or both arguments are supplied, if the file does
+            not exist / is not a regular file, or if the path escapes the
+            workspace.
         OSError: If the file exists but cannot be read.
     """
     has_content = content is not None
@@ -146,7 +149,10 @@ def _resolve_page_content(content: str | None, content_file: str | None) -> str:
     if content_file is None or content_file == "":
         raise ValueError("One of 'content' or 'content_file' must be provided.")
 
-    path = Path(content_file).expanduser()
+    # Confine the read to the workspace, same contract as attachment paths — an
+    # unconfined caller-supplied path is an arbitrary-file-read primitive (the
+    # file body is echoed back through the created/updated page).
+    path = validate_safe_path(Path(content_file).expanduser())
     if not path.is_file():
         msg = f"content_file does not exist or is not a regular file: {path}"
         raise ValueError(msg)
diff --git a/src/mcp_atlassian/servers/dependencies.py b/src/mcp_atlassian/servers/dependencies.py
index 9f945e9c1a2a2257bc72ec0be446f9550ed0a38c..8c32a0ebeb70404d28e5017e83ec7f5b14143e42 100644
--- a/src/mcp_atlassian/servers/dependencies.py
+++ b/src/mcp_atlassian/servers/dependencies.py
@@ -17,6 +17,7 @@ from starlette.requests import Request
 from mcp_atlassian.confluence import ConfluenceConfig, ConfluenceFetcher
 from mcp_atlassian.jira import JiraConfig, JiraFetcher
 from mcp_atlassian.servers.context import MainAppContext
+from mcp_atlassian.utils.env import is_env_truthy
 from mcp_atlassian.utils.oauth import OAuthConfig
 from mcp_atlassian.utils.urls import validate_url_for_ssrf
 
@@ -508,8 +509,10 @@ async def _get_fetcher(ctx: Context, spec: _ServiceSpec) -> Any:
     """
     fn_name = f"get_{spec.name.lower()}_fetcher"
     logger.debug(f"{fn_name}: ENTERED. Context ID: {id(ctx)}")
+    in_http_context = False
     try:
         request: Request = get_http_request()
+        in_http_context = True
         logger.debug(
             f"{fn_name}: In HTTP request context. "
             f"Request URL: {request.url}. "
@@ -592,6 +595,7 @@ async def _get_fetcher(ctx: Context, spec: _ServiceSpec) -> Any:
                 user_config,
                 "basic",
                 user_email=user_email,
+                attach_ssrf_hook=True,
             )
 
         # --- Branch 3: OAuth / PAT with token ---
@@ -641,6 +645,7 @@ async def _get_fetcher(ctx: Context, spec: _ServiceSpec) -> Any:
                 user_config,
                 "oauth_pat",
                 user_email=user_email,
+                attach_ssrf_hook=True,
             )
 
         else:
@@ -663,6 +668,17 @@ async def _get_fetcher(ctx: Context, spec: _ServiceSpec) -> Any:
         getattr(app_ctx, spec.config_attr, None) if app_ctx else None
     )
     if global_config_fallback:
+        # An HTTP request that reaches here has no per-user identity: serving it
+        # with the operator's global credentials lets any unauthenticated caller
+        # transact as the operator. Refuse unless explicitly opted in. Non-HTTP
+        # (stdio, single-user) is unaffected — the operator is the user there.
+        if in_http_context and not is_env_truthy("ALLOW_GLOBAL_CRED_FALLBACK"):
+            raise ValueError(
+                f"{spec.name} client (fetcher) not available: refusing to serve an "
+                "unauthenticated request with the operator's global credentials. "
+                "Provide a user token, or set ALLOW_GLOBAL_CRED_FALLBACK=true to "
+                "allow the global-credential fallback (single-user deployments only)."
+            )
         logger.debug(
             f"{fn_name}: Using global {spec.name}Fetcher "
             "from lifespan_context. "
diff --git a/src/mcp_atlassian/servers/main.py b/src/mcp_atlassian/servers/main.py
index 43f70a891ceeb9f02ce69fdc29af0247d500e6ff..454c982abdcc45e2ba7a111e81e1f28690c4fa94 100644
--- a/src/mcp_atlassian/servers/main.py
+++ b/src/mcp_atlassian/servers/main.py
@@ -12,6 +12,7 @@ from urllib.parse import urlparse
 from cachetools import TTLCache
 from fastmcp import FastMCP
 from fastmcp import settings as fastmcp_settings
+from fastmcp.exceptions import NotFoundError
 from fastmcp.server.event_store import EventStore
 from fastmcp.server.http import StarletteWithLifespan
 from fastmcp.tools import Tool as FastMCPTool
@@ -209,14 +210,15 @@ class AtlassianMCP(FastMCP[MainAppContext]):
             return self._active_streamable_http_path
         return self._normalize_http_path(fastmcp_settings.streamable_http_path)
 
-    async def _list_tools_mcp(self) -> list[MCPTool]:
-        # Filter tools based on enabled_tools, read_only mode, and service configuration from the lifespan context.
+    def _tool_filter_context(self) -> dict[str, Any] | None:
+        """Gather the per-request tool-enablement context (read-only mode, enabled
+        tools/toolsets, service availability) from the lifespan/request context.
+
+        Returns None when the lifespan context is unavailable.
+        """
         req_context = self._mcp_server.request_context
         if req_context is None or req_context.lifespan_context is None:
-            logger.warning(
-                "Lifespan context not available during _list_tools_mcp call."
-            )
-            return []
+            return None
 
         lifespan_ctx_dict = req_context.lifespan_context
         app_lifespan_state: MainAppContext | None = (
@@ -246,13 +248,78 @@ class AtlassianMCP(FastMCP[MainAppContext]):
             service_headers = getattr(request.state, "atlassian_service_headers", {})
             if service_headers:
                 header_based_services = get_available_services(service_headers)
-                logger.debug(
-                    f"Header-based service availability: {header_based_services}"
-                )
 
-        logger.debug(
-            f"_list_tools_mcp: read_only={read_only}, enabled_tools_filter={enabled_tools_filter}, header_services={header_based_services}"
-        )
+        return {
+            "read_only": read_only,
+            "enabled_tools_filter": enabled_tools_filter,
+            "enabled_toolsets_filter": enabled_toolsets_filter,
+            "app_lifespan_state": app_lifespan_state,
+            "header_based_services": header_based_services,
+        }
+
+    def _is_tool_authorized(
+        self, registered_name: str, tool_obj: FastMCPTool, ctx: dict[str, Any]
+    ) -> bool:
+        """Authorization boundaries enforced at BOTH listing and call time: the
+        ENABLED_TOOLS allowlist, the enabled toolsets, and read-only mode.
+
+        These are security boundaries — a tool excluded here must not be invocable
+        by name. (Service availability, below, is a listing-only UX filter: an
+        unavailable-service tool simply fails naturally if called.)
+        """
+        tool_tags = tool_obj.tags
+        if not should_include_tool_by_toolset(
+            tool_tags, ctx["enabled_toolsets_filter"]
+        ):
+            return False
+        if not should_include_tool(registered_name, ctx["enabled_tools_filter"]):
+            return False
+        if ctx["read_only"] and "write" in tool_tags:
+            return False
+        return True
+
+    def _is_tool_enabled(
+        self, registered_name: str, tool_obj: FastMCPTool, ctx: dict[str, Any]
+    ) -> bool:
+        """Listing filter: the tool is authorized AND its backing service is
+        configured/available (the latter is a listing-only graceful-hide)."""
+        if not self._is_tool_authorized(registered_name, tool_obj, ctx):
+            return False
+
+        app_lifespan_state = ctx["app_lifespan_state"]
+        header_based_services = ctx["header_based_services"]
+        tool_tags = tool_obj.tags
+
+        is_jira_tool = "jira" in tool_tags
+        is_confluence_tool = "confluence" in tool_tags
+        if app_lifespan_state:
+            jira_available = (
+                app_lifespan_state.full_jira_config is not None
+            ) or header_based_services.get("jira", False)
+            confluence_available = (
+                app_lifespan_state.full_confluence_config is not None
+            ) or header_based_services.get("confluence", False)
+            if is_jira_tool and not jira_available:
+                return False
+            if is_confluence_tool and not confluence_available:
+                return False
+        elif is_jira_tool or is_confluence_tool:
+            if is_jira_tool and not header_based_services.get("jira", False):
+                return False
+            if is_confluence_tool and not header_based_services.get(
+                "confluence", False
+            ):
+                return False
+        return True
+
+    async def _list_tools_mcp(self) -> list[MCPTool]:
+        # Filter tools based on enabled_tools, read_only mode, and service configuration from the lifespan context.
+        ctx = self._tool_filter_context()
+        if ctx is None:
+            logger.warning(
+                "Lifespan context not available during _list_tools_mcp call."
+            )
+            return []
 
         all_tools: dict[str, FastMCPTool] = await self.get_tools()
         logger.debug(
@@ -261,64 +328,9 @@ class AtlassianMCP(FastMCP[MainAppContext]):
 
         filtered_tools: list[MCPTool] = []
         for registered_name, tool_obj in all_tools.items():
-            tool_tags = tool_obj.tags
-
-            if not should_include_tool_by_toolset(tool_tags, enabled_toolsets_filter):
-                logger.debug(
-                    f"Excluding tool '{registered_name}' (toolset not enabled)"
-                )
+            if not self._is_tool_enabled(registered_name, tool_obj, ctx):
+                logger.debug(f"Excluding tool '{registered_name}' (filtered)")
                 continue
-
-            if not should_include_tool(registered_name, enabled_tools_filter):
-                logger.debug(f"Excluding tool '{registered_name}' (not enabled)")
-                continue
-
-            if tool_obj and read_only and "write" in tool_tags:
-                logger.debug(
-                    f"Excluding tool '{registered_name}' due to read-only mode and 'write' tag"
-                )
-                continue
-
-            # Exclude Jira/Confluence tools if config is not fully authenticated
-            is_jira_tool = "jira" in tool_tags
-            is_confluence_tool = "confluence" in tool_tags
-            service_configured_and_available = True
-            if app_lifespan_state:
-                jira_available = (
-                    app_lifespan_state.full_jira_config is not None
-                ) or header_based_services.get("jira", False)
-                confluence_available = (
-                    app_lifespan_state.full_confluence_config is not None
-                ) or header_based_services.get("confluence", False)
-
-                if is_jira_tool and not jira_available:
-                    logger.debug(
-                        f"Excluding Jira tool '{registered_name}' as Jira configuration/authentication is incomplete and no header-based auth available."
-                    )
-                    service_configured_and_available = False
-                if is_confluence_tool and not confluence_available:
-                    logger.debug(
-                        f"Excluding Confluence tool '{registered_name}' as Confluence configuration/authentication is incomplete and no header-based auth available."
-                    )
-                    service_configured_and_available = False
-            elif is_jira_tool or is_confluence_tool:
-                jira_available = header_based_services.get("jira", False)
-                confluence_available = header_based_services.get("confluence", False)
-
-                if is_jira_tool and not jira_available:
-                    logger.debug(
-                        f"Excluding Jira tool '{registered_name}' as no Jira authentication available."
-                    )
-                    service_configured_and_available = False
-                if is_confluence_tool and not confluence_available:
-                    logger.debug(
-                        f"Excluding Confluence tool '{registered_name}' as no Confluence authentication available."
-                    )
-                    service_configured_and_available = False
-
-            if not service_configured_and_available:
-                continue
-
             mcp_tool = tool_obj.to_mcp_tool(name=registered_name)
             _sanitize_schema_for_compatibility(mcp_tool)
             filtered_tools.append(mcp_tool)
@@ -328,6 +340,21 @@ class AtlassianMCP(FastMCP[MainAppContext]):
         )
         return filtered_tools
 
+    async def _call_tool_mcp(self, key: str, arguments: dict[str, Any]) -> Any:
+        # Enforce the same enablement filter at call time as at listing time, so a
+        # tool hidden from the listing (read-only mode, not in ENABLED_TOOLS, toolset
+        # disabled, or service unavailable) cannot be invoked directly by name.
+        # Denials look identical to an unknown tool (no exists-but-disabled leak).
+        ctx = self._tool_filter_context()
+        if ctx is not None:
+            all_tools = await self.get_tools()
+            tool_obj = all_tools.get(key)
+            if tool_obj is not None and not self._is_tool_authorized(
+                key, tool_obj, ctx
+            ):
+                raise NotFoundError(f"Unknown tool: {key}")
+        return await super()._call_tool_mcp(key, arguments)
+
     def http_app(
         self,
         path: str | None = None,
@@ -442,6 +469,28 @@ class UserTokenMiddleware:
             await self._send_json_error_response(safe_send, 401, auth_error)
             return  # Don't call self.app - request is rejected
 
+        # Reject unauthenticated MCP requests at the transport boundary: with no
+        # user identity, the downstream handler would fall back to the operator's
+        # global credentials, so any unauthenticated caller would transact as the
+        # operator. Refuse unless explicitly opted in (opt-in global-fallback gate).
+        if (
+            not ignore_header_auth
+            and self.mcp_server_ref
+            and self._should_process_auth(scope_copy)
+            and not scope_copy["state"].get("user_atlassian_auth_type")
+            and not is_env_truthy("ALLOW_GLOBAL_CRED_FALLBACK")
+        ):
+            logger.warning(
+                "UserTokenMiddleware: rejecting unauthenticated MCP request "
+                "(no user identity and ALLOW_GLOBAL_CRED_FALLBACK is off)"
+            )
+            await self._send_json_error_response(
+                safe_send,
+                401,
+                "Authentication required: no Atlassian credentials were provided.",
+            )
+            return  # Don't call self.app - request is rejected
+
         # Call the next application with modified scope and safe send wrapper
         await self.app(scope_copy, receive, safe_send)
 
diff --git a/src/mcp_atlassian/utils/oauth.py b/src/mcp_atlassian/utils/oauth.py
index 010b64265a5921ca150b71a3aeeea910116fbabd..8c74b618de2ce73f15eca5df78ec7565b31b86f7 100644
--- a/src/mcp_atlassian/utils/oauth.py
+++ b/src/mcp_atlassian/utils/oauth.py
@@ -398,9 +398,10 @@ class OAuthConfig:
                         will use the current object attributes.
         """
         try:
-            # Create the directory if it doesn't exist
+            # Create the directory if it doesn't exist (owner-only)
             token_dir = Path.home() / ".mcp-atlassian"
             token_dir.mkdir(exist_ok=True)
+            os.chmod(token_dir, 0o700)
 
             # Save the tokens to a file
             token_path = token_dir / f"oauth-{self.client_id}.json"
@@ -414,8 +415,12 @@ class OAuthConfig:
                     "base_url": self.base_url,
                 }
 
-            with open(token_path, "w") as f:
+            # Persisted tokens are secrets: create/truncate owner-only so they are
+            # never group/world-readable, independent of the process umask.
+            fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
+            with os.fdopen(fd, "w") as f:
                 json.dump(token_data, f)
+            os.chmod(token_path, 0o600)
 
             logger.debug(f"Saved OAuth tokens to file {token_path} (fallback storage)")
         except Exception as e:
diff --git a/src/mcp_atlassian/utils/oauth_setup.py b/src/mcp_atlassian/utils/oauth_setup.py
index a77f0bb87363c18de18f71d47551e2a4c2eebc66..fbe9b4a358dec7d4687b009d3a4d7d42b5d4a06a 100644
--- a/src/mcp_atlassian/utils/oauth_setup.py
+++ b/src/mcp_atlassian/utils/oauth_setup.py
@@ -17,6 +17,7 @@ import time
 import urllib.parse
 import webbrowser
 from dataclasses import dataclass
+from html import escape as html_escape
 
 from ..utils.oauth import OAuthConfig
 
@@ -85,6 +86,10 @@ class CallbackHandler(http.server.BaseHTTPRequestHandler):
         self.send_header("Content-type", "text/html")
         self.end_headers()
 
+        # Escape the message: it can carry attacker-controlled OAuth callback
+        # text (e.g. the error query param), so raw interpolation is reflected XSS.
+        escaped_message = html_escape(message)
+
         html = f"""
         <!DOCTYPE html>
         <html>
@@ -122,7 +127,7 @@ class CallbackHandler(http.server.BaseHTTPRequestHandler):
         <body>
             <h1>Atlassian OAuth Authorization</h1>
             <div class="message {"success" if status == 200 else "error"}">
-                <p>{message}</p>
+                <p>{escaped_message}</p>
             </div>
             <p>This window will automatically close in <span class="countdown">5</span> seconds...</p>
             <button onclick="window.close()">Close Window Now</button>
diff --git a/src/mcp_atlassian/utils/ssl.py b/src/mcp_atlassian/utils/ssl.py
index 8469fda5715a600157cfa4047878cec4f7cbeed8..7ef96ac656f8e02843ee8e9e256d6daf230b8bad 100644
--- a/src/mcp_atlassian/utils/ssl.py
+++ b/src/mcp_atlassian/utils/ssl.py
@@ -9,6 +9,8 @@ from requests.adapters import HTTPAdapter
 from requests.sessions import Session
 from urllib3.poolmanager import PoolManager
 
+from .ssrf_adapter import _PinnedHTTPConnectionPool, _PinnedHTTPSConnectionPool
+
 logger = logging.getLogger("mcp-atlassian")
 
 
@@ -48,6 +50,14 @@ class SSLIgnoreAdapter(HTTPAdapter):
             ssl_context=context,
             **pool_kwargs,
         )
+        # This adapter mounts at a more specific prefix than the session-wide
+        # SsrfPinningAdapter and would otherwise silently replace it — keep the
+        # DNS-pinning connection classes so disabling SSL verification does not
+        # also disable the SSRF rebinding guard.
+        self.poolmanager.pool_classes_by_scheme = {  # type: ignore[attr-defined]
+            "http": _PinnedHTTPConnectionPool,
+            "https": _PinnedHTTPSConnectionPool,
+        }
 
     def cert_verify(self, conn: Any, url: str, verify: bool, cert: Any | None) -> None:
         """Override cert verification to disable SSL verification.
diff --git a/src/mcp_atlassian/utils/ssrf_adapter.py b/src/mcp_atlassian/utils/ssrf_adapter.py
new file mode 100644
index 0000000000000000000000000000000000000000..223a067772fdeff82f8b95efca9097d06750d8e7
--- /dev/null
+++ b/src/mcp_atlassian/utils/ssrf_adapter.py
@@ -0,0 +1,158 @@
+"""A requests transport adapter that pins DNS resolution against SSRF.
+
+``validate_url_for_ssrf`` resolves and checks a host once (in middleware), but the
+outbound request re-resolves the hostname at connect time, so a DNS-rebinding
+response can swap in an internal address between validation and connection — the
+TOCTOU that bypasses a validate-then-reconnect SSRF guard (GHSA-49xv, 72fm, 489g).
+
+This adapter closes that window at the connection itself: it resolves each host
+exactly once, rejects any candidate address that is not globally routable
+(cloud-metadata / private / loopback), and connects to that same validated
+address — there is no separate re-resolution to rebind. The original hostname is
+preserved for TLS SNI and certificate verification, so HTTPS is unaffected.
+
+Operator-trusted hosts — the configured ``JIRA_URL`` / ``CONFLUENCE_URL`` hosts
+and ``MCP_ALLOWED_URL_DOMAINS`` entries — are exempt from the non-global
+rejection (on-prem DC instances legitimately live on private networks or
+localhost). Those values come from the server environment, which an attacker
+cannot influence through a request, so the rebinding guard is not weakened for
+caller-supplied URLs. The single-resolution pin still applies to every host.
+"""
+
+import os
+import socket
+from typing import Any
+from urllib.parse import urlparse
+
+from requests import Session
+from requests.adapters import HTTPAdapter
+from urllib3.connection import HTTPConnection, HTTPSConnection
+from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
+from urllib3.exceptions import NewConnectionError
+from urllib3.poolmanager import PoolManager
+
+from .urls import _check_ip_address, _get_domain_allowlist, _hostname_matches_allowlist
+
+
+def _operator_trusted_hosts() -> list[str]:
+    """Hosts the operator explicitly configured or allowlisted via environment."""
+    hosts = []
+    for env in ("JIRA_URL", "CONFLUENCE_URL"):
+        raw = os.environ.get(env, "").strip()
+        if raw:
+            hostname = urlparse(raw).hostname
+            if hostname:
+                hosts.append(hostname.lower())
+    hosts.extend(_get_domain_allowlist() or [])
+    return hosts
+
+
+def _pinned_create_connection(
+    address: tuple[str, int],
+    timeout: Any = socket._GLOBAL_DEFAULT_TIMEOUT,  # type: ignore[attr-defined]  # noqa: SLF001
+    source_address: tuple[str, int] | None = None,
+    socket_options: Any = None,
+) -> socket.socket:
+    """Resolve once, reject non-global addresses, connect to the validated IP.
+
+    A single ``getaddrinfo`` result is both validated and connected to, so a
+    rebinding name cannot return a public IP to the check and a private IP to the
+    connection.
+    """
+    host, port = address
+    host_trusted = _hostname_matches_allowlist(host, _operator_trusted_hosts())
+    err: Exception | None = None
+    for af, socktype, proto, _canonname, sa in socket.getaddrinfo(
+        host, port, 0, socket.SOCK_STREAM
+    ):
+        ip = sa[0]
+        if not host_trusted and _check_ip_address(ip) is not None:
+            msg = f"SSRF blocked: {host} resolves to non-global address {ip}"
+            raise OSError(msg)
+        sock = None
+        try:
+            sock = socket.socket(af, socktype, proto)
+            if socket_options:
+                for opt in socket_options:
+                    sock.setsockopt(*opt)
+            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:  # type: ignore[attr-defined]  # noqa: SLF001
+                sock.settimeout(timeout)
+            if source_address:
+                sock.bind(source_address)
+            sock.connect(sa)
+            return sock
+        except OSError as e:
+            err = e
+            if sock is not None:
+                sock.close()
+    if err is not None:
+        raise err
+    msg = f"getaddrinfo returned no addresses for {host}"
+    raise OSError(msg)
+
+
+class _PinnedConnMixin:
+    """Route socket creation through the validating, single-resolution connector."""
+
+    def _new_conn(self) -> socket.socket:
+        try:
+            return _pinned_create_connection(
+                (self._dns_host, self.port),  # type: ignore[attr-defined]
+                self.timeout,  # type: ignore[attr-defined]
+                source_address=self.source_address,  # type: ignore[attr-defined]
+                socket_options=self.socket_options,  # type: ignore[attr-defined]
+            )
+        except OSError as e:
+            raise NewConnectionError(
+                self,  # type: ignore[arg-type]
+                f"Failed to establish a new connection: {e}",
+            ) from e
+
+
+class _PinnedHTTPConnection(_PinnedConnMixin, HTTPConnection):
+    pass
+
+
+class _PinnedHTTPSConnection(_PinnedConnMixin, HTTPSConnection):
+    pass
+
+
+class _PinnedHTTPConnectionPool(HTTPConnectionPool):
+    ConnectionCls = _PinnedHTTPConnection
+
+
+class _PinnedHTTPSConnectionPool(HTTPSConnectionPool):
+    ConnectionCls = _PinnedHTTPSConnection
+
+
+class SsrfPinningAdapter(HTTPAdapter):
+    """A requests adapter that validates and pins DNS resolution for every call."""
+
+    def init_poolmanager(
+        self, connections: int, maxsize: int, block: bool = False, **pool_kwargs: Any
+    ) -> None:
+        self.poolmanager = PoolManager(
+            num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs
+        )
+        # Runtime attribute of urllib3's PoolManager; absent from the type stubs.
+        self.poolmanager.pool_classes_by_scheme = {  # type: ignore[attr-defined]
+            "http": _PinnedHTTPConnectionPool,
+            "https": _PinnedHTTPSConnectionPool,
+        }
+
+
+def mount_ssrf_pinning(session: Session) -> None:
+    """Mount the SSRF DNS-pinning adapter for http/https on ``session``.
+
+    Preserves the retry policy of any adapter already mounted (e.g. the one the
+    Atlassian client configures), so pinning does not silently drop retries.
+    """
+    for scheme in ("https://", "http://"):
+        existing = session.adapters.get(scheme)
+        retries = getattr(existing, "max_retries", None)
+        adapter = (
+            SsrfPinningAdapter(max_retries=retries)
+            if retries is not None
+            else SsrfPinningAdapter()
+        )
+        session.mount(scheme, adapter)
diff --git a/src/mcp_atlassian/utils/urls.py b/src/mcp_atlassian/utils/urls.py
index 4468643bc361aec5dc44dd5161ab2587d00add82..94f81afa0d89226e4ba52b6c6f2a6bcac36964be 100644
--- a/src/mcp_atlassian/utils/urls.py
+++ b/src/mcp_atlassian/utils/urls.py
@@ -4,9 +4,29 @@ import ipaddress
 import os
 import re
 import socket
+from collections.abc import Callable
+from typing import Any
 from urllib.parse import urlparse
 
 
+def make_ssrf_redirect_hook() -> Callable[..., Any]:
+    """Return a requests ``response`` hook that blocks SSRF-unsafe redirects.
+
+    Attach to any session (``session.hooks["response"].append(...)``) so that an
+    open redirect cannot steer an outbound request to an internal/metadata host.
+    """
+
+    def hook(response: Any, **kwargs: Any) -> Any:
+        if response.is_redirect:
+            error = validate_url_for_ssrf(response.headers.get("Location", ""))
+            if error:
+                response.close()
+                raise ValueError(f"Redirect blocked (SSRF): {error}")
+        return response
+
+    return hook
+
+
 def resolve_relative_url(url: str, base_url: str) -> str:
     """Resolve a relative URL against a base URL.
 
@@ -89,6 +109,12 @@ def validate_url_for_ssrf(url: str) -> str | None:
     if parsed.scheme not in ("http", "https"):
         return f"Blocked scheme: {parsed.scheme} (only http/https allowed)"
 
+    # requests (and browsers, per WHATWG) treat a backslash in the authority as a
+    # path separator, so "http://localhost\@evil.com/" parses (urlparse) to host
+    # evil.com but actually connects to localhost. Reject the parse mismatch.
+    if "\\" in parsed.netloc:
+        return f"Blocked backslash in URL authority: {url}"
+
     hostname = parsed.hostname
     if not hostname:
         return "No hostname in URL"

# (19 test/doc file(s) of the upstream fix omitted here)

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### pyproject.toml
```
[project]
name = "mcp-atlassian"
dynamic = ["version"]
description = "The Model Context Protocol (MCP) Atlassian integration is an open-source implementation that bridges Atlassian products (Jira and Confluence) with AI language models following Anthropic's MCP specification. This project enables secure, contextual AI interactions with Atlassian tools while maintaining data privacy and security. Key features include:"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "atlassian-python-api>=4.0.0",
    "requests[socks]>=2.31.0",
    "beautifulsoup4>=4.12.3",
    "httpx>=0.28.0",
    "mcp>=1.8.0,<2.0.0",
    "fastmcp>=2.14.0,<2.15.0",
    "fakeredis>=2.32.1,<2.35.0",
    "python-dotenv>=1.0.1",
    "markdownify>=0.11.6",
    "markdown>=3.7.0",
    "markdown-to-confluence>=0.3.4,<0.4.0",
    "pydantic>=2.10.6,<3.0",
    "trio>=0.29.0",
    "click>=8.1.7",
    "uvicorn>=0.27.1",
    "starlette>=0.49.1",
    "urllib3>=2.6.3",
    "thefuzz>=0.22.1",
    "python-dateutil>=2.9.0.post0",
    "types-python-dateutil>=2.9.0.20241206",
    "keyring>=25.6.0",
    "cachetools>=5.0.0",
    "types-cachetools>=5.5.0.20240820",
    "unidecode>=1.3.0",
    "truststore>=0.10.0",
    "tzdata>=2024.1; platform_system=='Windows'",
]
[[project.authors]]
name = "sooperset"
email = "soomiles.dev@gmail.com"

[build-system]
requires = ["hatchling", "uv-dynamic-versioning>=0.7.0"]
build-backend = "hatchling.build"

[project.scripts]
mcp-atlassian = "mcp_atlassian:main"

[dependency-groups]
dev = [
    "uv>=0.1.0",
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-anyio>=0.0.0",
    "pre-commit>=3.6.0",
    "ruff>=0.3.0",
    "black>=24.2.0",
    "mypy>=1.8.0",
    "mcp[cli]>=1.3.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "types-pyyaml>=6.0"
]

[tool.pytest.ini_options]
markers = [
    "integration: mark test as requiring integration with real services",
    "dc_e2e: mark test as requiring DC instances (Jira DC + Confluence DC)",
    "cloud_e2e: mark test as requiring Cloud instances (Jira Cloud + Confluence Cloud)",
]

[tool.ruff]
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]
line-length = 88
indent-width = 4
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "B", "W", "I", "N", "UP", "ANN", "S", "BLE", "FBT", "C4", "DTZ", "T10", "EM", "ISC", "ICN"]
ignore = ["ANN401", "EM101"]
fixable = ["ALL"]
unfixable = []
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S", "ANN", "B017"]
"tests/fixtures/*.py" = ["E501"]
"src/mcp_atlassian/server.py" = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = false
warn_no_return = true
warn_unreachable = true
strict_equality = true
strict_optional = true
disallow_subclassing_any = true
warn_incomplete_stub = true
exclude = "^src/"
explicit_package_bases = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
check_untyped_defs = false

[[tool.mypy.overrides]]
module = "atlassian.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "markdownify.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "src.mcp_atlassian.*"
disallow_untyped_defs = false

[tool.hatch.version]
source = "uv-dynamic-versioning"

[tool.uv-dynamic-versioning]
vcs = "git"
style = "pep440"
bump = true
fallback-version = "0.0.0"

```

### src/mcp_atlassian/confluence/attachments.py
```
"""Attachment operations for Confluence API."""

import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any

from ..models.confluence import ConfluenceAttachment
from ..utils.io import validate_safe_path
from ..utils.urls import resolve_relative_url
from .client import ConfluenceClient
from .protocols import AttachmentsOperationsProto
from .v2_adapter import ConfluenceV2Adapter

# Configure logging
logger = logging.getLogger("mcp-confluence")


class AttachmentsMixin(ConfluenceClient, AttachmentsOperationsProto):
    """Mixin for Confluence attachment operations."""

    @property
    def _v2_adapter(self) -> ConfluenceV2Adapter | None:
        """Get v2 API adapter for OAuth authentication.

        Returns:
            ConfluenceV2Adapter instance if OAuth is configured, None otherwise
        """
        if self.config.auth_type == "oauth" and self.config.is_cloud:
            return ConfluenceV2Adapter(
                session=self.confluence._session, base_url=self.confluence.url
            )
        return None

    def _rest_base_url(self) -> str:
        """Return the REST API base URL, adding the Cloud ``/wiki`` prefix.

        On Confluence Cloud, ``config.url`` is the bare site URL
        (``https://site.atlassian.net``) but the REST API is served under
        ``/wiki``. Hand-built URLs must include this prefix or requests 404.
        The ``endswith`` guard avoids producing ``/wiki/wiki`` when the
        configured URL already includes the prefix.

        Returns:
            The base URL to use for direct REST API calls.
        """
        base_url = self.config.url.rstrip("/")
        if self.config.is_cloud and not base_url.endswith("/wiki"):
            base_url = f"{base_url}/wiki"
        return base_url

    def _resolve_attachment_download_url(
        self,
        download_url: str | None,
        attachment_id: str | None = None,
        content_id: str | None = None,
    ) -> str:
        """Resolve an attachment's download URL to an absolute URL.

        Confluence Cloud removed the legacy ``/download/attachments/{cid}/{file}``
        endpoint that the attachment's ``_links.download`` still points to; it now
        returns 401 for API-token / scoped-token auth (while metadata endpoints
        keep working). Depending on ``config.attachment_download_use_v1`` this
        rewrites the link to the v1 REST endpoint
        ``/rest/api/content/{cid}/child/attachment/{aid}/download`` (which still
        authenticates correctly):

        - ``None`` (default): auto — v1 on Cloud, the legacy link on Server/DC.
        - ``True``: always use v1.
        - ``False``: always use the legacy link.

        Args:
            download_url: The (possibly relative) download link from the API.
            attachment_id: The attachment ID (e.g. ``att123``); required for v1.
            content_id: The parent content ID. If omitted, it is parsed from the
                legacy download link.

        Returns:
            An absolute URL to fetch the attachment binary from, or an empty
            string when ``download_url`` is falsy.
        """
        resolved = (
            resolve_relative_url(download_url, self.config.url) if download_url else ""
        )
        use_v1 = self.config.attachment_download_use_v1
        if use_v1 is None:
            # Auto: Cloud removed the legacy endpoint, so default to v1 there;
            # Server/DC keeps the legacy link.
            use_v1 = self.config.is_cloud
        if not (use_v1 and attachment_id and download_url):
            return resolved

        parsed = urllib.parse.urlsplit(download_url)
        if not content_id:
            # Legacy path form: /download/attachments/{content_id}/{filename}
            # (match with or without a leading slash on the path).
            marker = "download/attachments/"
            if marker not in parsed.path:
                logger.debug(
                    "Could not derive content_id from download URL %s; "
                    "falling back to the original link",
                    download_url,
                )
                return resolved
            content_id = parsed.path.split(marker, 1)[1].split("/", 1)[0]

        base = self._rest_base_url()
        # v1 "Get attachment download" endpoint — not part of the deprecated
        # /download/attachments/... paths. See:
        # https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content---attachments/
        v1_url = (
            f"{base}/rest/api/content/{content_id}"
            f"/child/attachment/{attachment_id}/download"
        )
        # Keep only the documented ``version`` query param (the endpoint honours
        # it) so a version-specific link still resolves to that version; drop the
        # other legacy params (api / cacheVersion / modificationDate).
        version = urllib.parse.parse_qs(parsed.query).get("version", [None])[0]
        if version:
            v1_url = f"{v1_url}?{urllib.parse.urlencode({'version': version})}"
        return v1_url

    def upload_attachment(
        self,
        content_id: str,
        file_path: str,
        comment: str | None = None,
        minor_edit: bool = True,
    ) -> dict[str, Any]:
        """
        Upload a single attachment to Confluence content.

        Args:
            content_id: The Confluence content ID
            file_path: The path to the file to upload
            comment: Optional comment for the attachment
            minor_edit: Whether this is a minor edit (default: True)

        Returns:
            A dictionary with upload result information
        """
        if not content_id:
            logger.error("No content ID provided for attachment upload")
            return {"success": False, "error": "No content ID provided"}

        if not file_path:
            logger.error("No file path provided for attachment upload")
            return {"success": False, "error": "No file path provided"}

        try:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {"success": False, "error": f"File not found: {file_path}"}

            logger.info(
                f"Uploading attachment from {file_path} to content {content_id} (minor_edit={minor_edit})"
            )

            # Use direct REST API call to support minorEdit parameter
            filename = os.path.basename(file_path)
            attachment = self._upload_attachment_direct(
                content_id, file_path, filename, comment, minor_edit
            )

            if attachment:
                file_size = os.path.getsize(file_path)
                logger.info(
                    f"Successfully uploaded attachment {filename} to content {content_id} (size: {file_size} bytes)"
                )
                return {
                    "success": True,
                    "content_id": content_id,
                    "filename": filename,
                    "size": file_size,
                    "id": attachment.get("id")
                    if isinstance(attachment, dict)
                    else None,
                }
            else:
                logger.error(
                    f"Failed to upload attachment {filename} to content {content_id}"
                )
                return {
                    "success": False,
                    "error": f"Failed to upload attachment {filename} to content {content_id}",
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error uploading attachment: {error_msg}")
            return {"success": False, "error": error_msg}

    def upload_attachments(
        self,
        content_id: str,
        file_paths: list[str],
        comment: str | None = None,
        minor_edit: bool = True,
    ) -> dict[str, Any]:
        """
        Upload multiple attachments to Confluence content.

        Args:
            content_id: The Confluence content ID
            file_paths: List of paths to files to upload
            comment: Optional comment for the attachments
            minor_edit: Whether this is a minor edit (default: True)

        Returns:
            A dictionary with upload results
        """
        if not content_id:
            logger.error("No content ID provided for attachment upload")
            return {"success": False, "error": "No content ID provided"}

        if not file_paths:
            logger.error("No file paths provided for attachment upload")
            return {"success": False, "error": "No file paths provided"}

        logger.info(f"Uploading {len(file_paths)} attachments to content {content_id}")

        # Upload each attachment
        uploaded = []
        failed = []

        for file_path in file_paths:
            result = self.upload_attachment(content_id, file_path, comment, minor_edit)

            if result.get("success"):
                uploaded.append(
                    {
                        "filename": result.get("filename"),
                        "size": result.get("size"),
                        "id": result.get("id"),
                    }
                )
            else:
                failed.append(
                    {
                        "filename": os.path.basename(file_path),
                        "error": result.get("error"),
                    }
                )

        return {
            "success": True,
            "content_id": content_id,
            "total": len(file_paths),
            "uploaded": uploaded,
            "failed": failed,
        }

    def upload_attachment_from_content(
        self,
        content_id: str,
        filename: str,
        content: bytes,
        comment: str | None = None,
        minor_edit: bool = True,
    ) -> dict[str, Any]:
        """
        Upload a single attachment from in-memory bytes.

        This is the filesystem-free counterpart to ``upload_attachment``. It is
        intended for deployments where the server cannot read host file paths
        (for example, a remote or containerized MCP server): the caller provides
        the raw file content directly instead of a path.

        Args:
            content_id: The Confluence content ID
            filename: Name of the attachment (determines title and file type)
            content: Raw file bytes to upload
            comment: Optional comment for the attachment
            minor_edit: Whether this is a minor edit (default: True)

        Returns:
            A dictionary with upload result information
        """
        if not content_id:
            logger.error("No content ID provided for attachment upload")
            return {"success": False, "error": "No content ID provided"}

        if not filename:
            logger.error("No filename provided for attachment upload")
            return {"success": False, "error": "No filename provided"}

        if content is None:
            logger.error("No file content provided for attachment upload")
            return {"success": False, "error": "No file content provided"}

        try:
            logger.info(
                f"Uploading attachment {filename} ({len(content)} bytes) to "
                f"content {content_id} (minor_edit={minor_edit})"
            )

            attachment = self._upload_attachment_from_bytes(
                content_id, filename, content, comment, minor_edit
            )

            if attachment:
                logger.info(
                    f"Successfully uploaded attachment {filename} to content "
                    f"{content_id} (size: {len(content)} bytes)"
                )
                return {
                    "success": True,
                    "content_id": content_id,
                    "filename": filename,
                    "size": len(content),
                    "id": attachment.get("id")
                    if isinstance(attachment, dict)
                    else None,
                }

            logger.error(
                f"Failed to upload attachment {filename} to content {content_id}"
            )
            return {
                "success": False,
                "error": (
                    f"Failed to upload attachment {filename} to content {content_id}"
                ),
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error uploading attachment from content: {error_msg}")
            return {"success": False, "error": error_msg}

    def fetch_attachment_content(self, url: str) -> bytes | None:
        """Fetch attachment content into memory.

        Args:
            url: The URL of the attachment to download.

        Returns:
            The raw bytes of the attachment, or None on failure.
        """
        if not url:
            logger.error("No URL provided for attachment fetch")
            return None

        try:
            logger.info(f"Fetching attachment from {url}")
            response = self.confluence._session.get(url, stream=True)
            response.raise_for_status()

            chunks: list[bytes] = []
            for chunk in response.iter_content(chunk_size=8192):
                chunks.append(chunk)

            data = b"".join(chunks)
            logger.info(
                f"Successfully fetched attachment from {url} (size: {len(data)} bytes)"
            )
            return data

        except Exception as e:
            logger.error(f"Error fetching attachment: {str(e)}")
            return None

    def download_attachment(self, url: str, target_path: str) -> bool:
        """
        Download a Confluence attachment to the specified path.

        Args:
            url: The URL of the attachment to download
            target_path: The path where the attachment should be saved

        Returns:
            True if successful, False otherwise
        """
        if not url:
            logger.error("No URL provided for attachment download")
            return False

        try:
            # Convert to absolute path if relative
            if not os.path.isabs(target_path):
                target_path = os.path.abspath(target_path)

            # Guard against path traversal (resolves symlinks)
            validate_safe_path(target_path)

            logger.info(f"Downloading attachment from {url} to {target_path}")

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Use the Confluence session to download the file
            response = self.confluence._session.get(url, stream=True)
            response.raise_for_status()

            # Write the file to disk
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify the file was created
            if os.path.exists(target_path):
                file_size = os.path.getsize(target_path)
                logger.info(
                    f"Successfully downloaded attachment to {target_path} (size: {file_size} bytes)"
                )
                return True
            else:
                logger.error(f"File was not created at {target_path}")
                return False

        except Exception as e:
            logger.error(f"Error downloading attachment: {str(e)}")
            return False

    def download_content_attachments(
        self, content_id: str, target_dir: str
    ) -> dict[str, Any]:
        """
        Download all attachments for Confluence content.

        Args:
            content_id: The Confluence content ID
            target_dir: The directory where attachments should be saved

        Returns:
            A dictionary with download results
        """
        # Convert to absolute path if relative
        if not os.path.isabs(target_dir):
            target_dir = os.path.abspath(target_dir)

        # Guard against path traversal (resolves symlinks)
        validate_safe_path(target_dir)

        logger.info(
            f"Downloading attachments for content {content_id} to directory: {target_dir}"
        )

        # Create the target directory if it doesn't exist
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        # Get the attachments
        logger.info(f"Fetching attachments for content {content_id}")
        attachments_result = self.get_content_attachments(content_id)

        if not attachments_result.get("success"):
            return attachments_result

        attachment_data = attachments_result.get("attachments", [])

        if not attachment_data:
            return {
                "success": True,
                "message": f"No attachments found for content {content_id}",
                "downloaded": [],
                "failed": [],
            }

        # Create ConfluenceAttachment objects for each attachment
        attachments = []
        for attachment in attachment_data:
            if isinstance(attachment, dict):
                attachments.append(ConfluenceAttachment.from_api_response(attachment))

        # Download each attachment
        downloaded = []
        failed = []

        for attachment in attachments:
            if not attachment.download_url:
                logger.warning(f"No download URL for attachment {attachment.title}")
                failed.append(
                    {
                        "filename": attachment.title,
                        "error": "No download URL available",
                    }
                )
                continue

            # Create a safe filename
            safe_filename = Path(attachment.title).name
            file_path = target_path / safe_filename

            # Resolve to an absolute URL (and optionally the v1 endpoint)
            download_url = self._resolve_attachment_download_url(
                attachment.download_url,
                attachment_id=attachment.id,
                content_id=content_id,
            )

            # Download the attachment
            success = self.download_attachment(download_url, str(file_path))

            if success:
                downloaded.append(
                    {
                        "filename": attachment.title,
                        "path": str(file_path),
                        "size": attachment.file_size,
                    }
                )
            else:
                failed.append(
                    {"filename": attachment.title, "error": "Download failed"}
                )

        return {
            "success": True,
            "content_id": content_id,
            "total": len(attachments),
            "downloaded": downloaded,
            "failed": failed,
        }

    def get_content_attachments(
        self,
        content_id: str,
        start: int = 0,
        limit: int = 50,
        filename: str | None = None,
        media_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all attachments for Confluence content.

        Args:
            content_id: The Confluence content ID
            start: Starting index for pagination
            limit: Maximum number of results to return
            filename: Optional filename filter (exact match)
            media_type: Optional MIME type filter (exact match)

        Returns:
            A dictionary with attachment information
        """
        if not content_id:
            logger.error("No content ID provided for getting attachments")
            return {"success": False, "error": "No content ID provided"}

        try:
            logger.info(f"Fetching attachments for content {content_id}")

            # Use v2 API for OAuth authentication, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to get attachments for '{content_id}'"
                )
                # V2 API supports server-side filtering
                response = v2_adapter.get_page_attachments(
                    page_id=content_id,
                    start=start,
                    limit=limit,
                    filename=filename,
                    media_type=media_type,
                )
            else:
                logger.debug(
                    f"Using v1 API for token/basic authentication to get attachments for '{content_id}'"
                )
                # V1 API doesn't support filtering - fetch all, then filter client-side
                response = self.confluence.get_attachments_from_content(
                    content_id, start=start, limit=limit
                )

            attachments = response.get("results", [])
            total = response.get("size", 0)

            # Apply client-side filtering for V1 API when filters are specified
            if not v2_adapter and (filename or media_type):
                filtered = []
                for att in attachments:
                    # Filter by filename (exact match)
                    if filename and att.get("title") != filename:
                        continue
                    # Filter by media_type (exact match)
                    if media_type and att.get("mediaType") != media_type:
                        continue
                    filtered.append(att)

                attachments = filtered
                total = len(filtered)
                logger.debug(
                    f"Client-side filtering: {len(filtered)} of {response.get('size', 0)} attachments matched"
                )

            logger.info(
                f"Retrieved {len(attachments)} attachments for content {content_id}"
            )

            return {
                "success": True,
                "content_id": content_id,
                "attachments": attachments,
                "total": total,
                "start": start,
                "limit": limit,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting attachments: {error_msg}")
            return {"success": False, "error": error_msg}

    def _upload_attachment_direct(
        self,
        content_id: str,
        file_path: str,
        filename: str,
        comment: str | None,
        minor_edit: bool,
    ) -> dict[str, Any] | None:
        """
        Upload attachment using direct REST API call.

        This method uses the Confluence REST API directly to support
        the minorEdit parameter, which is not available in the
        atlassian-python-api library's attach_file() method.

        Args:
            content_id: The Confluence content ID
            file_path: Full path to the file
            filename: Name of the file
            comment: Optional comment for the attachment
            minor_edit: Whether this is a minor edit

        Returns:
            Attachment metadata dict if successful, None otherwise
        """
        try:
            with open(file_path, "rb") as file_handle:
                return self._send_attachment_request(
                    content_id, filename, file_handle, comment, minor_edit
                )
        except Exception as e:
            logger.error(
                f"Direct API upload failed: {type(e).__name__}: {e}", exc_info=True
            )
            # Propagate error details instead of swallowing them
            raise

    def _upload_attachment_from_bytes(
        self,
        content_id: str,
        filename: str,
        content: bytes,
        comment: str | None,
        minor_edit: bool,
    ) -> dict[str, Any] | None:
        """
        Upload attachment from in-memory bytes using a direct REST API call.

        Unlike ``_upload_attachment_direct`` this never touches the filesystem,
        which is required when the server cannot read host file paths (for
        example when running inside a container).

        Args:
            content_id: The Confluence content ID
            filename: Name of the file (determines the attachment title/type)
            content: Raw file bytes to upload
            comment: Optional comment for the attachment
            minor_edit: Whether this is a minor edit

        Returns:
            Attachment metadata dict if successful, None otherwise
        """
        try:
            return self._send_attachment_request(
                content_id, filename, content, comment, minor_edit
            )
        except Exception as e:
            logger.error(
                f"In-memory API upload failed: {type(e).__name__}: {e}",
                exc_info=True,
            )
            raise

    def _send_attachment_request(
        self,
        content_id: str,
        filename: str,
        file_obj: Any,
        comment: str | None,
        minor_edit: bool,
    ) -> dict[str, Any]:
        """
        Send the multipart attachment upload request to the Confluence REST API.

        This uses the REST API directly to support the ``minorEdit`` parameter,
        which is not available in the atlassian-python-api library's
        ``attach_file()`` method. ``file_obj`` may be any value accepted by the
        ``requests`` library as multipart content (an open file handle or raw
        ``bytes``).

        Args:
            content_id: The Confluence content ID
            filename: Name of the file
            file_obj: File-like object or raw bytes to upload
            comment: Optional comment for the attachment
            minor_edit: Whether this is a minor edit

        Returns:
            Attachment metadata dict.
        """

        def make_files(content: Any) -> dict[str, Any]:
            files: dict[str, Any] = {"file": (filename, content)}
            if comment:
                files["comment"] = (None, comment, "text/plain; charset=utf-8")
            return files

        base_url = self._rest_base_url()
        url = f"{base_url}/rest/api/content/{content_id}/child/attachment"

        # Server/DC requires "no-check" (with hyphen) to bypass XSRF validation.
        headers = {"X-Atlassian-Token": "no-check"}

        data: dict[str, str] = {}
        if minor_edit is not None:
            data["minorEdit"] = str(minor_edit).lower()

        # Use POST to create a new attachment on Server/DC. PUT on the list
        # endpoint is not supported by Confluence Server/DC.
        response = self.confluence._session.post(
            url, headers=headers, files=make_files(file_obj), data=data
        )

        # Server/DC returns HTTP 400 for an existing attachment name. Look up the
        # attachment ID and POST to its /data endpoint to create a new version.
        if response.status_code == 400 and "same file name" in response.text:
            logger.debug(
                f"Attachment '{filename}' already exists on content {content_id}, "
                "updating existing attachment version"
            )
            encoded_filename = urllib.parse.quote(filename, safe="")
            att_list = self.confluence._session.get(
                f"{url}?filename={encoded_filename}",
                headers=headers,
            )
            att_list.raise_for_status()
            att_results = att_list.json().get("results", [])
            if att_results:
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)
                att_id = att_results[0]["id"]
                update_url = (
                    f"{base_url}/rest/api/content/{content_id}"
                    f"/child/attachment/{att_id}/data"
                )
                response = self.confluence._session.post(
                    update_url,
                    headers=headers,
                    files=make_files(file_obj),
                    data=data,
                )

        response.raise_for_status()

        # Parse response
        result = response.json()

        # Return first result if it's a list
        if isinstance(result, dict) and "results" in result:
            results = result.get("results", [])
            return results[0] if results else result
        return result

    def delete_attachment(self, attachment_id: str) -> dict[str, Any]:
        """
        Delete an attachment by ID.

        Args:
            attachment_id: The Confluence attachment ID

        Returns:
            A dictionary with deletion result
        """
        if not attachment_id:
            logger.error("No attachment ID provided for deletion")
            return {"success": False, "error": "No attachment ID provided"}

        try:
            logger.info(f"Deleting attachment {attachment_id}")

            # Use v2 API for OAuth authentication, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to delete attachment '{attachment_id}'"
                )
                v2_adapter.delete_attachment(attachment_id)
            else:
                logger.debug(
                    f"Using v1 API for token/basic authentication to delete attachment '{attachment_id}'"
                )
                # Use v1 API endpoint for deletion
                base_url = self._rest_base_url()
                url = f"{base_url}/rest/api/content/{attachment_id}"
                response = self.confluence._session.delete(url)
                response.raise_for_status()

            logger.info(f"Successfully deleted attachment {attachment_id}")

            return {
                "success": True,
                "attachment_id": attachment_id,
                "message": "Attachment deleted successfully",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error deleting attachment: {error_msg}")
            return {"success": False, "error": error_msg}

```

### src/mcp_atlassian/confluence/client.py
```
"""Base client module for Confluence API interactions."""

import logging
import os

from atlassian import Confluence
from requests import Session
from requests.exceptions import ConnectionError as RequestsConnectionError

from ..exceptions import MCPAtlassianAuthenticationError
from ..utils.http import (
    configure_circuit_breaker,
    configure_concurrency,
    configure_rate_limit,
    configure_retry,
)
from ..utils.logging import get_masked_session_headers, log_config_param, mask_sensitive
from ..utils.oauth import configure_oauth_session
from ..utils.ssl import configure_ssl_verification
from ..utils.user_agent import get_default_user_agent
from .config import ConfluenceConfig

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class ConfluenceClient:
    """Base client for Confluence API interactions."""

    def __init__(self, config: ConfluenceConfig | None = None) -> None:
        """Initialize the Confluence client with given or environment config.

        Args:
            config: Configuration for Confluence client. If None, will load from
                environment.

        Raises:
            ValueError: If configuration is invalid or environment variables are missing
            MCPAtlassianAuthenticationError: If OAuth authentication fails
        """
        self.config = config or ConfluenceConfig.from_env()

        # Initialize the Confluence client based on auth type
        if self.config.auth_type == "oauth":
            if not self.config.oauth_config:
                error_msg = "OAuth authentication requires oauth_config"
                raise ValueError(error_msg)

            # Determine Cloud vs Data Center OAuth
            is_dc_oauth = (
                getattr(self.config.oauth_config, "is_data_center", False) is True
            )

            if not is_dc_oauth and not self.config.oauth_config.cloud_id:
                error_msg = "Cloud OAuth authentication requires a valid cloud_id"
                raise ValueError(error_msg)

            # Create a session for OAuth
            session = Session()

            # Configure the session with OAuth authentication
            if not configure_oauth_session(session, self.config.oauth_config):
                error_msg = "Failed to configure OAuth session"
                raise MCPAtlassianAuthenticationError(error_msg)

            if is_dc_oauth:
                # Data Center: use the instance URL directly
                api_url = self.config.url
                is_cloud = False
            else:
                # Cloud: use the Atlassian Cloud API URL
                api_url = f"https://api.atlassian.com/ex/confluence/{self.config.oauth_config.cloud_id}"
                is_cloud = True

            # Initialize Confluence with the session
            self.confluence = Confluence(
                url=api_url,
                session=session,
                cloud=is_cloud,
                verify_ssl=self.config.ssl_verify,
                timeout=self.config.timeout,
            )
        elif self.config.auth_type == "pat":
            logger.debug(
                f"Initializing Confluence client with Token (PAT) auth. "
                f"URL: {self.config.url}, "
                f"Token (masked): {mask_sensitive(str(self.config.personal_token))}"
            )
            self.confluence = Confluence(
                url=self.config.url,
                token=self.config.personal_token,
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
                timeout=self.config.timeout,
            )
        else:  # basic auth
            logger.debug(
                f"Initializing Confluence client with Basic auth. "
                f"URL: {self.config.url}, Username: {self.config.username}, "
                f"API Token present: {bool(self.config.api_token)}, "
                f"Is Cloud: {self.config.is_cloud}"
            )
            self.confluence = Confluence(
                url=self.config.url,
                username=self.config.username,
                password=self.config.api_token,  # API token is used as password
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
                timeout=self.config.timeout,
            )
            logger.debug(
                f"Confluence client initialized. "
                f"Session headers (Authorization masked): "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )

        # Disable trust_env for PAT and OAuth to prevent .netrc from overriding
        # explicit credentials (#860). Basic auth can safely use .netrc.
        if self.config.auth_type in ("pat", "oauth"):
            self.confluence._session.trust_env = False

        # Configure SSL verification using the shared utility
        configure_ssl_verification(
            service_name="Confluence",
            url=self.config.url,
            session=self.confluence._session,
            ssl_verify=self.config.ssl_verify,
            client_cert=self.config.client_cert,
            client_key=self.config.client_key,
            client_key_password=self.config.client_key_password,
        )

        # Apply opt-in HTTP hardening after SSL setup so SSLIgnoreAdapter, if
        # mounted, also picks up the configured behavior.
        configure_retry(self.confluence._session, service="Confluence")
        configure_concurrency(self.confluence._session, service="Confluence")
        configure_rate_limit(self.confluence._session, service="Confluence")
        configure_circuit_breaker(self.confluence._session, service="Confluence")

        # Proxy configuration
        proxies = {}
        if self.config.http_proxy:
            proxies["http"] = self.config.http_proxy
        if self.config.https_proxy:
            proxies["https"] = self.config.https_proxy
        if self.config.socks_proxy:
            proxies["socks"] = self.config.socks_proxy
        if proxies:
            self.confluence._session.proxies.update(proxies)
            for k, v in proxies.items():
                log_config_param(
                    logger, "Confluence", f"{k.upper()}_PROXY", v, sensitive=True
                )
        if self.config.no_proxy and isinstance(self.config.no_proxy, str):
            os.environ["NO_PROXY"] = self.config.no_proxy
            log_config_param(logger, "Confluence", "NO_PROXY", self.config.no_proxy)

        # Set an explicit User-Agent so requests aren't blocked by WAFs that
        # reject the default ``python-requests/X.Y`` header. User-supplied
        # custom headers below can still override this.
        self.confluence._session.headers["User-Agent"] = get_default_user_agent()

        # Apply custom headers if configured
        if self.config.custom_headers:
            self._apply_custom_headers()

        # Import here to avoid circular imports
        from ..preprocessing.confluence import ConfluencePreprocessor

        self.preprocessor = ConfluencePreprocessor(base_url=self.config.url)

        # Test authentication during initialization (in debug mode only)
        if logger.isEnabledFor(logging.DEBUG):
            try:
                self._validate_authentication()
            except MCPAtlassianAuthenticationError:
                logger.warning(
                    "Authentication validation failed during client initialization - "
                    "continuing anyway"
                )

    def _v1_rest_base_url(self) -> str:
        """Return the base URL for direct Confluence REST API v1 calls.

        Confluence Cloud OAuth uses the Atlassian API gateway base URL stored on
        the underlying client. V1 REST calls through that gateway require the
        ``/wiki`` product prefix before ``/rest/api``.

        Returns:
            Base URL suitable for appending ``/rest/api/...``.
        """
        if self.config.auth_type == "oauth" and self.config.is_cloud:
            base_url = self.confluence.url.rstrip("/")
        else:
            base_url = self.config.url.rstrip("/")

        if self.config.is_cloud and not base_url.endswith("/wiki"):
            base_url = f"{base_url}/wiki"
        return base_url

    def _validate_authentication(self) -> None:
        """Validate authentication by making a simple API call."""
        try:
            logger.debug(
                "Testing Confluence authentication by making a simple API call..."
            )
            # Make a simple API call to test authentication
            spaces = self.confluence.get_all_spaces(start=0, limit=1)
            if spaces is not None:
                logger.info(
                    f"Confluence authentication successful. "
                    f"API call returned {len(spaces.get('results', []))} spaces."
                )
            else:
                logger.warning(
                    "Confluence authentication test returned None - "
                    "this may indicate an issue"
                )
        except RequestsConnectionError as e:
            error_msg = (
                f"Could not connect to Confluence at {self.config.url}. "
                "Check that CONFLUENCE_URL is correct and the instance is reachable."
            )
            logger.error(error_msg)
            raise MCPAtlassianAuthenticationError(error_msg) from e
        except Exception as e:
            error_msg = f"Confluence authentication validation failed: {e}"
            logger.error(error_msg)
            logger.debug(
                f"Authentication headers during failure: "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )
            raise MCPAtlassianAuthenticationError(error_msg) from e

    def _apply_custom_headers(self) -> None:
        """Apply custom headers to the Confluence session."""
        if not self.config.custom_headers:
            return

        logger.debug(
            f"Applying {len(self.config.custom_headers)} custom headers to Confluence session"
        )
        for header_name, header_value in self.config.custom_headers.items():
            self.confluence._session.headers[header_name] = header_value
            logger.debug(f"Applied custom header: {header_name}")

    def _process_html_content(
        self, html_content: str, space_key: str
    ) -> tuple[str, str]:
        """Process HTML content into both HTML and markdown formats.

        Args:
            html_content: Raw HTML content from Confluence
            space_key: The key of the space containing the content

        Returns:
            Tuple of (processed_html, processed_markdown)
        """
        return self.preprocessor.process_html_content(
            html_content, space_key, self.confluence
        )

```

### src/mcp_atlassian/confluence/search.py
```
"""Module for Confluence search operations."""

import logging
import re
from typing import Any
from urllib.parse import quote

from ..models.confluence import (
    ConfluencePage,
    ConfluenceSearchResult,
    ConfluenceUserSearchResult,
    ConfluenceUserSearchResults,
)
from ..models.confluence.common import ConfluenceUser
from ..utils.decorators import handle_atlassian_api_errors
from ..utils.pagination import clamp_limit
from .client import ConfluenceClient
from .utils import quote_cql_identifier_if_needed

logger = logging.getLogger("mcp-atlassian")


class SearchMixin(ConfluenceClient):
    """Mixin for Confluence search operations."""

    @handle_atlassian_api_errors("Confluence API")
    def search(
        self, cql: str, limit: int = 10, spaces_filter: str | None = None
    ) -> list[ConfluencePage]:
        """
        Search content using Confluence Query Language (CQL).

        Args:
            cql: Confluence Query Language string
            limit: Maximum number of results to return
            spaces_filter: Optional comma-separated list of space keys to filter by,
                overrides config

        Returns:
            List of ConfluencePage models containing search results

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the
                Confluence API (401/403)
        """
        limit = clamp_limit(limit, context="confluence.search")

        # Use spaces_filter parameter if provided, otherwise fall back to config
        filter_to_use = spaces_filter or self.config.spaces_filter

        # Apply spaces filter if present
        if filter_to_use:
            # Split spaces filter by commas and handle possible whitespace
            spaces = [s.strip() for s in filter_to_use.split(",")]

            # Build the space filter query part using proper quoting for each space key
            space_query = " OR ".join(
                [f"space = {quote_cql_identifier_if_needed(space)}" for space in spaces]
            )

            # Add the space filter to existing query with parentheses
            if cql and space_query:
                if "space = " not in cql:  # Only add if not already filtering by space
                    cql = f"({cql}) AND ({space_query})"
            else:
                cql = space_query

            logger.info(f"Applied spaces filter to query: {cql}")

        # Execute the CQL search query
        results = self.confluence.cql(cql=cql, limit=limit)

        # Convert the response to a search result model
        search_result = ConfluenceSearchResult.from_api_response(
            results,
            base_url=self.config.url,
            cql_query=cql,
            is_cloud=self.config.is_cloud,
        )

        # Process result excerpts as content
        processed_pages = []
        for page in search_result.results:
            # Get the excerpt from the original search results
            for result_item in results.get("results", []):
                if result_item.get("content", {}).get("id") == page.id:
                    excerpt = result_item.get("excerpt", "")
                    if excerpt:
                        # Process the excerpt as HTML content
                        space_key = page.space.key if page.space else ""
                        _, processed_markdown = self.preprocessor.process_html_content(
                            excerpt,
                            space_key=space_key,
                            confluence_client=self.confluence,
                        )
                        # Create a new page with processed content
                        page.content = processed_markdown
                    break

            processed_pages.append(page)

        # Return the list of result pages with processed content
        return processed_pages

    @handle_atlassian_api_errors("Confluence API")
    def search_user(
        self,
        cql: str,
        limit: int = 10,
        group_name: str = "confluence-users",
    ) -> list[ConfluenceUserSearchResult]:
        """
        Search users using CQL (Cloud) or group member API (Server/DC).

        Args:
            cql: Confluence Query Language string for user search
            limit: Maximum number of results to return
            group_name: Group to search within on Server/DC
                (default: "confluence-users")

        Returns:
            List of ConfluenceUserSearchResult models containing
            user search results

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails
                with the Confluence API (401/403)
        """
        limit = clamp_limit(limit, context="confluence.search_user")

        if self.config.is_cloud:
            # Cloud: use CQL search endpoint
            results = self.confluence.get(
                "rest/api/search/user",
                params={"cql": cql, "limit": limit},
            )
            search_result = ConfluenceUserSearchResults.from_api_response(results or {})
            return search_result.results

        # Server/DC: fall back to group member API
        return self._search_user_server_dc(cql, group_name, limit)

    def _search_user_server_dc(
        self,
        cql: str,
        group_name: str,
        limit: int,
    ) -> list[ConfluenceUserSearchResult]:
        """Search users on Server/DC via group member API with pagination.

        Args:
            cql: CQL string or plain search term to fuzzy match.
            group_name: Group to search within.
            limit: Max results to return.

        Returns:
            List of matching ConfluenceUserSearchResult models.
        """
        # Extract search term from CQL if possible
        match = re.search(r'user\.fullname\s*~\s*"([^"]*)"', cql)
        search_term = match.group(1) if match else cql
        search_lower = search_term.lower()

        matches: list[ConfluenceUserSearchResult] = []
        start = 0
        page_size = 200
        encoded_group = quote(group_name, safe="")

        while len(matches) < limit:
            response: dict[str, Any] = self.confluence.get(
                f"rest/api/group/{encoded_group}/member",
                params={"start": start, "limit": page_size},
            )
            members = response.get("results", [])

            for member in members:
                display = member.get("displayName", "")
                username = member.get("username", "")
                if search_lower in display.lower() or search_lower in username.lower():
                    user = ConfluenceUser.from_api_response(member)
                    # Server/DC responses lack accountStatus;
                    # default to active for group members
                    if member.get("accountStatus") is None:
                        user.is_active = True
                    result = ConfluenceUserSearchResult(
                        user=user,
                        title=display,
                        entity_type="user",
                    )
                    matches.append(result)
                    if len(matches) >= limit:
                        break

            # Stop when no more pages available
            has_next = "_links" in response and "next" in response.get("_links", {})
            if not has_next or not members:
                break
            start += len(members)

        return matches[:limit]

```

### src/mcp_atlassian/jira/attachments.py
```
"""Attachment operations for Jira API."""

import logging
import mimetypes
import os
from pathlib import Path
from typing import Any

from ..models.jira import JiraAttachment
from ..utils.io import validate_safe_path
from ..utils.media import ATTACHMENT_MAX_BYTES
from .client import JiraClient
from .protocols import AttachmentsOperationsProto

# Configure logging
logger = logging.getLogger("mcp-jira")


class AttachmentsMixin(JiraClient, AttachmentsOperationsProto):
    """Mixin for Jira attachment operations."""

    def download_attachment(self, url: str, target_path: str) -> bool:
        """
        Download a Jira attachment to the specified path.

        Args:
            url: The URL of the attachment to download
            target_path: The path where the attachment should be saved

        Returns:
            True if successful, False otherwise
        """
        if not url:
            logger.error("No URL provided for attachment download")
            return False

        try:
            # Convert to absolute path if relative
            if not os.path.isabs(target_path):
                target_path = os.path.abspath(target_path)

            # Guard against path traversal (resolves symlinks)
            validate_safe_path(target_path)

            logger.info(f"Downloading attachment from {url} to {target_path}")

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Use the Jira session to download the file
            response = self.jira._session.get(url, stream=True)
            response.raise_for_status()

            # Write the file to disk
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify the file was created
            if os.path.exists(target_path):
                file_size = os.path.getsize(target_path)
                logger.info(
                    f"Successfully downloaded attachment to {target_path} (size: {file_size} bytes)"
                )
                return True
            else:
                logger.error(f"File was not created at {target_path}")
                return False

        except Exception as e:
            logger.error(f"Error downloading attachment: {str(e)}")
            return False

    def fetch_attachment_content(self, url: str) -> bytes | None:
        """
        Fetch attachment content into memory.

        Args:
            url: The URL of the attachment to download

        Returns:
            The raw bytes of the attachment, or None on failure
        """
        if not url:
            logger.error("No URL provided for attachment fetch")
            return None

        try:
            logger.info(f"Fetching attachment from {url}")
            response = self.jira._session.get(url, stream=True)
            response.raise_for_status()

            chunks: list[bytes] = []
            for chunk in response.iter_content(chunk_size=8192):
                chunks.append(chunk)

            data = b"".join(chunks)
            logger.info(
                f"Successfully fetched attachment from {url} (size: {len(data)} bytes)"
            )
            return data

        except Exception as e:
            logger.error(f"Error fetching attachment: {str(e)}")
            return None

    def get_issue_attachments(self, issue_key: str) -> list[JiraAttachment]:
        """Return attachment metadata for a Jira issue without downloading.

        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').

        Returns:
            A list of JiraAttachment instances.
        """
        logger.info(f"Fetching attachment metadata for {issue_key}")
        issue_data = self.jira.issue(issue_key, fields="attachment")

        if not isinstance(issue_data, dict):
            msg = f"Unexpected return value type from `jira.issue`: {type(issue_data)}"
            logger.error(msg)
            raise TypeError(msg)

        if "fields" not in issue_data:
            logger.error(f"Could not retrieve issue {issue_key}")
            return []

        attachment_data = issue_data.get("fields", {}).get("attachment", [])
        return [
            JiraAttachment.from_api_response(item)
            for item in attachment_data
            if isinstance(item, dict)
        ]

    def get_issue_attachment_contents(self, issue_key: str) -> dict[str, Any]:
        """
        Fetch all attachment contents for a Jira issue into memory.

        Unlike download_issue_attachments, this method does not write to
        the filesystem.  Each attachment is returned as raw bytes so the
        caller (e.g. the MCP server layer) can serialise them however it
        needs (base64 embedded resources, etc.).

        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')

        Returns:
            A dictionary with:
                success (bool)
                issue_key (str)
                total (int)
                attachments (list[dict]): each dict has 'filename',
                    'content_type', 'size', and 'data' (bytes)
                failed (list[dict]): each dict has 'filename' and 'error'
        """
        logger.info(f"Fetching attachment contents for {issue_key}")

        issue_data = self.jira.issue(issue_key, fields="attachment")

        if not isinstance(issue_data, dict):
            msg = f"Unexpected return value type from `jira.issue`: {type(issue_data)}"
            logger.error(msg)
            raise TypeError(msg)

        if "fields" not in issue_data:
            logger.error(f"Could not retrieve issue {issue_key}")
            return {
                "success": False,
                "error": f"Could not retrieve issue {issue_key}",
            }

        attachment_data = issue_data.get("fields", {}).get("attachment", [])

        if not attachment_data:
            return {
                "success": True,
                "message": f"No attachments found for issue {issue_key}",
                "attachments": [],
                "failed": [],
            }

        attachments: list[JiraAttachment] = []
        for item in attachment_data:
            if isinstance(item, dict):
                attachments.append(JiraAttachment.from_api_response(item))

        if not attachments:
            return {
                "success": True,
                "message": f"No attachments found for issue {issue_key}",
                "attachments": [],
                "failed": [],
            }

        fetched: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for attachment in attachments:
            if not attachment.url:
                logger.warning(f"No URL for attachment {attachment.filename}")
                failed.append(
                    {"filename": attachment.filename, "error": "No URL available"}
                )
                continue

            if attachment.size > ATTACHMENT_MAX_BYTES:
                logger.warning(
                    f"Skipping attachment {attachment.filename}: "
                    f"{attachment.size} bytes exceeds 50 MB limit"
                )
                failed.append(
                    {
                        "filename": attachment.filename,
                        "error": (
                            f"Attachment '{attachment.filename}' is "
                            f"{attachment.size} bytes which exceeds "
                            "the 50 MB inline limit. Retrieve it "
                            "directly from Jira."
                        ),
                    }
                )
                continue

            data = self.fetch_attachment_content(attachment.url)
            if data is not None:
                content_type = (
                    attachment.content_type
                    or mimetypes.guess_type(attachment.filename)[0]
                    or "application/octet-stream"
                )
                fetched.append(
                    {
                        "filename": attachment.filename,
                        "content_type": content_type,
                        "size": len(data),
                        "data": data,
                    }
                )
            else:
                failed.append(
                    {"filename": attachment.filename, "error": "Fetch failed"}
                )

        return {
            "success": True,
            "issue_key": issue_key,
            "total": len(attachments),
            "attachments": fetched,
            "failed": failed,
        }

    def download_issue_attachments(
        self, issue_key: str, target_dir: str
    ) -> dict[str, Any]:
        """
        Download all attachments for a Jira issue.

        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            target_dir: The directory where attachments should be saved

        Returns:
            A dictionary with download results
        """
        # Convert to absolute path if relative
        if not os.path.isabs(target_dir):
            target_dir = os.path.abspath(target_dir)

        # Guard against path traversal (resolves symlinks)
        validate_safe_path(target_dir)

        logger.info(
            f"Downloading attachments for {issue_key} to directory: {target_dir}"
        )

        # Create the target directory if it doesn't exist
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        # Get the issue with attachments
        logger.info(f"Fetching issue {issue_key} with attachments")
        issue_data = self.jira.issue(issue_key, fields="attachment")

        if not isinstance(issue_data, dict):
            msg = f"Unexpected return value type from `jira.issue`: {type(issue_data)}"
            logger.error(msg)
            raise TypeError(msg)

        if "fields" not in issue_data:
            logger.error(f"Could not retrieve issue {issue_key}")
            return {"success": False, "error": f"Could not retrieve issue {issue_key}"}

        # Process attachments
        attachments = []
        results = []

        # Extract attachments from the API response
        attachment_data = issue_data.get("fields", {}).get("attachment", [])

        if not attachment_data:
            return {
                "success": True,
                "message": f"No attachments found for issue {issue_key}",
                "downloaded": [],
                "failed": [],
            }

        # Create JiraAttachment objects for each attachment
        for attachment in attachment_data:
            if isinstance(attachment, dict):
                attachments.append(JiraAttachment.from_api_response(attachment))

        # Download each attachment
        downloaded = []
        failed = []

        for attachment in attachments:
            if not attachment.url:
                logger.warning(f"No URL for attachment {attachment.filename}")
                failed.append(
                    {"filename": attachment.filename, "error": "No URL available"}
                )
                continue

            # Create a safe filename
            safe_filename = Path(attachment.filename).name
            file_path = target_path / safe_filename

            # Download the attachment
            success = self.download_attachment(attachment.url, str(file_path))

            if success:
                downloaded.append(
                    {
                        "filename": attachment.filename,
                        "path": str(file_path),
                        "size": attachment.size,
                    }
                )
            else:
                failed.append(
                    {"filename": attachment.filename, "error": "Download failed"}
                )

        return {
            "success": True,
            "issue_key": issue_key,
            "total": len(attachments),
            "downloaded": downloaded,
            "failed": failed,
        }

    def upload_attachment(self, issue_key: str, file_path: str) -> dict[str, Any]:
        """
        Upload a single attachment to a Jira issue.

        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            file_path: The path to the file to upload

        Returns:
            A dictionary with upload result information
        """
        if not issue_key:
            logger.error("No issue key provided for attachment upload")
            return {"success": False, "error": "No issue key provided"}

        if not file_path:
            logger.error("No file path provided for attachment upload")
            return {"success": False, "error": "No file path provided"}

        try:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {"success": False, "error": f"File not found: {file_path}"}

            logger.info(f"Uploading attachment from {file_path} to issue {issue_key}")

            # Use the Jira API to upload the file
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as file:
                attachment = self.jira.add_attachment(
                    issue_key=issue_key, filename=file_path
                )

            if attachment:
                file_size = os.path.getsize(file_path)
                logger.info(
                    f"Successfully uploaded attachment {filename} to {issue_key} (size: {file_size} bytes)"
                )
                return {
                    "success": True,
                    "issue_key": issue_key,
                    "filename": filename,
                    "size": file_size,
                    "id": attachment.get("id")
                    if isinstance(attachment, dict)
                    else None,
                }
            else:
                logger.error(f"Failed to upload attachment {filename} to {issue_key}")
                return {
                    "success": False,
                    "error": f"Failed to upload attachment {filename} to {issue_key}",
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error uploading attachment: {error_msg}")
            return {"success": False, "error": error_msg}

    def upload_attachments(
        self, issue_key: str, file_paths: list[str]
    ) -> dict[str, Any]:
        """
        Upload multiple attachments to a Jira issue.

        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            file_paths: List of paths to files to upload

        Returns:
            A dictionary with upload results
        """
        if not issue_key:
            logger.error("No issue key provided for attachment upload")
            return {"success": False, "error": "No issue key provided"}

        if not file_paths:
            logger.error("No file paths provided for attachment upload")
            return {"success": False, "error": "No file paths provided"}

        logger.info(f"Uploading {len(file_paths)} attachments to issue {issue_key}")

        # Upload each attachment
        uploaded = []
        failed = []

        for file_path in file_paths:
            result = self.upload_attachment(issue_key, file_path)

            if result.get("success"):
                uploaded.append(
                    {
                        "filename": result.get("filename"),
                        "size": result.get("size"),
                        "id": result.get("id"),
                    }
                )
            else:
                failed.append(
                    {
                        "filename": os.path.basename(file_path),
                        "error": result.get("error"),
                    }
                )

        return {
            "success": True,
            "issue_key": issue_key,
            "total": len(file_paths),
            "uploaded": uploaded,
            "failed": failed,
        }

```

### src/mcp_atlassian/jira/client.py
```
"""Base client module for Jira API interactions."""

import logging
import os
from typing import Any, Literal

from atlassian import Jira
from requests import Session
from requests.exceptions import ConnectionError as RequestsConnectionError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.preprocessing import JiraPreprocessor
from mcp_atlassian.utils.http import (
    configure_circuit_breaker,
    configure_concurrency,
    configure_rate_limit,
    configure_retry,
)
from mcp_atlassian.utils.logging import (
    get_masked_session_headers,
    log_config_param,
    mask_sensitive,
)
from mcp_atlassian.utils.oauth import configure_oauth_session
from mcp_atlassian.utils.ssl import configure_ssl_verification
from mcp_atlassian.utils.user_agent import get_default_user_agent

from ..models.jira.adf import markdown_to_adf
from .config import JiraConfig

# Configure logging
logger = logging.getLogger("mcp-jira")


class JiraClient:
    """Base client for Jira API interactions."""

    _field_ids_cache: list[dict[str, Any]] | None
    _current_user_account_id: str | None

    config: JiraConfig
    preprocessor: JiraPreprocessor

    def __init__(self, config: JiraConfig | None = None) -> None:
        """Initialize the Jira client with configuration options.

        Args:
            config: Optional configuration object (will use env vars if not provided)

        Raises:
            ValueError: If configuration is invalid or required credentials are missing
            MCPAtlassianAuthenticationError: If OAuth authentication fails
        """
        # Load configuration from environment variables if not provided
        self.config = config or JiraConfig.from_env()

        # Initialize the Jira client based on auth type
        if self.config.auth_type == "oauth":
            if not self.config.oauth_config:
                error_msg = "OAuth authentication requires oauth_config"
                raise ValueError(error_msg)

            # Determine Cloud vs Data Center OAuth
            is_dc_oauth = (
                getattr(self.config.oauth_config, "is_data_center", False) is True
            )

            if not is_dc_oauth and not self.config.oauth_config.cloud_id:
                error_msg = "Cloud OAuth authentication requires a valid cloud_id"
                raise ValueError(error_msg)

            # Create a session for OAuth
            session = Session()

            # Configure the session with OAuth authentication
            if not configure_oauth_session(session, self.config.oauth_config):
                error_msg = "Failed to configure OAuth session"
                raise MCPAtlassianAuthenticationError(error_msg)

            if is_dc_oauth:
                # Data Center: use the instance URL directly
                api_url = self.config.url
                is_cloud = False
            else:
                # Cloud: use the Atlassian Cloud API URL
                api_url = f"https://api.atlassian.com/ex/jira/{self.config.oauth_config.cloud_id}"
                is_cloud = True

            # Initialize Jira with the session
            self.jira = Jira(
                url=api_url,
                session=session,
                cloud=is_cloud,
                verify_ssl=self.config.ssl_verify,
                timeout=self.config.timeout,
            )
        elif self.config.auth_type == "pat":
            logger.debug(
                f"Initializing Jira client with Token (PAT) auth. "
                f"URL: {self.config.url}, "
                f"Token (masked): {mask_sensitive(str(self.config.personal_token))}"
            )
            self.jira = Jira(
                url=self.config.url,
                token=self.config.personal_token,
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
                timeout=self.config.timeout,
            )
        else:  # basic auth
            logger.debug(
                f"Initializing Jira client with Basic auth. "
                f"URL: {self.config.url}, Username: {self.config.username}, "
                f"API Token present: {bool(self.config.api_token)}, "
                f"Is Cloud: {self.config.is_cloud}"
            )
            self.jira = Jira(
                url=self.config.url,
                username=self.config.username,
                password=self.config.api_token,
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
                timeout=self.config.timeout,
            )
            logger.debug(
                f"Jira client initialized. Session headers (Authorization masked): "
                f"{get_masked_session_headers(dict(self.jira._session.headers))}"
            )

        # Disable trust_env for PAT and OAuth to prevent .netrc from overriding
        # explicit credentials (#860). Basic auth can safely use .netrc.
        if self.config.auth_type in ("pat", "oauth"):
            self.jira._session.trust_env = False

        # Configure SSL verification using the shared utility
        configure_ssl_verification(
            service_name="Jira",
            url=self.config.url,
            session=self.jira._session,
            ssl_verify=self.config.ssl_verify,
            client_cert=self.config.client_cert,
            client_key=self.config.client_key,
            client_key_password=self.config.client_key_password,
        )

        # Apply opt-in HTTP hardening after SSL setup so SSLIgnoreAdapter, if
        # mounted, also picks up the configured behavior.
        configure_retry(self.jira._session, service="Jira")
        configure_concurrency(self.jira._session, service="Jira")
        configure_rate_limit(self.jira._session, service="Jira")
        configure_circuit_breaker(self.jira._session, service="Jira")

        # Proxy configuration
        proxies = {}
        if self.config.http_proxy:
            proxies["http"] = self.config.http_proxy
        if self.config.https_proxy:
            proxies["https"] = self.config.https_proxy
        if self.config.socks_proxy:
            proxies["socks"] = self.config.socks_proxy
        if proxies:
            self.jira._session.proxies.update(proxies)
            for k, v in proxies.items():
                log_config_param(
                    logger, "Jira", f"{k.upper()}_PROXY", v, sensitive=True
                )
        if self.config.no_proxy and isinstance(self.config.no_proxy, str):
            os.environ["NO_PROXY"] = self.config.no_proxy
            log_config_param(logger, "Jira", "NO_PROXY", self.config.no_proxy)

        # Set an explicit User-Agent so requests aren't blocked by WAFs that
        # reject the default ``python-requests/X.Y`` header. User-supplied
        # custom headers below can still override this.
        self.jira._session.headers["User-Agent"] = get_default_user_agent()

        # Apply custom headers if configured
        if self.config.custom_headers:
            self._apply_custom_headers()

        # Initialize the text preprocessor for text processing capabilities
        self.preprocessor = JiraPreprocessor(
            base_url=self.config.url,
            disable_translation=self.config.disable_jira_markup_translation,
        )
        self._field_ids_cache = None
        self._current_user_account_id = None

        # Test authentication during initialization (in debug mode only)
        if logger.isEnabledFor(logging.DEBUG):
            try:
                self._validate_authentication()
            except MCPAtlassianAuthenticationError:
                logger.warning(
                    "Authentication validation failed during client initialization - "
                    "continuing anyway"
                )

    def _validate_authentication(self) -> None:
        """Validate authentication by making a simple API call."""
        try:
            logger.debug(
                "Testing Jira authentication by retrieving current user info..."
            )
            current_user = self.jira.myself()
            if current_user:
                logger.info(
                    f"Jira authentication successful. "
                    f"Current user: {current_user.get('displayName', 'Unknown')} "
                    f"({current_user.get('emailAddress', 'No email')})"
                )
            else:
                logger.warning(
                    "Jira authentication test returned empty user info - "
                    "this may indicate an issue"
                )
        except RequestsConnectionError as e:
            error_msg = (
                f"Could not connect to Jira at {self.config.url}. "
                "Check that JIRA_URL is correct and the instance is reachable."
            )
            logger.error(error_msg)
            raise MCPAtlassianAuthenticationError(error_msg) from e
        except Exception as e:
            error_msg = f"Jira authentication validation failed: {e}"
            logger.error(error_msg)
            logger.debug(
                f"Authentication headers during failure: "
                f"{get_masked_session_headers(dict(self.jira._session.headers))}"
            )
            raise MCPAtlassianAuthenticationError(error_msg) from e

    def _apply_custom_headers(self) -> None:
        """Apply custom headers to the Jira session."""
        if not self.config.custom_headers:
            return

        logger.debug(
            f"Applying {len(self.config.custom_headers)} custom headers to Jira session"
        )
        for header_name, header_value in self.config.custom_headers.items():
            self.jira._session.headers[header_name] = header_value
            logger.debug(f"Applied custom header: {header_name}")

    def _clean_text(self, text: str) -> str:
        """Clean text content by:
        1. Processing user mentions and links
        2. Converting HTML/wiki markup to markdown

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Otherwise create a temporary one
        _ = self.config.url if hasattr(self, "config") else ""
        return self.preprocessor.clean_jira_text(text)

    def _markdown_to_jira(self, markdown_text: str) -> str | dict[str, Any]:
        """Convert Markdown to Jira format (ADF for Cloud, wiki markup for Server).

        Args:
            markdown_text: Text in Markdown format

        Returns:
            ADF dict for Cloud, wiki markup string for Server/DC
        """
        if not markdown_text:
            return markdown_to_adf("") if self.config.is_cloud else ""

        if self.config.is_cloud:
            try:
                return markdown_to_adf(markdown_text)
            except Exception as e:
                logger.warning(f"Error converting markdown to ADF: {e}")
                return {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": markdown_text}],
                        }
                    ],
                }

        try:
            return self.preprocessor.markdown_to_jira(markdown_text)
        except Exception as e:
            logger.warning(f"Error converting markdown to Jira format: {str(e)}")
            return markdown_text

    def _post_api3(
        self,
        resource: str,
        data: dict[str, Any],
        params: dict[str, str] | None = None,
    ) -> Any:
        """POST to Jira REST API v3 (required for ADF payloads on Cloud).

        The atlassian-python-api library defaults to /rest/api/2/ which
        expects description/body as plain strings. ADF dicts require v3.
        Callers are responsible for choosing v2 vs v3 based on payload type.
        """
        url = self.jira.resource_url(resource, api_version="3")
        return self.jira.post(url, data=data, params=params)

    def _put_api3(self, resource: str, data: dict[str, Any]) -> Any:
        """PUT to Jira REST API v3 (required for ADF payloads on Cloud)."""
        url = self.jira.resource_url(resource, api_version="3")
        return self.jira.put(url, data=data)

    def get_paged(
        self,
        method: Literal["get", "post"],
        url: str,
        params_or_json: dict | None = None,
        *,
        absolute: bool = False,
    ) -> list[dict]:
        """
        Repeatly fetch paged data from Jira API using `nextPageToken` to paginate.

        Args:
            method: The HTTP method to use
            url: The URL to retrieve data from
            params_or_json: Optional query parameters or JSON data to send
            absolute: Whether to use absolute URL

        Returns:
            List of requested json data

        Raises:
            ValueError: If using paged request on non-cloud Jira
        """

        if not self.config.is_cloud:
            raise ValueError(
                "Paged requests are only available for Jira Cloud platform"
            )

        all_results: list[dict] = []
        current_data = params_or_json or {}

        while True:
            if method == "get":
                api_result = self.jira.get(
                    path=url, params=current_data, absolute=absolute
                )
            else:
                api_result = self.jira.post(
                    path=url, json=current_data, absolute=absolute
                )

            if not isinstance(api_result, dict):
                error_message = f"API result is not a dictionary: {api_result}"
                logger.error(error_message)
                raise ValueError(error_message)

            # Extract values from response
            all_results.append(api_result)

            # Check if this is the last page
            if "nextPageToken" not in api_result:
                break

            # Update for next iteration
            current_data["nextPageToken"] = api_result["nextPageToken"]

        return all_results

    def create_version(
        self,
        project: str,
        name: str,
        start_date: str | None = None,
        release_date: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new version in a Jira project.

        Args:
            project: The project key (e.g., 'PROJ')
            name: The name of the version
            start_date: The start date (YYYY-MM-DD, optional)
            release_date: The release date (YYYY-MM-DD, optional)
            description: Description of the version (optional)

        Returns:
            The created version object as returned by Jira
        """
        payload = {"project": project, "name": name}
        if start_date:
            payload["startDate"] = start_date
        if release_date:
            payload["releaseDate"] = release_date
        if description:
            payload["description"] = description
        logger.info(f"Creating Jira version: {payload}")
        result = self.jira.post("/rest/api/2/version", json=payload)
        if not isinstance(result, dict):
            error_message = f"Unexpected response from Jira API: {result}"
            raise ValueError(error_message)
        return result

    def update_version(
        self,
        version_id: str,
        name: str | None = None,
        description: str | None = None,
        start_date: str | None = None,
        release_date: str | None = None,
        archived: bool | None = None,
        released: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing version in a Jira project.

        Only fields that are not None are sent in the request, so callers can
        toggle a single attribute (e.g. archived) without touching the others.

        Args:
            version_id: The numeric ID of the version to update.
            name: New name for the version (optional).
            description: New description for the version (optional).
            start_date: New start date (YYYY-MM-DD, optional).
            release_date: New release date (YYYY-MM-DD, optional).
            archived: Archived flag (optional).
            released: Released flag (optional).

        Returns:
            The updated version object as returned by Jira.
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if start_date is not None:
            payload["startDate"] = start_date
        if release_date is not None:
            payload["releaseDate"] = release_date
        if archived is not None:
            payload["archived"] = archived
        if released is not None:
            payload["released"] = released
        if not payload:
            raise ValueError("update_version requires at least one field to update")
        logger.info(f"Updating Jira version {version_id}: {payload}")
        result = self.jira.put(f"/rest/api/2/version/{version_id}", data=payload)
        if not isinstance(result, dict):
            error_message = f"Unexpected response from Jira API: {result}"
            raise ValueError(error_message)
        return result

```

### src/mcp_atlassian/jira/search.py
```
"""Module for Jira search operations."""

import logging
import re
from typing import Any

import requests
from requests.exceptions import HTTPError

from ..models.jira import JiraSearchResult
from ..utils.decorators import handle_auth_errors
from ..utils.pagination import clamp_limit
from .client import JiraClient
from .constants import DEFAULT_READ_JIRA_FIELDS
from .protocols import IssueOperationsProto
from .utils import quote_jql_identifier_if_needed, sanitize_jql_reserved_words

logger = logging.getLogger("mcp-jira")


class SearchMixin(JiraClient, IssueOperationsProto):
    """Mixin for Jira search operations."""

    @handle_auth_errors("Jira API")
    def search_issues(
        self,
        jql: str,
        fields: list[str] | tuple[str, ...] | set[str] | str | None = None,
        start: int = 0,
        limit: int = 50,
        expand: str | None = None,
        projects_filter: str | None = None,
        page_token: str | None = None,
    ) -> JiraSearchResult:
        """
        Search for issues using JQL (Jira Query Language).

        Args:
            jql: JQL query string
            fields: Fields to return (comma-separated string, list, tuple, set, or "*all")
            start: Starting index if number of issues is greater than the limit
                  Note: This parameter is ignored in Cloud environments and results will always
                  start from the first page.
            limit: Maximum issues to return
            expand: Optional items to expand (comma-separated)
            projects_filter: Optional comma-separated list of project keys to filter by, overrides config
            page_token: Optional pagination token from a previous search result.
                  Cloud only — Server/DC uses start for pagination.

        Returns:
            JiraSearchResult object containing issues and metadata (total, start_at, max_results)

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Jira API (401/403)
            Exception: If there is an error searching for issues
        """
        try:
            limit = clamp_limit(limit, context="jira.search_issues")

            # Sanitize JQL reserved words in project key values
            jql = sanitize_jql_reserved_words(jql)

            # Use projects_filter parameter if provided, otherwise fall back to config
            filter_to_use = projects_filter or self.config.projects_filter

            # Apply projects filter if present
            if filter_to_use:
                # Split projects filter by commas and handle possible whitespace
                projects = [p.strip() for p in filter_to_use.split(",")]

                # Build the project filter query part
                # Sanitize project names to prevent JQL injection
                # Escape backslashes before double-quotes to prevent bypass
                projects = [
                    p.replace("\\", "\\\\").replace('"', '\\"') for p in projects
                ]

                if len(projects) == 1:
                    quoted = quote_jql_identifier_if_needed(projects[0])
                    project_query = f"project = {quoted}"
                else:
                    quoted_projects = [
                        quote_jql_identifier_if_needed(p) for p in projects
                    ]
                    projects_list = ", ".join(quoted_projects)
                    project_query = f"project IN ({projects_list})"

                # Add the project filter to existing query
                if not jql:
                    # Empty JQL - just use project filter
                    jql = project_query
                elif jql.strip().upper().startswith("ORDER BY"):
                    # JQL starts with ORDER BY - prepend project filter
                    jql = f"{project_query} {jql}"
                elif (
                    "project = " not in jql.lower() and "project in" not in jql.lower()
                ):
                    # Only add if not already filtering by project
                    # Extract ORDER BY clause if present to avoid invalid JQL
                    order_match = re.search(
                        r"\s+(ORDER\s+BY\s+.*)$", jql, re.IGNORECASE
                    )
                    if order_match:
                        order_clause = order_match.group(1)
                        jql_without_order = jql[: order_match.start()]
                        jql = (
                            f"({jql_without_order}) AND {project_query} {order_clause}"
                        )
                    else:
                        jql = f"({jql}) AND {project_query}"

                logger.info(f"Applied projects filter to query: {jql}")

            # Convert fields to proper format if it's a list/tuple/set
            fields_param: str | None
            if fields is None:  # Use default if None
                fields_param = ",".join(DEFAULT_READ_JIRA_FIELDS)
            elif isinstance(fields, list | tuple | set):
                fields_param = ",".join(fields)
            else:
                fields_param = fields

            if self.config.is_cloud:
                # Cloud: Use v3 API endpoint POST /rest/api/3/search/jql
                # The old v2 /rest/api/*/search endpoint is deprecated
                # See: https://developer.atlassian.com/changelog/#CHANGE-2046

                # Build request body for v3 API
                fields_list = fields_param.split(",") if fields_param else ["id", "key"]
                request_body: dict[str, Any] = {
                    "jql": jql,
                    "fields": fields_list,
                }
                # Note: v3 API uses 'expand' as a comma-separated string, not an array
                if expand:
                    request_body["expand"] = expand

                # Fetch issues using v3 API with nextPageToken pagination
                all_issues: list[dict[str, Any]] = []
                next_page_token: str | None = page_token

                while len(all_issues) < limit:
                    # Only request the remaining count to avoid over-fetching.
                    # This ensures the returned nextPageToken aligns with
                    # the last issue we actually return to the caller.
                    remaining = limit - len(all_issues)
                    request_body["maxResults"] = min(remaining, 100)

                    if next_page_token:
                        request_body["nextPageToken"] = next_page_token

                    response = self.jira.post(
                        "rest/api/3/search/jql", json=request_body
                    )

                    if not isinstance(response, dict):
                        msg = f"Unexpected response type from v3 search API: {type(response)}"
                        logger.error(msg)
                        raise TypeError(msg)

                    issues = response.get("issues", [])
                    all_issues.extend(issues)

                    # Check for more pages
                    next_page_token = response.get("nextPageToken")
                    if not next_page_token:
                        break

                # Build response dict for model
                # Note: v3 API doesn't provide total count, so we use -1
                response_dict: dict[str, Any] = {
                    "issues": all_issues[:limit],
                    "total": -1,
                    "startAt": 0,
                    "maxResults": limit,
                }
                if next_page_token:
                    response_dict["nextPageToken"] = next_page_token

                search_result = JiraSearchResult.from_api_response(
                    response_dict,
                    base_url=self.config.url,
                    requested_fields=fields_param,
                )

                return search_result
            else:
                limit = min(limit, 50)
                response = self.jira.jql(
                    jql, fields=fields_param, start=start, limit=limit, expand=expand
                )
                if not isinstance(response, dict):
                    msg = f"Unexpected return value type from `jira.jql`: {type(response)}"
                    logger.error(msg)
                    raise TypeError(msg)

                # Convert the response to a search result model
                search_result = JiraSearchResult.from_api_response(
                    response, base_url=self.config.url, requested_fields=fields_param
                )

                # Return the full search result object
                return search_result

        except HTTPError:
            raise  # let decorator handle auth errors
        except Exception as e:
            logger.error(f"Error searching issues with JQL '{jql}': {str(e)}")
            raise Exception(f"Error searching issues: {str(e)}") from e

    def get_board_issues(
        self,
        board_id: str,
        jql: str,
        fields: str | None = None,
        start: int = 0,
        limit: int = 50,
        expand: str | None = None,
    ) -> JiraSearchResult:
        """
        Get all issues linked to a specific board.

        Args:
            board_id: The ID of the board
            jql: JQL query string
            fields: Fields to return (comma-separated string or "*all")
            start: Starting index
            limit: Maximum issues to return
            expand: Optional items to expand (comma-separated)

        Returns:
            JiraSearchResult object containing board issues and metadata

        Raises:
            Exception: If there is an error getting board issues
        """
        try:
            limit = clamp_limit(limit, context="jira.get_board_issues")

            # Sanitize JQL reserved words in project key values
            jql = sanitize_jql_reserved_words(jql) or jql

            # Determine fields_param
            fields_param = fields
            if fields_param is None:
                fields_param = ",".join(DEFAULT_READ_JIRA_FIELDS)

            response = self.jira.get_issues_for_board(
                board_id=board_id,
                jql=jql,
                fields=fields_param,
                start=start,
                limit=limit,
                expand=expand,
            )
            if not isinstance(response, dict):
                msg = f"Unexpected return value type from `jira.get_issues_for_board`: {type(response)}"
                logger.error(msg)
                raise TypeError(msg)

            # Convert the response to a search result model
            search_result = JiraSearchResult.from_api_response(
                response, base_url=self.config.url, requested_fields=fields_param
            )
            return search_result
        except requests.HTTPError as e:
            logger.error(
                f"Error searching issues for board with JQL '{board_id}': {str(e.response.content)}"
            )
            raise Exception(
                f"Error searching issues for board with JQL: {str(e.response.content)}"
            ) from e
        except Exception as e:
            logger.error(f"Error searching issues for board with JQL '{jql}': {str(e)}")
            raise Exception(
                f"Error searching issues for board with JQL {str(e)}"
            ) from e

    def get_sprint_issues(
        self,
        sprint_id: str,
        fields: str | None = None,
        start: int = 0,
        limit: int = 50,
    ) -> JiraSearchResult:
        """
        Get all issues linked to a specific sprint.

        Args:
            sprint_id: The ID of the sprint
            fields: Fields to return (comma-separated string or "*all")
            start: Starting index
            limit: Maximum issues to return

        Returns:
            JiraSearchResult object containing sprint issues and metadata

        Raises:
            Exception: If there is an error getting sprint issues
        """
        try:
            limit = clamp_limit(limit, context="jira.get_sprint_issues")

            # Use JQL search to get sprint issues with proper fields filtering
            jql = f"sprint = {sprint_id}"
            return self.search_issues(
                jql=jql,
                fields=fields,
                start=start,
                limit=limit,
            )
        except Exception as e:
            logger.error(f"Error searching issues for sprint '{sprint_id}': {str(e)}")
            raise Exception(f"Error searching issues for sprint: {str(e)}") from e

```

### src/mcp_atlassian/servers/confluence.py
```
"""Confluence FastMCP server instance and tool definitions."""

import base64
import binascii
import json
import logging
import mimetypes
import re
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, urlsplit

from fastmcp import Context, FastMCP
from mcp.types import BlobResourceContents, EmbeddedResource, ImageContent, TextContent
from pydantic import BeforeValidator, Field

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.models.confluence import ConfluenceAttachment
from mcp_atlassian.servers.dependencies import get_confluence_fetcher
from mcp_atlassian.utils.decorators import (
    check_write_access,
)
from mcp_atlassian.utils.media import (
    ATTACHMENT_MAX_BYTES,
    fetch_and_encode_attachment,
    is_image_attachment,
)

logger = logging.getLogger(__name__)


_CONFLUENCE_TINY_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,11}")
_PAGE_ID_PATH_PATTERN = re.compile(r"(?:^|/)pages/([0-9]+)(?:/|$)")
_TINY_LINK_PATH_PATTERN = re.compile(r"(?:^|/)x/([A-Za-z0-9_-]+)(?:/|$)")
_MAX_CONFLUENCE_PAGE_ID = (1 << 63) - 1


def _encode_confluence_tiny_id(page_id: int) -> str:
    """Encode a page ID using Confluence's tiny-link representation."""
    encoded = base64.b64encode(page_id.to_bytes(8, byteorder="little"))
    return (
        encoded.decode("ascii")
        .rstrip("=")
        .rstrip("A")
        .replace("/", "-")
        .replace("+", "_")
    )


def _decode_confluence_tiny_id(encoded: str) -> int | None:
    """Decode a Confluence tiny-link identifier to a numeric page ID.

    Confluence encodes a little-endian 64-bit page ID with base64, substitutes
    URL-safe characters, and removes padding and trailing zero-byte markers.

    Args:
        encoded: Identifier from the path segment after ``/x/``.

    Returns:
        The positive page ID, or ``None`` when the identifier is invalid.
    """
    if _CONFLUENCE_TINY_ID_PATTERN.fullmatch(encoded) is None:
        return None

    standard_base64 = encoded.replace("-", "/").replace("_", "+")
    padded = standard_base64.ljust(11, "A") + "="
    try:
        decoded = base64.b64decode(padded, validate=True)
    except (binascii.Error, ValueError):
        return None

    if len(decoded) != 8:
        return None

    page_id = int.from_bytes(decoded, byteorder="little")
    if not 0 < page_id <= _MAX_CONFLUENCE_PAGE_ID:
        return None
    if _encode_confluence_tiny_id(page_id) != encoded:
        return None
    return page_id


def _resolve_page_id(page_reference: str) -> str:
    """Resolve a page ID from a numeric ID, full URL, or tiny link.

    Args:
        page_reference: Numeric ID, page URL, or tiny-link URL/path.

    Returns:
        The resolved numeric ID, or the original value when it is not a
        supported page reference.
    """
    if re.fullmatch(r"[0-9]+", page_reference):
        return page_reference

    parsed = urlsplit(page_reference)
    page_match = _PAGE_ID_PATH_PATTERN.search(parsed.path)
    if page_match:
        return page_match.group(1)

    query_page_ids = parse_qs(parsed.query).get("pageId", [])
    if len(query_page_ids) == 1 and re.fullmatch(r"[0-9]+", query_page_ids[0]):
        return query_page_ids[0]

    tiny_match = _TINY_LINK_PATH_PATTERN.search(parsed.path)
    if tiny_match:
        encoded = tiny_match.group(1)
        resolved = _decode_confluence_tiny_id(encoded)
        if resolved is not None:
            logger.info("Resolved tiny link 'x/%s' to page ID %s", encoded, resolved)
            return str(resolved)
        logger.warning("Could not decode tiny link 'x/%s'", encoded)

    return page_reference


def _resolve_page_content(content: str | None, content_file: str | None) -> str:
    """Resolve page body from either an inline string or a file path.

    Exactly one of ``content`` / ``content_file`` must be supplied. ``content_file``
    exists so callers (especially MCP clients transporting large bodies over stdio
    JSON) can hand off content via the filesystem instead of marshalling it as a
    tool-call argument.

    Args:
        content: Inline page body (any supported content_format).
        content_file: Absolute or relative filesystem path to read the body from.
            Read as UTF-8.

    Returns:
        The resolved page body as a string.

    Raises:
        ValueError: If neither or both arguments are supplied, or if the file does
            not exist / is not a regular file.
        OSError: If the file exists but cannot be read.
    """
    has_content = content is not None
    has_file = content_file is not None and content_file != ""
    if has_content and has_file:
        raise ValueError("Provide either 'content' or 'content_file', not both.")
    if not has_content and not has_file:
        raise ValueError("One of 'content' or 'content_file' must be provided.")
    if has_content:
        return content
    if content_file is None or content_file == "":
        raise ValueError("One of 'content' or 'content_file' must be provided.")

    path = Path(content_file).expanduser()
    if not path.is_file():
        msg = f"content_file does not exist or is not a regular file: {path}"
        raise ValueError(msg)
    return path.read_text(encoding="utf-8")


confluence_mcp = FastMCP(
    name="Confluence MCP Service",
    instructions="Provides tools for interacting with Atlassian Confluence.",
)


@confluence_mcp.tool(
    tags={"confluence", "read", "toolset:confluence_pages"},
    annotations={"title": "Search Content", "readOnlyHint": True},
)
async def search(
    ctx: Context,
    query: Annotated[
        str,
        Field(
            description=(
                "Search query - can be either a simple text (e.g. 'project documentation') or a CQL query string. "
                "Simple queries use 'siteSearch' by default, to mimic the WebUI search, with an automatic fallback "
                "to 'text' search if not supported. Examples of CQL:\n"
                "- Basic search: 'type=page AND space=DEV'\n"
                "- Personal space search: 'space=\"~username\"' (note: personal space keys starting with ~ must be quoted)\n"
                "- Search by title: 'title~\"Meeting Notes\"'\n"
                "- Use siteSearch: 'siteSearch ~ \"important concept\"'\n"
                "- Use text search: 'text ~ \"important concept\"'\n"
                "- Recent content: 'created >= \"2023-01-01\"'\n"
                "- Content with specific label: 'label=documentation'\n"
                "- Recently modified content: 'lastModified > startOfMonth(\"-1M\")'\n"
                "- Content modified this year: 'creator = currentUser() AND lastModified > startOfYear()'\n"
                "- Content you contributed to recently: 'contributor = currentUser() AND lastModified > startOfWeek()'\n"
                "- Content watched by user: 'watcher = \"user@domain.com\" AND type = page'\n"
                '- Exact phrase in content: \'text ~ "\\"Urgent Review Required\\"" AND label = "pending-approval"\'\n'
                '- Title wildcards: \'title ~ "Minutes*" AND (space = "HR" OR space = "Marketing")\'\n'
                'Note: Special identifiers need proper quoting in CQL: personal space keys (e.g., "~username"), '
                "reserved words, numeric IDs, and identifiers with special characters."
            )
        ),
    ],
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results (1-50)",
            default=10,
            ge=1,
            le=50,
        ),
    ] = 10,
    spaces_filter: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Comma-separated list of space keys to filter results by. "
                "Overrides the environment variable CONFLUENCE_SPACES_FILTER if provided. "
                "Use empty string to disable filtering."
            ),
            default=None,
        ),
    ] = None,
) -> str:
    """Search Confluence content using simple terms or CQL.

    Args:
        ctx: The FastMCP context.
        query: Search query - can be simple text or a CQL query string.
        limit: Maximum number of results (1-50).
        spaces_filter: Comma-separated list of space keys to filter by.

    Returns:
        JSON string representing a list of simplified Confluence page objects.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    # Check if the query is a simple search term or already a CQL query
    if query and not any(
        x in query for x in ["=", "~", ">", "<", " AND ", " OR ", "currentUser()"]
    ):
        original_query = query
        try:
            query = f'siteSearch ~ "{original_query}"'
            logger.info(
                f"Converting simple search term to CQL using siteSearch: {query}"
            )
            pages = confluence_fetcher.search(
                query, limit=limit, spaces_filter=spaces_filter
            )
        except Exception as e:
            logger.warning(f"siteSearch failed ('{e}'), falling back to text search.")
            query = f'text ~ "{original_query}"'
            logger.info(f"Falling back to text search with CQL: {query}")
            pages = confluence_fetcher.search(
                query, limit=limit, spaces_filter=spaces_filter
            )
    else:
        pages = confluence_fetcher.search(
            query, limit=limit, spaces_filter=spaces_filter
        )
    search_results = [page.to_simplified_dict() for page in pages]
    return json.dumps(search_results, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "read", "toolset:confluence_pages"},
    annotations={"title": "Get Page", "readOnlyHint": True},
)
async def get_page(
    ctx: Context,
    page_id: Annotated[
        str | None,
        Field(
            description=(
                "Confluence page ID, full page URL, or tiny link. For example: "
                "'123456789', "
                "'https://example.atlassian.net/wiki/spaces/TEAM/pages/"
                "123456789/Page+Title', or "
                "'https://example.atlassian.net/wiki/x/N4CIO'. Provide this OR "
                "both 'title' and 'space_key'. If page_id is provided, title "
                "and space_key will be ignored."
            ),
            default=None,
        ),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    title: Annotated[
        str | None,
        Field(
            description=(
                "The exact title of the Confluence page. Use this with 'space_key' if 'page_id' is not known."
            ),
            default=None,
        ),
    ] = None,
    space_key: Annotated[
        str | None,
        Field(
            description=(
                "The key of the Confluence space where the page resides (e.g., 'DEV', 'TEAM'). Required if using 'title'."
            ),
            default=None,
        ),
    ] = None,
    include_metadata: Annotated[
        bool,
        Field(
            description="Whether to include page metadata such as creation date, last update, version, and labels.",
            default=True,
        ),
    ] = True,
    convert_to_markdown: Annotated[
        bool,
        Field(
            description=(
                "Whether to convert page to markdown (true) or keep it in raw HTML format (false). "
                "Raw HTML can reveal macros (like dates) not visible in markdown, but CAUTION: "
                "using HTML significantly increases token usage in AI responses."
            ),
            default=True,
        ),
    ] = True,
) -> str:
    """Get content of a specific Confluence page by its ID, or by its title and space key.

    Args:
        ctx: The FastMCP context.
        page_id: Confluence page ID, full page URL, or tiny link. If provided,
            'title' and 'space_key' are ignored.
        title: The exact title of the page. Must be used with 'space_key'.
        space_key: The key of the space. Must be used with 'title'.
        include_metadata: Whether to include page metadata.
        convert_to_markdown: Convert content to markdown (true) or keep raw HTML (false).

    Returns:
        JSON string representing the page content and/or metadata, or an error if not found or parameters are invalid.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    page_object = None

    if page_id:
        if title or space_key:
            logger.warning(
                "page_id was provided; title and space_key parameters will be ignored."
            )
        try:
            page_id_str = str(page_id)

            # Resolve page ID from URL or tiny link
            page_id_str = _resolve_page_id(page_id_str)

            page_object = confluence_fetcher.get_page_content(
                page_id_str, convert_to_markdown=convert_to_markdown
            )
        except Exception as e:
            logger.error(f"Error fetching page by ID '{page_id}': {e}")
            return json.dumps(
                {"error": f"Failed to retrieve page by ID '{page_id}': {e}"},
                indent=2,
                ensure_ascii=False,
            )
    elif title and space_key:
        page_object = confluence_fetcher.get_page_by_title(
            space_key, title, convert_to_markdown=convert_to_markdown
        )
        if not page_object:
            return json.dumps(
                {
                    "error": f"Page with title '{title}' not found in space '{space_key}'."
                },
                indent=2,
                ensure_ascii=False,
            )
    else:
        raise ValueError(
            "Either 'page_id' OR both 'title' and 'space_key' must be provided."
        )

    if not page_object:
        return json.dumps(
            {"error": "Page not found with the provided identifiers."},
            indent=2,
            ensure_ascii=False,
        )

    if include_metadata:
        result = {"metadata": page_object.to_simplified_dict()}
    else:
        result = {"content": {"value": page_object.content}}

    return json.dumps(result, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "read", "toolset:confluence_pages"},
    annotations={"title": "Get Page Children", "readOnlyHint": True},
)
async def get_page_children(
    ctx: Context,
    parent_id: Annotated[
        str,
        Field(
            description="The ID of the parent page whose children you want to retrieve"
        ),
    ],
    expand: Annotated[
        str,
        Field(
            description="Fields to expand in the response (e.g., 'version', 'body.storage')",
            default="version",
        ),
    ] = "version",
    limit: Annotated[
        int,
        Field(
            description="Maximum number of child items to return (1-50)",
            default=25,
            ge=1,
            le=50,
        ),
    ] = 25,
    include_content: Annotated[
        bool,
        Field(
            description="Whether to include the page content in the response",
            default=False,
        ),
    ] = False,
    convert_to_markdown: Annotated[
        bool,
        Field(
            description="Whether to convert page content to markdown (true) or keep it in raw HTML format (false). Only relevant if include_content is true.",
            default=True,
        ),
    ] = True,
    start: Annotated[
        int,
        Field(description="Starting index for pagination (0-based)", default=0, ge=0),
    ] = 0,
    include_folders: Annotated[
        bool,
        Field(
            description="Whether to include child folders in addition to child pages",
            default=True,
        ),
    ] = True,
) -> str:
    """Get child pages and folders of a specific Confluence page.

    Args:
        ctx: The FastMCP context.
        parent_id: The ID of the parent page.
        expand: Fields to expand.
        limit: Maximum number of child items.
        include_content: Whether to include page content.
        convert_to_markdown: Convert content to markdown if include_content is true.
        start: Starting index for pagination.
        include_folders: Whether to include child folders (default: True).

    Returns:
        JSON string representing a list of child page and folder objects.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    if include_content and "body" not in expand:
        expand = f"{expand},body.storage" if expand else "body.storage"

    try:
        pages = confluence_fetcher.get_page_children(
            page_id=parent_id,
            start=start,
            limit=limit,
            expand=expand,
            convert_to_markdown=convert_to_markdown,
            include_folders=include_folders,
        )
        child_pages = [page.to_simplified_dict() for page in pages]
        result = {
            "parent_id": parent_id,
            "count": len(child_pages),
            "limit_requested": limit,
            "start_requested": start,
            "results": child_pages,
        }
    except Exception as e:
        logger.error(
            f"Error getting/processing children for page ID {parent_id}: {e}",
            exc_info=True,
        )
        result = {"error": f"Failed to get child pages: {e}"}

    return json.dumps(result, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "read", "toolset:confluence_pages"},
    annotations={"title": "Get Space Page Tree", "readOnlyHint": True},
)
async def get_space_page_tree(
    ctx: Context,
    space_key: Annotated[
        str,
        Field(description="Space key"),
    ],
    limit: Annotated[
        int,
        Field(
            description="Max pages to fetch",
            default=100,
            ge=1,
            le=1000,
        ),
    ] = 100,
) -> str:
    """Get page hierarchy for a Confluence space as a flat list.

    Returns pages with parent_id and depth attributes for token-efficient
    processing. Filter by depth to focus on relevant sections, or find
    pages by title. Much more efficient than rendering full ASCII trees.

    Use this to understand space organization before creating/moving pages.

    Args:
        ctx: The FastMCP context.
        space_key: Space key identifier.
        limit: Maximum pages to fetch (start with 100 for faster results).

    Returns:
        JSON with space_key, total_pages, and pages array containing
        {id, title, parent_id, position, depth} for each page.
        Root pages have parent_id: null and depth: 0.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    tree_data = confluence_fetcher.get_space_page_tree(space_key=space_key, limit=limit)

    result: dict[str, object] = dict(tree_data)

    # has_more is computed by the fetcher from the API's _links.next signal
    if tree_data.get("has_more"):
        result["hint"] = (
            f"Results truncated at {limit} pages. Increase limit to see more."
        )

    return json.dumps(result, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "read", "toolset:confluence_comments"},
    annotations={"title": "Get Comments", "readOnlyHint": True},
)
async def get_comments(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be parsed from URL, "
                "e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' "
                "-> '123456789')"
            )
        ),
    ],
) -> str:
    """Get comments for a specific Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: Confluence page ID.

    Returns:
        JSON string representing a list of comment objects.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    comments = confluence_fetcher.get_page_comments(page_id)
    formatted_comments = [comment.to_simplified_dict() for comment in comments]
    return json.dumps(formatted_comments, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "read", "toolset:confluence_labels"},
    annotations={"title": "Get Labels", "readOnlyHint": True},
)
async def get_labels(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence content ID (page, blog post, or attachment). "
                "For pages: numeric ID from URL (e.g., '123456789'). "
                "For attachments: ID with 'att' prefix (e.g., 'att123456789'). "
                "Works with any Confluence content type that supports labels."
            )
        ),
    ],
) -> str:
    """Get labels for Confluence content (pages, blog posts, or attachments).

    Args:
        ctx: The FastMCP context.
        page_id: Confluence content ID (page or attachment).

    Returns:
        JSON string representing a list of label objects.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    labels = confluence_fetcher.get_page_labels(page_id)
    formatted_labels = [label.to_simplified_dict() for label in labels]
    return json.dumps(formatted_labels, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "write", "toolset:confluence_labels"},
    annotations={"title": "Add Label", "destructiveHint": True},
)
@check_write_access
async def add_label(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence content ID to label. "
                "For pages/blogs: numeric ID (e.g., '123456789'). "
                "For attachments: ID with 'att' prefix (e.g., 'att123456789'). "
                "Use get_attachments to find attachment IDs."
            )
        ),
    ],
    name: Annotated[
        str,
        Field(
            description=(
                "Label name to add (lowercase, no spaces). "
                "Examples: 'draft', 'reviewed', 'confidential', 'v1.0'. "
                "Labels help organize and categorize content."
            )
        ),
    ],
) -> str:
    """Add label to Confluence content (pages, blog posts, or attachments).

    Useful for:
    - Categorizing attachments (e.g., 'screenshot', 'diagram', 'legal-doc')
    - Tracking status (e.g., 'approved', 'needs-review', 'archived')
    - Filtering content by topic or version

    Args:
        ctx: The FastMCP context.
        page_id: Content ID (page or attachment).
        name: Label name to add.

    Returns:
        JSON string representing the updated list of label objects.

    Raises:
        ValueError: If in read-only mode or Confluence client is unavailable.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    labels = confluence_fetcher.add_page_label(page_id, name)
    formatted_labels = [label.to_simplified_dict() for label in labels]
    return json.dumps(formatted_labels, indent=2, ensure_ascii=False)


@confluence_mcp.tool(
    tags={"confluence", "write", "toolset:confluence_pages"},
    annotations={"title": "Create Page", "destructiveHint": True},
)
@check_write_access
async def create_page(
    ctx: Context,
    space_key: Annotated[
        str,
        Field(
            description="The key of the space to create the page in (usually a short uppercase code like 'DEV', 'TEAM', or 'DOC')"
        ),
    ],
    title: Annotated[str, Field(description="The title of the page")],
    content: Annotated[
        str | None,
        Field(
            description=(
                "The content of the page. Format depends on content_format "
                "parameter. Can be Markdown (default), wiki markup, storage "
                "format, or XHTML storage format. Either 'content' or "
                "'content_file' must be provided, but not both."
            ),
            default=None,
        ),
    ] = None,
    parent_id: Annotated[
        str | None,
        Field(
            description="(Optional) parent page ID. If provided, this page will be created as a child of the specified page",
            default=None,
        ),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    content_format: Annotated[
        str,
        Field(
            description=(
                "(Optional) The format of the content parameter. Options: "
                "'markdown' (default), 'wiki', 'storage', or 'xhtml'. Use "
                "'xhtml' when providing Confluence XHTML storage format "
                "(same as 'storage'). Wiki format uses Confluence wiki "
                "markup syntax"
            ),
            default="markdown",
        ),
    ] = "markdown",
    enable_heading_anchors: Annotated[
        bool,
        Field(
            description="(Optional) Whether to enable automatic heading anchor generation. Only applies when content_format is 'markdown'",
            default=False,
        ),
    ] = False,
    include_content: Annotated[
        bool,
        Field(
            description="(Optional) Whether to include page content in the response. Defaults to false since callers already have the content at create time",
            default=False,
        ),
    ] = False,
    emoji: Annotated[
        str | None,
        Field(
            description="(Optional) Page title emoji (icon shown in navigation). Can be any emoji character like '📝', '🚀', '📚'. Set to null/None to remove.",
            default=None,
        ),
    ] = None,
    content_file: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Absolute or relative filesystem path to read the "
                "page body from (UTF-8). Use this instead of 'content' when "
                "the body is too large to pass comfortably as a tool "
                "argument. Mutually exclusive with 'content'."
            ),
            default=None,
        ),
    ] = None,
    page_width: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Page layout width. Options: 'full-width', "
                "'default'. Defaults to null (Confluence default)."
            ),
            default=None,
        ),
    ] = None,
    table_layout: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Table width preset applied to all markdown tables. "
                "Options: 'full-width' (1800 px), 'wide' (960 px), "
                "'default' (760 px). Only applies when content_format is "
                "'markdown'."
            ),
            default=None,
        ),
    ] = None,
) -> str:
    """Create a new Confluence page.

    Args:
        ctx: The FastMCP context.
        space_key: The key of the space.
        title: The title of the page.
        content: The content of the page (format depends on content_format).
            Mutually exclusive with content_file; exactly one must be
            supplied.
        content_file: Filesystem path to read the page body from (UTF-8).
            Useful for bodies too large to pass as an inline tool argument.
        parent_id: Optional parent page ID.
        content_format: The format of the content ('markdown', 'wiki',
            'storage', or 'xhtml').
        enable_heading_anchors: Whether to enable heading anchors (markdown only).
        include_content: Whether to include page content in the response.
        emoji: Optional page title emoji (icon shown in navigation).
        page_width: Optional page layout width ('full-width' or 'default').
        table_layout: Optional table width preset ('full-width', 'wide', 'default').

    Returns:
        JSON string representing the created page object.

    Raises:
        ValueError: If in read-only mode, Confluence client is unavailable, or invalid content_format.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # Validate content_format
    if content_format not in ["markdown", "wiki", "storage", "xhtml"]:
        raise ValueError(
            f"Invalid content_format: {content_format}. Must be "
            "'markdown', 'wiki', 'storage', or 'xhtml'"
        )

    resolved_content = _resolve_page_content(content, content_file)

    # Determine parameters based on content format
    if content_format == "markdown":
        is_markdown = True
        content_representation = None  # Will be converted to storage
    else:
        is_markdown = False
        # Map 'xhtml' to 'storage' (both use storage format)
        content_representation = (
            "storage" if content_format == "xhtml" else content_format
        )

    page = confluence_fetcher.create_page(
        space_key=space_key,
        title=title,
        body=resolved_content,
        parent_id=parent_id,
        is_markdown=is_markdown,
        enable_heading_anchors=enable_heading_anchors
        if content_format == "markdown"
        else False,
        content_representation=content_representation,
        emoji=emoji,
        page_width=page_width,
        table_layout=table_layout if content_format == "markdown" else None,
    )
    result = page.to_simplified_dict()
    if not include_content:
        result.pop("content", None)
    return json.dumps(
        {"message": "Page created successfully", "page": result},
        indent=2,
        ensure_ascii=False,
    )


@confluence_mcp.tool(
    tags={"confluence", "write", "toolset:confluence_pages"},
    annotations={"title": "Update Page", "destructiveHint": True},
)
@check_write_access
async def update_page(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to update")],
    title: Annotated[str, Field(description="The new title of the page")],
    content: Annotated[
        str | None,
        Field(
            description=(
                "The new content of the page. Format depends on "
                "content_format parameter and may be Markdown (default), wiki "
                "markup, storage format, or XHTML storage format. Either "
                "'content' or 'content_file' must be provided, but not both."
            ),
            default=None,
        ),
    ] = None,
    is_minor_edit: Annotated[
        bool, Field(description="Whether this is a minor edit", default=False)
    ] = False,
    version_comment: Annotated[
        str | None, Field(description="Optional comment for this version", default=None)
    ] = None,
    parent_id: Annotated[
        str | None,
        Field(description="Optional the new parent page ID", default=None),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    content_format: Annotated[
        str,
        Field(
            description=(
                "(Optional) The format of the content parameter. Options: "
                "'markdown' (default), 'wiki', 'storage', or 'xhtml'. Use "
                "'xhtml' when providing Confluence XHTML storage format "
                "(same as 'storage'). Wiki format uses Confluence wiki "
                "markup syntax"
            ),
            default="markdown",
        ),
    ] = "markdown",
    enable_heading_anchors: Annotated[
        bool,
        Field(
            description="(Optional) Whether to enable automatic heading anchor generation. Only applies when content_format is 'markdown'",
            default=False,
        ),
    ] = False,
    include_content: Annotated[
        bool,
        Field(
            description="(Optional) Whether to include page content in the response. Defaults to false since callers already have the content at update time",
            default=False,
        ),
    ] = False,
    emoji: Annotated[
        str | None,
        Field(
            description="(Optional) Page title emoji (icon shown in navigation). Can be any emoji character like '📝', '🚀', '📚'. Set to null/None to remove.",
            default=None,
        ),
    ] = None,
    content_file: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Absolute or relative filesystem path to read the "
                "new page body from (UTF-8). Use this instead of 'content' "
                "when the body is too large to pass comfortably as a tool "
                "argument. Mutually exclusive with 'content'."
            ),
            default=None,
        ),
    ] = None,
    page_width: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Page layout width. Options: 'full-width', "
                "'default'. Defaults to null (preserve existing)."
            ),
            default=None,
        ),
    ] = None,
    table_layout: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Table width preset applied to all markdown tables. "
                "Options: 'full-width' (1800 px), 'wide' (960 px), "
                "'default' (760 px). Only applies when content_format is "
                "'markdown'."
            ),
            default=None,
        ),
    ] = None,
) -> str:
    """Update an existing Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: The ID of the page to update.
        title: The new title of the page.
        content: The new content of the page (format depends on
            content_format). Mutually exclusive with content_file; exactly
            one must be supplied.
        content_file: Filesystem path to read the new page body from
            (UTF-8). Useful for bodies too large to pass as an inline tool
            argument.
        is_minor_edit: Whether this is a minor edit.
        version_comment: Optional comment for this version.
        parent_id: Optional new parent page ID.
        content_format: The format of the content ('markdown', 'wiki',
            'storage', or 'xhtml').
        enable_heading_anchors: Whether to enable heading anchors (markdown only).
        include_content: Whether to include page content in the response.
        emoji: Optional page title emoji (icon shown in navigation).
        page_width: Optional page layout width ('full-width' or 'default').
        table_layout: Optional table width preset ('full-width', 'wide', 'default').

    Returns:
        JSON string representing the updated page object.

    Raises:
        ValueError: If Confluence client is not configured, available, or invalid content_format.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # Validate content_format
    if content_format not in ["markdown", "wiki", "storage", "xhtml"]:
        raise ValueError(
            f"Invalid content_format: {content_format}. Must be "
            "'markdown', 'wiki', 'storage', or 'xhtml'"
        )

    resolved_content = _resolve_page_content(content, content_file)

    # Determine parameters based on content format
    if content_format == "markdown":
        is_markdown = True
        content_representation = None  # Will be converted to storage
    else:
        is_markdown = False
        # Map 'xhtml' to 'storage' (both use storage format)
        content_representation = (
            "storage" if content_format == "xhtml" else content_format
        )

    updated_page = confluence_fetcher.update_page(
        page_id=page_id,
        title=title,
        body=resolved_content,
        is_minor_edit=is_minor_edit,
        version_comment=version_comment,
        is_markdown=is_markdown,
        parent_id=parent_id,
        enable_heading_anchors=enable_heading_anchors
        if content_format == "markdown"
        else False,
        content_representation=content_representation,
        emoji=emoji,
        page_width=page_width,
        table_layout=table_layout if content_format == "markdown" else None,
    )
    page_data = updated_page.to_simplified_dict()
    if not include_content:
        page_data.pop("content", None)
    return json.dumps(
        {"message": "Page updated successfully", "page": page_data},
        indent=2,
        ensure_ascii=False,
    )


@confluence_mcp.tool(
    tags={"confluence", "write", "toolset:confluence_pages"},
    annotations={"title": "Update Page Section", "destructiveHint": True},
)
@check_write_access
async def update_page_section(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to update")],
    heading_text: Annotated[
        str,
        Field(
            description=(
                "Exact text of the heading that starts the section to replace. "
                "Matching is case-sensitive. Use confluence_get_page with "
                "convert_to_markdown=false to inspect exact heading text when unsure."
            )
        ),
    ],
    new_content: Annotated[
        str,
        Field(
            description=(
                "Replacement content for the section body. "
                "Do NOT include the heading itself — only the body beneath it. "
                "Format is controlled by content_format."
            )
        ),
    ],
    *,
    content_format: Annotated[
        str,
        Field(
            description=(
                "(Optional) Format of new_content. "
                "Options: 'markdown' (default) or 'storage' "
                "(raw Confluence storage XML). Use 'storage' to insert "
                "macros or elements that markdown cannot express."
            ),
            default="markdown",
        ),
    ] = "markdown",
    is_minor_edit: Annotated[
        bool, Field(description="Whether this is a minor edit", default=False)
    ] = False,
    version_comment: Annotated[
        str | None,
        Field(description="Optional comment for this version", default=None),
    ] = None,
) -> str:
    """Update a single section of a Confluence page without affecting the rest.

    Replaces only the content beneath a named heading, leaving all other
    sections, macros, layouts, and Confluence-specific elements completely
    intact. This avoids the data loss that occurs when a full page is
    downloaded as Markdown, edited, and re-uploaded.

    Args:
        ctx: The FastMCP context.
        page_id: The ID of the page to update.
        heading_text: Exact heading text identifying the section to replace.
        new_content: New body content for the section (heading not included).
        content_format: Format of new_content ('markdown' or 'storage').
        is_minor_edit: Whether to flag this as a minor edit.
        version_comment: Optional version comment.

    Returns:
        JSON string representing the updated page metadata.

    Raises:
        ValueError: If Confluence client is not configured, heading is not
            found, or content_format is invalid.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    if content_format not in ("markdown", "storage"):
        error_msg = (
            f"Invalid content_format '{content_format}'. Must be "
            "'markdown' or 'storage'."
        )
        raise ValueError(error_msg)

    updated_page = confluence_fetcher.update_page_section(
        page_id=page_id,
        heading_text=heading_text,
        new_content=new_content,
        content_format=content_format,
        is_minor_edit=is_minor_edit,
        version_comment=version_comment or "",
    )

    page_data = updated_page.to_simplified_dict()
    page_data.pop("content", None)
    return json.dumps(
        {
            "message": f"Section '{heading_text}' updated successfully",
            "page": page_data,
        },
        indent=2,
        ensure_ascii=False,
    )


@confluence_mcp.tool(
    tags={"confluence", "write", "toolset:confluence_pages"},
    annotations={"title": "Delete Page", "destructiveHint": True},
)
@check_write_access
async def delete_page(
    ctx: Context,
    page_id: Annotated[str, Field(descr
... [truncated, file is 100890 chars]
```

### src/mcp_atlassian/servers/dependencies.py
```
"""Dependency providers for JiraFetcher and ConfluenceFetcher with context awareness.

Provides get_jira_fetcher and get_confluence_fetcher for use in tool functions.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from fastmcp import Context
from fastmcp.server.dependencies import get_access_token, get_http_request
from starlette.requests import Request

from mcp_atlassian.confluence import ConfluenceConfig, ConfluenceFetcher
from mcp_atlassian.jira import JiraConfig, JiraFetcher
from mcp_atlassian.servers.context import MainAppContext
from mcp_atlassian.utils.oauth import OAuthConfig
from mcp_atlassian.utils.urls import validate_url_for_ssrf

if TYPE_CHECKING:
    from mcp_atlassian.confluence.config import (
        ConfluenceConfig as UserConfluenceConfigType,
    )
    from mcp_atlassian.jira.config import JiraConfig as UserJiraConfigType

logger = logging.getLogger("mcp-atlassian.servers.dependencies")


# ---------------------------------------------------------------------------
# Service specification for generic fetcher resolution
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _ServiceSpec:
    """Per-service parameters for the generic fetcher dependency logic."""

    name: str  # "Jira" or "Confluence"
    fetcher_class: type  # JiraFetcher / ConfluenceFetcher
    config_class: type  # JiraConfig / ConfluenceConfig
    state_key: str  # request.state attribute for caching
    config_attr: str  # MainAppContext attribute for global config
    url_header: str  # X-Atlassian-{Service}-Url
    token_header: str  # X-Atlassian-{Service}-Personal-Token
    filter_kwargs: dict[str, Any]  # e.g. {"projects_filter": None}
    get_session: Callable[[Any], Any]  # fetcher → session
    validate_fn: Callable[[Any], Any]  # fetcher → validation data
    on_validated: Callable[
        [str, Request, Any, str, str | None], None
    ]  # logging + email backfill


def _jira_on_validated(
    fn_name: str,
    request: Request,
    validation_data: Any,
    auth_branch: str,
    user_email: str | None,
) -> None:
    """Post-validation logging for Jira (user ID only)."""
    if auth_branch == "header_pat":
        logger.debug(
            f"{fn_name}: Validated header-based Jira token "
            f"for user ID: {validation_data}"
        )
    elif auth_branch == "basic":
        logger.debug(
            f"{fn_name}: Validated Jira basic auth for user ID: {validation_data}"
        )
    else:  # oauth_pat
        logger.debug(f"{fn_name}: Validated Jira token for user ID: {validation_data}")


def _confluence_on_validated(
    fn_name: str,
    request: Request,
    validation_data: Any,
    auth_branch: str,
    user_email: str | None,
) -> None:
    """Post-validation logging + email backfill for Confluence."""
    derived_email = (
        validation_data.get("email") if isinstance(validation_data, dict) else None
    )
    display_name = (
        validation_data.get("displayName")
        if isinstance(validation_data, dict)
        else None
    )
    if auth_branch == "header_pat":
        logger.debug(
            f"{fn_name}: Validated header-based Confluence token. "
            f"User context: Email='{derived_email}', "
            f"DisplayName='{display_name}'"
        )
        # Always backfill email in PAT header branch
        if derived_email and validation_data and isinstance(validation_data, dict):
            request.state.user_atlassian_email = validation_data["email"]
    elif auth_branch == "basic":
        logger.debug(
            f"{fn_name}: Validated basic auth. "
            f"User: {user_email}, DisplayName='{display_name}'"
        )
    else:  # oauth_pat
        logger.debug(
            f"{fn_name}: Validated Confluence token. "
            f"User context: "
            f"Email='{user_email or derived_email}', "
            f"DisplayName='{display_name}'"
        )
        # Backfill only when email not already known
        if (
            not user_email
            and derived_email
            and validation_data
            and isinstance(validation_data, dict)
            and validation_data.get("email")
        ):
            request.state.user_atlassian_email = validation_data["email"]


def _jira_spec() -> _ServiceSpec:
    """Build Jira service spec.

    Deferred to a function so test patches on ``JiraFetcher`` / ``JiraConfig``
    are picked up at call time rather than at module import time.
    """
    return _ServiceSpec(
        name="Jira",
        fetcher_class=JiraFetcher,
        config_class=JiraConfig,
        state_key="jira_fetcher",
        config_attr="full_jira_config",
        url_header="X-Atlassian-Jira-Url",
        token_header="X-Atlassian-Jira-Personal-Token",  # noqa: S106
        filter_kwargs={"projects_filter": None},
        get_session=lambda f: f.jira._session,
        validate_fn=lambda f: f.get_current_user_account_id(),
        on_validated=_jira_on_validated,
    )


def _confluence_spec() -> _ServiceSpec:
    """Build Confluence service spec.

    Deferred to a function so test patches on ``ConfluenceFetcher`` /
    ``ConfluenceConfig`` are picked up at call time.
    """
    return _ServiceSpec(
        name="Confluence",
        fetcher_class=ConfluenceFetcher,
        config_class=ConfluenceConfig,
        state_key="confluence_fetcher",
        config_attr="full_confluence_config",
        url_header="X-Atlassian-Confluence-Url",
        token_header="X-Atlassian-Confluence-Personal-Token",  # noqa: S106
        filter_kwargs={"spaces_filter": None},
        get_session=lambda f: f.confluence._session,
        validate_fn=lambda f: f.get_current_user_info(),
        on_validated=_confluence_on_validated,
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _get_app_lifespan_ctx(ctx: Context) -> MainAppContext | None:
    """Extract MainAppContext from FastMCP lifespan context."""
    lifespan_ctx_dict = ctx.request_context.lifespan_context  # type: ignore
    return (
        lifespan_ctx_dict.get("app_lifespan_context")
        if isinstance(lifespan_ctx_dict, dict)
        else None
    )


def _get_global_config(
    ctx: Context, spec: _ServiceSpec
) -> JiraConfig | ConfluenceConfig:
    """Get global config from lifespan context.

    Raises:
        ValueError: If the global config is not available.
    """
    app_ctx = _get_app_lifespan_ctx(ctx)
    config = getattr(app_ctx, spec.config_attr, None) if app_ctx else None
    if not config:
        raise ValueError(
            f"{spec.name} global configuration (URL, SSL) is not "
            "available from lifespan context."
        )
    return config


def _create_and_validate(
    request: Request,
    spec: _ServiceSpec,
    config: Any,
    auth_branch: str,
    user_email: str | None = None,
    *,
    attach_ssrf_hook: bool = False,
) -> Any:
    """Create a fetcher, validate credentials, cache on request.state.

    Args:
        request: The current Starlette request.
        spec: Service specification.
        config: Service-specific config instance.
        auth_branch: One of "header_pat", "basic", "oauth_pat".
        user_email: User email from request state (for logging).
        attach_ssrf_hook: Whether to attach SSRF redirect hook.

    Returns:
        Validated fetcher instance.

    Raises:
        ValueError: On validation or creation failure.
    """
    fn_name = f"get_{spec.name.lower()}_fetcher"
    auth_desc = "header-based" if auth_branch == "header_pat" else "user"
    try:
        fetcher = spec.fetcher_class(config=config)
        if attach_ssrf_hook:
            session = spec.get_session(fetcher)
            session.hooks["response"].append(
                _make_ssrf_safe_hook(validate_url_for_ssrf)
            )
        validation_data = spec.validate_fn(fetcher)
        spec.on_validated(
            fn_name,
            request,
            validation_data,
            auth_branch,
            user_email,
        )
        setattr(request.state, spec.state_key, fetcher)
        return fetcher
    except Exception as e:
        logger.error(
            f"{fn_name}: Failed to create/validate {auth_desc} {spec.name}Fetcher: {e}",
            exc_info=True,
        )
        raise ValueError(f"Invalid {auth_desc} {spec.name} token or configuration: {e}")


def _resolve_oauth_access_token(fallback_token: str, service: str) -> str:
    """Resolve upstream OAuth token from FastMCP auth context with safe fallback."""
    try:
        access_token = get_access_token()
    except (RuntimeError, LookupError) as e:
        logger.debug(
            "OAuth token resolution via FastMCP context failed for %s; "
            "using request token (%s)",
            service,
            e,
        )
        return fallback_token

    if access_token and access_token.token:
        if access_token.token != fallback_token:
            logger.debug(
                "Resolved upstream %s token from FastMCP auth context", service
            )
        return access_token.token

    return fallback_token


def _make_ssrf_safe_hook(
    validate_fn: Callable[[str], str | None],
) -> Callable[..., Any]:
    """Create a requests response hook that validates redirect URLs.

    Blocks HTTP redirects that target internal/private IP addresses
    to prevent SSRF via open-redirect chains.

    Args:
        validate_fn: A function that returns None if safe,
            error string if blocked.

    Returns:
        A requests response hook function.
    """

    def hook(response: Any, **kwargs: Any) -> Any:
        if response.is_redirect:
            redirect_url = response.headers.get("Location", "")
            error = validate_fn(redirect_url)
            if error:
                response.close()
                raise ValueError(f"Redirect blocked (SSRF): {error}")
        return response

    return hook


def _resolve_bearer_auth_type(
    base_config: JiraConfig | ConfluenceConfig,
    middleware_auth_type: str,
    cloud_id: str | None = None,
) -> str:
    """Disambiguate Bearer tokens: determine if they're OAuth or PAT.

    The middleware treats all ``Bearer`` tokens as ``auth_type="oauth"`` because
    it is stateless.  The dependency layer has access to the global config and can
    make a better decision:

    * If the global config has OAuth configured (cloud_id or DC base_url) → keep "oauth"
    * Otherwise → fall back to "pat" (Server/DC Bearer-prefixed PAT)

    Args:
        base_config: The global JiraConfig or ConfluenceConfig.
        middleware_auth_type: The auth_type set by the middleware ("oauth" or "pat").
        cloud_id: Optional per-request cloud_id from headers.

    Returns:
        The resolved auth_type ("oauth" or "pat").
    """
    if middleware_auth_type != "oauth":
        return middleware_auth_type

    # Per-request cloud_id header means the client intends Cloud OAuth
    if cloud_id:
        return "oauth"

    # Check if global config has OAuth set up
    global_oauth = getattr(base_config, "oauth_config", None)
    if global_oauth is not None:
        # Has cloud_id → Cloud OAuth
        if global_oauth.cloud_id:
            return "oauth"
        # Has DC base_url → DC OAuth
        if getattr(global_oauth, "is_data_center", False) is True:
            return "oauth"

    # No OAuth config globally → Bearer token is actually a PAT
    logger.info(
        "Bearer token received but no OAuth config found globally. "
        "Treating as PAT for Server/Data Center."
    )
    return "pat"


def _create_user_config_for_fetcher(
    base_config: JiraConfig | ConfluenceConfig,
    auth_type: str,
    credentials: dict[str, Any],
    cloud_id: str | None = None,
) -> JiraConfig | ConfluenceConfig:
    """Create a user-specific configuration for Jira or Confluence fetchers.

    Args:
        base_config: The base JiraConfig or ConfluenceConfig to clone and modify.
        auth_type: The authentication type ('oauth', 'pat', or 'basic').
        credentials: Dictionary of credentials (token, email, etc).
        cloud_id: Optional cloud ID to override the base config cloud ID.

    Returns:
        JiraConfig or ConfluenceConfig with user-specific credentials.

    Raises:
        ValueError: If required credentials are missing or auth_type is unsupported.
        TypeError: If base_config is not a supported type.
    """
    if auth_type not in ["oauth", "pat", "basic"]:
        raise ValueError(
            f"Unsupported auth_type '{auth_type}' for user-specific config creation. Expected 'oauth', 'pat', or 'basic'."
        )

    username_for_config: str | None = credentials.get("user_email_context")

    logger.debug(
        f"Creating user config for fetcher. Auth type: {auth_type}, Credentials keys: {credentials.keys()}, Cloud ID: {cloud_id}"
    )

    common_args: dict[str, Any] = {
        "url": base_config.url,
        "auth_type": auth_type,
        "ssl_verify": base_config.ssl_verify,
        "http_proxy": base_config.http_proxy,
        "https_proxy": base_config.https_proxy,
        "no_proxy": base_config.no_proxy,
        "socks_proxy": base_config.socks_proxy,
    }

    if auth_type == "oauth":
        user_access_token = credentials.get("oauth_access_token")
        if not user_access_token:
            raise ValueError(
                "OAuth access token missing in credentials for user auth_type 'oauth'"
            )
        if (
            not base_config
            or not hasattr(base_config, "oauth_config")
            or not getattr(base_config, "oauth_config", None)
        ):
            raise ValueError(
                f"Global OAuth config for {type(base_config).__name__} is missing, "
                "but user auth_type is 'oauth'."
            )
        global_oauth_cfg = base_config.oauth_config

        # Determine if this is DC OAuth (base_url set, no cloud_id)
        is_dc_oauth = getattr(global_oauth_cfg, "is_data_center", False) is True

        # Use provided cloud_id or fall back to global config cloud_id
        effective_cloud_id = cloud_id if cloud_id else global_oauth_cfg.cloud_id
        effective_base_url = (
            getattr(global_oauth_cfg, "base_url", None) if is_dc_oauth else None
        )

        if not effective_cloud_id and not effective_base_url:
            raise ValueError(
                "Cloud ID or Data Center base URL is required for OAuth authentication. "
                "Provide cloud_id via X-Atlassian-Cloud-Id header or configure it globally, "
                "or set base_url for Data Center OAuth."
            )

        # Minimal OAuth config (user-provided tokens): client credentials fall back
        # to empty strings. The global oauth_config may be a
        # BYOAccessTokenOAuthConfig (e.g. a placeholder *_OAUTH_ACCESS_TOKEN set to
        # suppress the headless OAuth setup flow), which has no
        # client_id/client_secret/redirect_uri/scope attributes. With the OAuth proxy
        # active these come from the proxy config, not here, so getattr() with an
        # empty-string fallback is safe and avoids an AttributeError.
        oauth_config_for_user = OAuthConfig(
            client_id=getattr(global_oauth_cfg, "client_id", "") or "",
            client_secret=getattr(global_oauth_cfg, "client_secret", "") or "",
            redirect_uri=getattr(global_oauth_cfg, "redirect_uri", "") or "",
            scope=getattr(global_oauth_cfg, "scope", "") or "",
            access_token=user_access_token,
            refresh_token=None,
            expires_at=None,
            cloud_id=effective_cloud_id if not is_dc_oauth else None,
            base_url=effective_base_url,
        )
        common_args.update(
            {
                "username": username_for_config,
                "api_token": None,
                "personal_token": None,
                "oauth_config": oauth_config_for_user,
            }
        )
    elif auth_type == "pat":
        user_pat = credentials.get("personal_access_token")
        if not user_pat:
            raise ValueError("PAT missing in credentials for user auth_type 'pat'")

        # Log warning if cloud_id is provided with PAT auth (not typically needed)
        if cloud_id:
            logger.warning(
                f"Cloud ID '{cloud_id}' provided with PAT authentication. "
                "PAT authentication typically uses the base URL directly and doesn't require cloud_id override."
            )

        common_args.update(
            {
                "personal_token": user_pat,
                "oauth_config": None,
                "username": None,
                "api_token": None,
            }
        )
    elif auth_type == "basic":
        user_email = credentials.get("user_email")
        user_api_token = credentials.get("api_token")
        if not user_email or not user_api_token:
            raise ValueError(
                "Email and API token missing in credentials for user auth_type 'basic'"
            )

        common_args.update(
            {
                "username": user_email,
                "api_token": user_api_token,
                "personal_token": None,
                "oauth_config": None,
            }
        )

    if isinstance(base_config, JiraConfig):
        user_jira_config: UserJiraConfigType = dataclasses.replace(
            base_config, **common_args
        )
        user_jira_config.projects_filter = base_config.projects_filter
        return user_jira_config
    elif isinstance(base_config, ConfluenceConfig):
        user_confluence_config: UserConfluenceConfigType = dataclasses.replace(
            base_config, **common_args
        )
        user_confluence_config.spaces_filter = base_config.spaces_filter
        return user_confluence_config
    else:
        raise TypeError(f"Unsupported base_config type: {type(base_config)}")


async def _get_fetcher(ctx: Context, spec: _ServiceSpec) -> Any:
    """Generic fetcher resolution for both Jira and Confluence.

    Handles header-based PAT, basic auth, OAuth/PAT, and global fallback.
    """
    fn_name = f"get_{spec.name.lower()}_fetcher"
    logger.debug(f"{fn_name}: ENTERED. Context ID: {id(ctx)}")
    try:
        request: Request = get_http_request()
        logger.debug(
            f"{fn_name}: In HTTP request context. "
            f"Request URL: {request.url}. "
            f"State.{spec.state_key} exists: "
            f"{hasattr(request.state, spec.state_key) and getattr(request.state, spec.state_key) is not None}. "
            f"State.user_auth_type: "
            f"{getattr(request.state, 'user_atlassian_auth_type', 'N/A')}. "
            f"State.user_token_present: "
            f"{hasattr(request.state, 'user_atlassian_token') and request.state.user_atlassian_token is not None}."
        )
        # Use fetcher from request.state if already present
        cached = getattr(request.state, spec.state_key, None)
        if cached:
            logger.debug(f"{fn_name}: Returning {spec.name}Fetcher from request.state.")
            return cached
        user_auth_type = getattr(request.state, "user_atlassian_auth_type", None)
        logger.debug(f"{fn_name}: User auth type: {user_auth_type}")

        service_headers = getattr(request.state, "atlassian_service_headers", {})
        url_header_val = service_headers.get(spec.url_header)
        token_header_val = service_headers.get(spec.token_header)

        # --- Branch 1: header-based PAT ---
        if (
            user_auth_type == "pat"
            and url_header_val
            and token_header_val
            and not hasattr(request.state, "user_atlassian_token")
        ):
            logger.info(
                f"Creating header-based {spec.name}Fetcher "
                f"with URL: {url_header_val} and PAT token"
            )
            header_config = spec.config_class(
                url=url_header_val,
                auth_type="pat",
                personal_token=token_header_val,
                ssl_verify=True,
                http_proxy=None,
                https_proxy=None,
                no_proxy=None,
                socks_proxy=None,
                custom_headers=None,
                **spec.filter_kwargs,
            )
            return _create_and_validate(
                request,
                spec,
                header_config,
                "header_pat",
                attach_ssrf_hook=True,
            )

        # --- Branch 2: basic auth ---
        elif user_auth_type == "basic":
            user_email = getattr(request.state, "user_atlassian_email", None)
            user_api_token = getattr(request.state, "user_atlassian_api_token", None)

            if not user_email or not user_api_token:
                rai
... [truncated, file is 25875 chars]
```

### src/mcp_atlassian/servers/main.py
[omitted: context budget exhausted]

### src/mcp_atlassian/utils/oauth.py
[omitted: context budget exhausted]

### src/mcp_atlassian/utils/oauth_setup.py
[omitted: context budget exhausted]

### src/mcp_atlassian/utils/ssl.py
[omitted: context budget exhausted]

### src/mcp_atlassian/utils/ssrf_adapter.py
[omitted: context budget exhausted]

### src/mcp_atlassian/utils/urls.py
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
### src/mcp_atlassian/confluence/__init__.py
```
"""Confluence API integration module.

This module provides access to Confluence content through the Model Context Protocol.
"""

from .analytics import AnalyticsMixin
from .attachments import AttachmentsMixin
from .client import ConfluenceClient
from .comments import CommentsMixin
from .config import ConfluenceConfig
from .labels import LabelsMixin
from .pages import PagesMixin
from .permissions import PermissionsMixin
from .restrictions import RestrictionsMixin
from .search import SearchMixin
from .spaces import SpacesMixin
from .users import UsersMixin


class ConfluenceFetcher(
    SearchMixin,
    SpacesMixin,
    PagesMixin,
    CommentsMixin,
    LabelsMixin,
    UsersMixin,
    AnalyticsMixin,
    AttachmentsMixin,
    PermissionsMixin,
    RestrictionsMixin,
):
    """Main entry point for Confluence operations, providing backward compatibility.

    This class combines functionality from various mixins to maintain the same
    API as the original ConfluenceFetcher class.

    Available mixins:
    - SearchMixin: CQL search operations
    - SpacesMixin: Space operations
    - PagesMixin: Page operations
    - CommentsMixin: Comment operations
    - LabelsMixin: Label operations
    - UsersMixin: User operations
    - AnalyticsMixin: Page view analytics (Cloud only)
    - AttachmentsMixin: Attachment operations
    - PermissionsMixin: Permission inspection operations (Cloud only)
    - RestrictionsMixin: Page restriction operations
    """

    pass


__all__ = [
    "ConfluenceFetcher",
    "ConfluenceConfig",
    "ConfluenceClient",
    "AnalyticsMixin",
    "PermissionsMixin",
    "RestrictionsMixin",
]

```

### src/mcp_atlassian/jira/__init__.py
```
"""Jira API module for mcp_atlassian.

This module provides various Jira API client implementations.
"""

# flake8: noqa

# Re-export the Jira class for backward compatibility
from atlassian.jira import Jira

from .attachments import AttachmentsMixin
from .boards import BoardsMixin
from .client import JiraClient
from .comments import CommentsMixin
from .config import JiraConfig
from .development import DevelopmentMixin
from .epics import EpicsMixin
from .field_options import FieldOptionsMixin
from .fields import FieldsMixin
from .forms_api import FormsApiMixin  # Forms REST API
from .formatting import FormattingMixin
from .issues import IssuesMixin
from .links import LinksMixin
from .metrics import MetricsMixin
from .projects import ProjectsMixin
from .queues import QueuesMixin
from .sla import SLAMixin
from .search import SearchMixin
from .sprints import SprintsMixin
from .transitions import TransitionsMixin
from .users import UsersMixin
from .watchers import WatchersMixin
from .worklog import WorklogMixin


class JiraFetcher(
    ProjectsMixin,
    FieldsMixin,
    FieldOptionsMixin,
    FormsApiMixin,  # Use new Forms REST API instead of FormsMixin
    FormattingMixin,
    TransitionsMixin,
    WorklogMixin,
    EpicsMixin,
    CommentsMixin,
    SearchMixin,
    IssuesMixin,
    UsersMixin,
    WatchersMixin,
    BoardsMixin,
    SprintsMixin,
    QueuesMixin,
    AttachmentsMixin,
    LinksMixin,
    MetricsMixin,
    SLAMixin,
    DevelopmentMixin,
):
    """
    The main Jira client class providing access to all Jira operations.

    This class inherits from multiple mixins that provide specific functionality:
    - ProjectsMixin: Project-related operations
    - FieldsMixin: Field-related operations
    - FormattingMixin: Content formatting utilities
    - TransitionsMixin: Issue transition operations
    - WorklogMixin: Worklog operations
    - EpicsMixin: Epic operations
    - CommentsMixin: Comment operations
    - SearchMixin: Search operations
    - IssuesMixin: Issue operations
    - UsersMixin: User operations
    - WatchersMixin: Watcher operations
    - BoardsMixin: Board operations
    - SprintsMixin: Sprint operations
    - AttachmentsMixin: Attachment download operations
    - LinksMixin: Issue link operations
    - MetricsMixin: Issue metrics and date operations
    - QueuesMixin: Service Desk queue read operations (Server/DC)
    - SLAMixin: SLA calculations

    The class structure is designed to maintain backward compatibility while
    improving code organization and maintainability.
    """

    pass


__all__ = [
    "JiraFetcher",
    "JiraConfig",
    "JiraClient",
    "Jira",
    "MetricsMixin",
    "SLAMixin",
]

```

### src/mcp_atlassian/utils/__init__.py
```
"""
Utility functions for the MCP Atlassian integration.
This package provides various utility functions used throughout the codebase.
"""

from .date import parse_date
from .io import is_read_only_mode, validate_safe_path

# Export lifecycle utilities
from .lifecycle import (
    ensure_clean_exit,
    setup_signal_handlers,
)
from .logging import setup_logging
from .media import (
    ATTACHMENT_MAX_BYTES,
    fetch_and_encode_attachment,
    is_image_attachment,
)

# Export OAuth utilities
from .oauth import OAuthConfig, configure_oauth_session
from .ssl import SSLIgnoreAdapter, configure_ssl_verification
from .urls import is_atlassian_cloud_url, resolve_relative_url, validate_url_for_ssrf

# Export all utility functions for backward compatibility
__all__ = [
    "ATTACHMENT_MAX_BYTES",
    "SSLIgnoreAdapter",
    "configure_ssl_verification",
    "is_atlassian_cloud_url",
    "is_image_attachment",
    "is_read_only_mode",
    "validate_safe_path",
    "setup_logging",
    "parse_date",
    "parse_iso8601_date",
    "OAuthConfig",
    "configure_oauth_session",
    "resolve_relative_url",
    "setup_signal_handlers",
    "ensure_clean_exit",
    "fetch_and_encode_attachment",
    "validate_url_for_ssrf",
]

```

### src/mcp_atlassian/jira/users.py
```
"""Module for Jira user operations."""

import logging
import re
from typing import TYPE_CHECKING, TypeVar

import requests
from requests.exceptions import HTTPError
from unidecode import unidecode

from mcp_atlassian.models.jira.common import JiraUser
from mcp_atlassian.utils.decorators import handle_auth_errors

from .client import JiraClient

if TYPE_CHECKING:
    from mcp_atlassian.models.jira.common import JiraUser

JiraUserType = TypeVar("JiraUserType", bound="JiraUser")

logger = logging.getLogger("mcp-jira")


def normalize_text(text: str | None) -> str:
    """Normalize text for case-insensitive Unicode comparison.

    Uses unidecode for ASCII transliteration to handle characters like
    Polish "ł" matching ASCII "l", then casefold for case-insensitivity.

    Args:
        text: The text to normalize.

    Returns:
        Normalized ASCII text suitable for comparison.
    """
    if not text:
        return ""
    # Transliterate to ASCII (ł→l, ó→o, etc.) then casefold for case-insensitivity
    return unidecode(text).casefold()


class UsersMixin(JiraClient):
    """Mixin for Jira user operations."""

    def get_current_user_account_id(self) -> str:
        """
        Get the account ID of the current user.

        Returns:
            str: Account ID of the current user.

        Raises:
            Exception: If unable to get the current user's account ID.
        """
        if getattr(self, "_current_user_account_id", None) is not None:
            return self._current_user_account_id

        try:
            logger.debug(
                "Calling self.jira.myself() to get current user details for account ID."
            )
            myself_data = self.jira.myself()

            if not isinstance(myself_data, dict):
                error_msg = "Failed to get user data: response was not a dictionary."
                logger.error(
                    f"{error_msg} Response type: {type(myself_data)}, Response: {str(myself_data)[:200]}"
                )
                raise Exception(error_msg)

            logger.debug(f"Received myself_data: {str(myself_data)[:500]}")

            account_id = None
            if isinstance(myself_data.get("accountId"), str):
                account_id = myself_data["accountId"]
            elif isinstance(myself_data.get("key"), str):
                logger.info(
                    "Using 'key' instead of 'accountId' for Jira Data Center/Server"
                )
                account_id = myself_data["key"]
            elif isinstance(myself_data.get("name"), str):
                logger.info(
                    "Using 'name' instead of 'accountId' for Jira Data Center/Server"
                )
                account_id = myself_data["name"]

            if account_id is None:
                error_msg = f"Could not find accountId, key, or name in user data: {str(myself_data)[:200]}"
                raise ValueError(error_msg)

            self._current_user_account_id = account_id
            return account_id
        except HTTPError as http_err:
            response_content = ""
            if http_err.response is not None:
                try:
                    response_content = http_err.response.text
                except Exception:
                    response_content = "(could not decode response content)"
            logger.error(
                f"HTTPError getting current user account ID: {http_err}. Response: {response_content[:500]}"
            )
            error_msg = f"Unable to get current user account ID: {http_err}"
            raise Exception(error_msg) from http_err
        except Exception as e:
            logger.error(f"Error getting current user account ID: {e}", exc_info=True)
            error_msg = f"Unable to get current user account ID: {e}"
            raise Exception(error_msg) from e

    def _get_account_id(self, assignee: str) -> str:
        """
        Get the account ID for a username or account ID.

        Args:
            assignee (str): Username or account ID.

        Returns:
            str: Account ID.

        Raises:
            ValueError: If the account ID could not be found.
        """
        # If it looks like an account ID already, return it.
        # Cloud account IDs come in two shapes: the legacy 24-char hex format
        # (e.g. "5b10ac8d82e05b22cc7d4ef5") and the current "<digits>:<uuid>"
        # format (e.g. "712020:f653aab5-cc61-4c57-8fa8-f7d73b94499d").
        # An explicit "accountid:" prefix is also accepted, matching the
        # format documented in the create_issue/update_issue tool schemas.
        if assignee.startswith("accountid:"):
            return assignee[len("accountid:") :]
        if assignee.startswith("5") and len(assignee) >= 10:
            return assignee
        if re.match(r"^\d+:[0-9a-fA-F][0-9a-fA-F-]{7,}$", assignee):
            return assignee

        account_id = self._lookup_user_directly(assignee)
        if account_id:
            return account_id

        account_id = self._lookup_user_by_permissions(assignee)
        if account_id:
            return account_id

        error_msg = f"Could not find account ID for user: {assignee}"
        raise ValueError(error_msg)

    def _lookup_user_directly(self, username: str) -> str | None:
        """
        Look up a user account ID directly.

        Args:
            username (str): Username to look up.

        Returns:
            Optional[str]: Account ID if found, None otherwise.
        """
        try:
            params = {}
            if self.config.is_cloud:
                params["query"] = username
            else:
                params["username"] = username

            response = self.jira.user_find_by_user_string(**params, start=0, limit=1)
            if not isinstance(response, list):
                msg = f"Unexpected return value type from `jira.user_find_by_user_string`: {type(response)}"
                logger.error(msg)
                return None

            search_norm = normalize_text(username)
            for user in response:
                if (
                    normalize_text(user.get("displayName", "")) == search_norm
                    or normalize_text(user.get("name", "")) == search_norm
                    or normalize_text(user.get("emailAddress", "")) == search_norm
                ):
                    if self.config.is_cloud:
                        if "accountId" in user:
                            return user["accountId"]
                    else:
                        if "name" in user:
                            logger.info(
                                "Using 'name' for assignee field in Jira Data Center/Server"
                            )
                            return user["name"]
                        elif "key" in user:
                            logger.info(
                                "Using 'key' as fallback for assignee name in Jira Data Center/Server"
                            )
                            return user["key"]
            return None
        except Exception as e:
            logger.info(f"Error looking up user directly: {str(e)}")
            return None

    def _resolve_server_dc_user_params(self, email: str) -> dict[str, str] | None:
        """Resolve email to Server/DC user API params via search.

        Unlike _lookup_user_directly which returns a bare string,
        this returns the correct API parameter dict, avoiding the
        need to guess whether the value is a username or key.

        Args:
            email: Email address to resolve.

        Returns:
            Dict with 'username' or 'key' param, or None if not found.
        """
        try:
            response = self.jira.user_find_by_user_string(
                username=email, start=0, limit=1
            )
            if not isinstance(response, list):
                return None

            search_norm = normalize_text(email)
            for user in response:
                if (
                    normalize_text(user.get("displayName", "")) == search_norm
                    or normalize_text(user.get("name", "")) == search_norm
                    or normalize_text(user.get("emailAddress", "")) == search_norm
                ):
                    if user.get("name"):
                        return {"username": user["name"]}
                    elif user.get("key"):
                        return {"key": user["key"]}
            return None
        except Exception as e:
            logger.info(f"Error resolving server user by email: {e}")
            return None

    def _lookup_user_by_permissions(self, username: str) -> str | None:
        """
        Look up a user account ID by permissions.

        Args:
            username (str): Username to look up.

        Returns:
            Optional[str]: Account ID if found, None otherwise.
        """
        try:
            url = f"{self.config.url}/rest/api/2/user/permission/search"
            params = {"query": username, "permissions": "BROWSE"}

            auth = None
            headers = {}
            if self.config.auth_type == "pat":
                headers["Authorization"] = f"Bearer {self.config.personal_token}"
            else:
                auth = (self.config.username or "", self.config.api_token or "")

            response = requests.get(
                url,
                params=params,
                auth=auth,
                headers=headers,
                verify=self.config.ssl_verify,
            )

            if response.status_code == 200:
                data = response.json()
                for user in data.get("users", []):
                    if self.config.is_cloud:
                        if "accountId" in user:
                            return user["accountId"]
                    else:
                        if "name" in user:
                            logger.info(
                                "Using 'name' for assignee field in Jira Data Center/Server"
                            )
                            return user["name"]
                        elif "key" in user:
                            logger.info(
                                "Using 'key' as fallback for assignee name in Jira Data Center/Server"
                            )
                            return user["key"]
            return None
        except Exception as e:
            logger.info(f"Error looking up user by permissions: {str(e)}")
            return None

    def _determine_user_api_params(self, identifier: str) -> dict[str, str]:
        """
        Determines the correct API parameter and value for the jira.user() call based on the identifier and instance type.

        Args:
            identifier (str): User identifier (accountId, username, key, or email).

        Returns:
            Dict[str, str]: A dictionary containing the single keyword argument for self.jira.user().

        Raises:
            ValueError: If a usable parameter cannot be determined.
        """
        api_kwargs: dict[str, str] = {}

        # Cloud: identifier is accountId
        if self.config.is_cloud and (
            re.match(r"^[0-9a-f]{24}$", identifier) or re.match(r"^\d+:\w+", identifier)
        ):
            api_kwargs["account_id"] = identifier
            logger.debug(f"Determined param: account_id='{identifier}' (Cloud)")
        # Server/DC: username, key, or email
        elif not self.config.is_cloud:
            if "@" in identifier:
                # /rest/api/2/user?username=email won't match by email on Server/DC.
                # Use /rest/api/2/user/search first to resolve email → actual username/key.
                resolved_params = self._resolve_server_dc_user_params(identifier)
                if resolved_params:
                    api_kwargs.update(resolved_params)
                    param_name = next(iter(resolved_params))
                    logger.debug(
                
... [truncated]
```

### src/mcp_atlassian/confluence/pages.py
```
"""Module for Confluence page operations."""

import difflib
import logging
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from requests.exceptions import HTTPError

from ..models.confluence import ConfluencePage
from ..utils.decorators import handle_auth_errors
from ..utils.pagination import clamp_limit
from .client import ConfluenceClient
from .utils import emoji_to_hex_id, extract_emoji_from_property
from .v2_adapter import ConfluenceV2Adapter

logger = logging.getLogger("mcp-atlassian")


class PagesMixin(ConfluenceClient):
    """Mixin for Confluence page operations."""

    @property
    def _v2_adapter(self) -> ConfluenceV2Adapter | None:
        """Get v2 API adapter for OAuth authentication.

        Returns:
            ConfluenceV2Adapter instance if OAuth is configured, None otherwise
        """
        if self.config.auth_type == "oauth" and self.config.is_cloud:
            return ConfluenceV2Adapter(
                session=self.confluence._session, base_url=self.confluence.url
            )
        return None

    @property
    def _page_children_v2_adapter(self) -> ConfluenceV2Adapter | None:
        """Get v2 API adapter for Cloud page-children lookups.

        Returns:
            ConfluenceV2Adapter instance for Cloud, None for Server/Data Center.
        """
        if self.config.is_cloud:
            return ConfluenceV2Adapter(
                session=self.confluence._session, base_url=self.confluence.url
            )
        return None

    @staticmethod
    def _v2_next_cursor(response: dict[str, Any]) -> str | None:
        """Extract the next cursor from a Confluence v2 paginated response."""
        links = response.get("_links", {})
        if not isinstance(links, dict):
            return None

        next_link = links.get("next")
        if not isinstance(next_link, str) or not next_link:
            return None

        cursor = parse_qs(urlparse(next_link).query).get("cursor", [None])[0]
        return cursor or None

    @staticmethod
    def _is_requested_child_type(
        item: dict[str, Any], *, include_folders: bool
    ) -> bool:
        """Return whether a v2 direct-child item matches the tool contract."""
        item_type = item.get("type", "page")
        return item_type == "page" or (include_folders and item_type == "folder")

    def _get_v2_page_children_items(
        self,
        v2_adapter: ConfluenceV2Adapter,
        page_id: str,
        start: int,
        limit: int,
        expand: str,
        *,
        include_folders: bool,
    ) -> list[dict[str, Any]]:
        """Fetch v2 direct children while preserving the v1 start/limit contract."""
        if limit <= 0:
            return []

        child_items: list[dict[str, Any]] = []
        cursor: str | None = None
        seen_cursors: set[str | None] = set()
        items_to_skip = max(start, 0)

        while len(child_items) < limit:
            if cursor in seen_cursors:
                logger.warning(
                    "Stopping v2 child pagination for page '%s' after repeated "
                    "cursor '%s'",
                    page_id,
                    cursor,
                )
                break
            seen_cursors.add(cursor)

            page_results = v2_adapter.get_page_direct_children(
                page_id=page_id,
                limit=limit,
                cursor=cursor,
            )
            raw_items = page_results.get("results", [])
            if not isinstance(raw_items, list):
                break

            requested_items = [
                item
                for item in raw_items
                if isinstance(item, dict)
                and self._is_requested_child_type(item, include_folders=include_folders)
            ]

            if items_to_skip:
                if len(requested_items) <= items_to_skip:
                    items_to_skip -= len(requested_items)
                    cursor = self._v2_next_cursor(page_results)
                    if not cursor:
                        break
                    continue

                requested_items = requested_items[items_to_skip:]
                items_to_skip = 0

            remaining = limit - len(child_items)
            child_items.extend(requested_items[:remaining])

            if len(child_items) >= limit:
                break

            cursor = self._v2_next_cursor(page_results)
            if not cursor:
                break

        if "body" in expand:
            return self._enrich_v2_child_pages_with_content(v2_adapter, child_items)

        return child_items

    def _enrich_v2_child_pages_with_content(
        self,
        v2_adapter: ConfluenceV2Adapter,
        child_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Fetch page details for v2 direct-child page items when body is requested."""
        enriched_items: list[dict[str, Any]] = []

        for item in child_items:
            if item.get("type", "page") != "page" or not item.get("id"):
                enriched_items.append(item)
                continue

            page = v2_adapter.get_page(
                page_id=str(item["id"]),
                expand="body.storage,version,space",
            )
            enriched_items.append({**item, **page})

        return enriched_items

    @handle_auth_errors("Confluence API")
    def get_page_content(
        self, page_id: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage:
        """
        Get content of a specific page.

        Args:
            page_id: The ID of the page to retrieve
            convert_to_markdown: When True, returns content in
                markdown format, otherwise returns raw HTML
                (keyword-only)

        Returns:
            ConfluencePage model containing the page content and
            metadata

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails
                with the Confluence API (401/403)
            Exception: If there is an error retrieving the page
        """
        try:
            # Use v2 API for OAuth, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to get page '{page_id}'"
                )
                page = v2_adapter.get_page(
                    page_id=page_id,
                    expand="body.storage,version,space,children.attachment,history",
                )
            else:
                logger.debug(
                    "Using v1 API for token/basic"
                    f" authentication to get page '{page_id}'"
                )
                page = self.confluence.get_page_by_id(
                    page_id=page_id,
                    expand="body.storage,version,space,children.attachment,history",
                )

            # Check if API returned an error string
            if isinstance(page, str):
                error_msg = f"API returned error response: {page[:500]}"
                raise Exception(error_msg)

            space_key = page.get("space", {}).get("key", "")
            try:
                content = page["body"]["storage"]["value"]
            except (KeyError, TypeError) as e:
                logger.warning(
                    f"Page {page.get('id', 'unknown')} missing body.storage.value: {e}"
                )
                content = ""
            page_id_str = str(page.get("id", ""))
            page_attachments = (
                page.get("children", {}).get("attachment", {}).get("results", [])
            )
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                content,
                space_key=space_key,
                confluence_client=self.confluence,
                content_id=page_id_str,
                attachments=page_attachments,
            )

            page_content = processed_markdown if convert_to_markdown else processed_html

            # Fetch page emoji and width from content properties
            emoji = self._get_page_emoji(page_id)
            page_width = self._get_page_width(page_id)

            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                content_override=page_content,
                content_format=("storage" if not convert_to_markdown else "markdown"),
                is_cloud=self.config.is_cloud,
                emoji=emoji,
                page_width=page_width,
            )
        except HTTPError:
            raise  # let decorator handle auth errors
        except Exception as e:
            logger.error(
                f"Error retrieving page content for page ID {page_id}: {str(e)}"
            )
            raise Exception(f"Error retrieving page content: {str(e)}") from e

    @handle_auth_errors("Confluence API")
    def get_page_ancestors(self, page_id: str) -> list[ConfluencePage]:
        """
        Get ancestors (parent pages) of a specific page.

        Args:
            page_id: The ID of the page to get ancestors for

        Returns:
            List of ConfluencePage models representing the
            ancestors in hierarchical order (immediate parent
            first, root ancestor last)

        Raises:
            MCPAtlassianAuthenticationError: If authentication
                fails with the Confluence API (401/403)
        """
        try:
            ancestors = self.confluence.get_page_ancestors(page_id)

            ancestor_models = []
            for ancestor in ancestors:
                page_model = ConfluencePage.from_api_response(
                    ancestor,
                    base_url=self.config.url,
                    include_body=False,
                )
                ancestor_models.append(page_model)

            return ancestor_models
        except HTTPError:
            raise  # let decorator handle auth errors
        except Exception as e:
            logger.error(f"Error fetching ancestors for page {page_id}: {str(e)}")
            logger.debug("Full exception details:", exc_info=True)
            return []

    def _get_page_emoji(self, page_id: str) -> str | None:
        """Get the page title emoji from content properties.

        The page emoji (icon shown in navigation) is stored as a content property
        with key 'emoji-title-published' or 'emoji-title-draft'.

        Args:
            page_id: The ID of the page

        Returns:
            The emoji character if set, None otherwise
        """
        try:
            # Use v2 API for OAuth authentication
            v2_adapter = self._v2_adapter
            if v2_adapter:
                return v2_adapter.get_page_emoji(page_id)

            # For token/basic auth, use v1 API via atlassian library
            properties = self.confluence.get_page_properties(page_id)
            if not properties:
                return None

            results = properties.get("results", [])
            for prop in results:
                key = prop.get("key", "")
                if key in ("emoji-title-published", "emoji-title-draft"):
                    value = prop.get("value", {})
                    return extract_emoji_from_property(value)

            return None

        except Exception as e:
            logger.debug(f"Error fetching emoji for page {page_id}: {str(e)}")
            return None

    def _set_single_property(
        self, page_id: str, property_key: str, value: str | None
    ) -> bool:
        """Set or remove a single page property via v1 API.

        Uses create (POST) for new properties and update (PUT) for existing ones.
        The v1 API requires a version number when updating existing properties.

        Args:
            page_id: The ID of the page
            property_key: The prop
... [truncated]
```

### scripts/oauth_authorize.py
```
#!/usr/bin/env python
"""
OAuth 2.0 Authorization Flow Helper for MCP Atlassian

This script helps with the OAuth 2.0 (3LO) authorization flow for Atlassian Cloud:
1. Opens a browser to the authorization URL
2. Starts a local server to receive the callback with the authorization code
3. Exchanges the authorization code for access and refresh tokens
4. Saves the tokens for later use by MCP Atlassian

Usage:
    python oauth_authorize.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
                             --redirect-uri http://localhost:8080/callback
                             --scope "read:jira-work write:jira-work read:confluence-space.summary offline_access"

IMPORTANT: The 'offline_access' scope is required for refresh tokens to work properly.
Without this scope, tokens will expire quickly and authentication will fail.

Environment variables can also be used:
- ATLASSIAN_OAUTH_CLIENT_ID
- ATLASSIAN_OAUTH_CLIENT_SECRET
- ATLASSIAN_OAUTH_REDIRECT_URI
- ATLASSIAN_OAUTH_SCOPE
"""

import argparse
import http.server
import logging
import os
import secrets
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser

# Add the parent directory to the path so we can import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp_atlassian.utils.oauth import OAuthConfig

# Configure logging (basicConfig should be called only once, ideally at the very start)
# Adding lineno for better debugging.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(lineno)d - %(message)s",
    force=True,
)


logger = logging.getLogger("oauth-authorize")
logger.setLevel(logging.DEBUG)
logging.getLogger("mcp-atlassian.oauth").setLevel(logging.DEBUG)

# Global variables for callback handling
authorization_code = None
received_state = None
callback_received = False
callback_error = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests (OAuth callback and favicon)."""
        global authorization_code, callback_received, callback_error, received_state

        parsed_path = urllib.parse.urlparse(self.path)
        logger.debug(f"CallbackHandler received GET request for: {self.path}")

        # Ignore favicon requests politely
        if parsed_path.path == "/favicon.ico":
            self.send_error(404, "File not found")
            logger.debug("CallbackHandler: Ignored /favicon.ico request.")
            return

        # Process only /callback path
        if parsed_path.path != "/callback":
            self.send_error(404, "Not Found: Only /callback is supported.")
            logger.warning(
                f"CallbackHandler: Received request for unexpected path: {parsed_path.path}"
            )
            return

        # Parse the query parameters from the URL
        query = parsed_path.query
        params = urllib.parse.parse_qs(query)

        if "error" in params:
            callback_error = params["error"][0]
            callback_received = True
            logger.error(f"Authorization error from callback: {callback_error}")
            self._send_response(f"Authorization failed: {callback_error}")
            return

        if "code" in params:
            authorization_code = params["code"][0]
            if "state" in params:
                received_state = params["state"][0]
            callback_received = True
            logger.info(
                "Authorization code and state received successfully via callback."
            )
            self._send_response(
                "Authorization successful! You can close this window now."
            )
        else:
            logger.error("Invalid callback: 'code' or 'error' parameter missing.")
            self._send_response(
                "Invalid callback: Authorization code missing", status=400
            )

    def _send_response(self, message: str, status: int = 200) -> None:
        """Send response to the browser."""
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Atlassian OAuth Authorization</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 40px;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .message {{
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .success {{
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
            </style>
        </head>
        <body>
            <h1>Atlassian OAuth Authorization</h1>
            <div class="message {"success" if status == 200 else "error"}">
                <p>{message}</p>
            </div>
            <p>This window will automatically close in 5 seconds...</p>
            <script>
                setTimeout(function() {{
                    window.close();
                }}, 5000);
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    # Make the server quiet
    def log_message(self, format: str, *args: str) -> None:
        return


def start_callback_server(port: int) -> socketserver.TCPServer:
    """Start a local server to receive the OAuth callback."""
    handler = CallbackHandler
    httpd = socketserver.TCPServer(("", port), handler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return httpd


def wait_for_callback(timeout: int = 300) -> bool:
    """Wait for the callback to be received."""
    start_time = time.time()
    while not callback_received and (time.time() - start_time) < timeout:
        time.sleep(1)

    if not callback_received:
        logger.error(
            f"Timed out waiting for authorization callback after {timeout} seconds"
        )
        return False

    if callback_error:
        logger.error(f"Authorization error: {callback_error}")
        return False

    return True


def parse_redirect_uri(redirect_uri: str) -> tuple[str, int]:
    """Parse the redirect URI to extract host and port."""
    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.hostname, port


def run_oauth_flow(args: argparse.Namespace) -> bool:
    """Run the OAuth 2.0 authorization flow."""
    # Create OAuth configuration
    oauth_config = OAuthConfig(
        client_id=args.client_id,
        client_secret=args.client_secret,
        redirect_uri=args.redirect_uri,
        scope=args.scope,
    )

    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(16)

    # Start local callback server if using localhost
    hostname, port = parse_redirect_uri(args.redirect_uri)
    httpd = None

    if hostname and hostname.lower() in ["localhost", "127.0.0.1"]:
        logger.info(f"Attempting to start local callback server on {hostname}:{port}")
        try:
            httpd = start_callback_server(port)
        except OSError as e:
            logger.error(f"Failed to start callback server: {e}")
            logger.error(f"Make sure port {port} is available and not in use")
            return False

    # Get the authorization URL
    auth_url = oauth_config.get_authorization_url(state=state)

    # Open the browser for authorization
    logger.info(f"Opening browser for authorization at {auth_url}")
    webbrowser.open(auth_url)
    logger.info(
        "If the browser doesn't open automatically, please visit this URL manually."
    )

    # Wait for the callback
    if not wait_for_callback():
        if httpd:
            httpd.shutdown()
        return False

    # Verify state to prevent CSRF attacks
    if received_state != state:
        logger.error(
            f"State mismatch! Possible CSRF attack. Expected: {state}, Received: {received_state}"
        )
        if httpd:
            httpd.shutdown()
        return False
    logger.info("CSRF state verified successfully.")

    # Exchange the code for tokens
    logger.info("Exchanging authorization code for tokens...")
    if not authorization_code:
        logger.error("Authorization code is missing, cannot exchange for tokens.")
        if httpd:
            httpd.shutdown()
        return False

    if oauth_config.exchange_code_for_tokens(authorization_code):
        logger.info("🎉 OAuth authorization flow completed successfully!")

        if oauth_config.cloud_id:
            logger.info(f"Retrieved Cloud ID: {oauth_config.cloud_id}")
            logger.info(
                "\n💡 Tip: Add/update the following in your .env file or environment variables:"
            )
            logger.info(f"ATLASSIAN_OAUTH_CLIENT_ID={oauth_config.client_id}")
            logger.info(f"ATLASSIAN_OAUTH_CLIENT_SECRET={oauth_config.client_secret}")
            logger.info(f"ATLASSIAN_OAUTH_REDIRECT_URI={oauth_config.redirect_uri}")
            logger.info(f"ATLASSIAN_OAUTH_SCOPE={oauth_config.scope}")
            logger.info(f"ATLASSIAN_OAUTH_CLOUD_ID={oauth_config.cloud_id}")
        else:
            logger.warning(
                "Cloud ID could not be obtained. Some API calls might require it."
            )

        if httpd:
            httpd.shutdown()
        return True
    else:
        logger.error("Failed to exchange authorization code for tokens")
        if httpd:
            httpd.shutdown()
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OAuth 2.0 Authorization Flow Helper for MCP Atlassian"
    )
    parser.add_argument("--client-id", help="OAuth Client ID")
    parser.add_argument("--client-secret", help="OAuth Client Secret")
    parser.add_argument(
        "--redirect-uri",
        help="OAuth Redirect URI (e.g., http://localhost:8080/callback)",
    )
    parser.add_argument("--scope", help="OAuth Scope (space-separated)")

    args = parser.parse_args()

    # Check for environment variables if arguments are not provided
    if not args.client_id:
        args.client_id = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID")
    if not args.client_secret:
        args.client_secret = os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET")
    if not args.redirect_uri:
        args.redirect_uri = os.getenv("ATLASSIAN_OAUTH_REDIRECT_URI")
    if not args.scope:
        args.scope = os.getenv("ATLASSIAN_OAUTH_SCOPE")

    # Validate required arguments
    missing = []
    if not args.client_id:
        missing.append("client-id")
    if not args.client_secret:
        missing.append("client-secret")
    if not args.redirect_uri:
        missing.append("redirect-uri")
    if not args.scope:
        missing.append("scope")

    if missing:
        logger.error(f"Missing required arguments: {', '.join(missing)}")
        parser.print_help()
        return 1

    # Check for offline_access scope
    if args.scope and "offline_access" not in args.scope.split():
        logger.warning("\n⚠️ WARNING: The 'offline_access' scope is missing!")
        logger.warning(
            "Without this scope, refresh tokens will not be issued and authentication will fail when tokens expire."
        )
        logger.warning("Consider adding 'offline_access' to your scope string.")
        proceed = input("Do you w
... [truncated]
```

### src/mcp_atlassian/confluence/permissions.py
```
"""Module for Confluence permission operations."""

import logging
from typing import Any, cast

from requests.exceptions import HTTPError

from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class PermissionsMixin(ConfluenceClient):
    """Mixin for Confluence permission operations."""

    def _require_cloud_permissions_api(self) -> None:
        """Ensure the Cloud permissions APIs are available."""
        if not self.config.is_cloud:
            msg = (
                "Confluence permission inspection is only available for "
                "Confluence Cloud. Server/Data Center instances use different "
                "permission APIs."
            )
            raise ValueError(msg)

    def _permissions_rest_base_url(self) -> str:
        """Return the REST base URL for Cloud permission endpoints."""
        if self.config.auth_type == "oauth" and self.config.is_cloud:
            return str(self.confluence.url).rstrip("/")

        base_url = self.config.url.rstrip("/")
        if self.config.is_cloud and not base_url.endswith("/wiki"):
            base_url = f"{base_url}/wiki"
        return base_url

    def check_content_permissions(
        self,
        content_id: str,
        user_identifier: str,
        operation: str,
        subject_type: str = "user",
    ) -> dict[str, Any]:
        """Check whether a user or group has a specific permission on content.

        Wraps POST /wiki/rest/api/content/{id}/permission/check.

        Args:
            content_id: The ID of the page, blog post, or other content.
            user_identifier: Account ID (for users) or group ID (for groups).
            operation: The operation to check, e.g. "read", "update", "delete".
            subject_type: Whether the subject is a "user" or "group".
                Defaults to "user".

        Returns:
            Dictionary with a "hasPermission" boolean key.

        Raises:
            ValueError: If the API call fails or returns an unexpected response.
            HTTPError: If authentication fails (401/403 are propagated).
        """
        self._require_cloud_permissions_api()
        url = (
            f"{self._permissions_rest_base_url()}"
            f"/rest/api/content/{content_id}/permission/check"
        )
        body = {
            "operation": operation,
            "subject": {
                "type": subject_type,
                "identifier": user_identifier,
            },
        }
        try:
            response = self.confluence._session.post(url, json=body)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except HTTPError as e:
            if e.response is not None and e.response.status_code in (401, 403):
                raise
            logger.error(
                f"HTTP error checking content permissions for '{content_id}': {e}"
            )
            msg = f"Failed to check permissions for content '{content_id}': {e}"
            raise ValueError(msg) from e
        except Exception as e:
            logger.error(f"Error checking content permissions for '{content_id}': {e}")
            msg = f"Failed to check permissions for content '{content_id}': {e}"
            raise ValueError(msg) from e

    def get_space_permissions(
        self,
        space_id: str,
        limit: int = 25,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List all permission assignments for a Confluence space.

        Wraps GET /wiki/api/v2/spaces/{id}/permissions.

        Args:
            space_id: The numeric ID of the space.
            limit: Maximum number of permission entries to return. Defaults to 25.
            cursor: Optional pagination cursor from a previous response.

        Returns:
            Dictionary with a "results" list of permission assignment objects,
            each containing "id", "principal", and "operation" fields.

        Raises:
            ValueError: If the API call fails or returns an unexpected response.
            HTTPError: If authentication fails (401/403 are propagated).
        """
        self._require_cloud_permissions_api()
        url = (
            f"{self._permissions_rest_base_url()}/api/v2/spaces/{space_id}/permissions"
        )
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        try:
            response = self.confluence._session.get(url, params=params)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except HTTPError as e:
            if e.response is not None and e.response.status_code in (401, 403):
                raise
            logger.error(
                f"HTTP error fetching space permissions for space '{space_id}': {e}"
            )
            msg = f"Failed to get permissions for space '{space_id}': {e}"
            raise ValueError(msg) from e
        except Exception as e:
            logger.error(
                f"Error fetching space permissions for space '{space_id}': {e}"
            )
            msg = f"Failed to get permissions for space '{space_id}': {e}"
            raise ValueError(msg) from e

```

### src/mcp_atlassian/jira/forms_api.py
```
"""Module for Jira Forms REST API operations.

This module provides support for the Jira Forms REST API at
https://api.atlassian.com/jira/forms/cloud/{cloudId}.

Features:
- UUID-based form IDs
- Atlassian Document Format (ADF) for form layouts
- Direct field updates via PUT /form/{formId}
- Support for form templates, attachments, and exports
"""

import logging
import os
from typing import Any

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

from ..models.jira import ProFormaForm
from .client import JiraClient
from .forms_common import handle_forms_http_error

logger = logging.getLogger("mcp-jira")


class FormsApiMixin(JiraClient):
    """Mixin for Jira Forms REST API operations.

    This uses the Forms API at https://api.atlassian.com/jira/forms/cloud/{cloudId}.
    The cloud_id is obtained from OAuth config or must be provided via environment variable.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Forms API mixin.

        Note:
            cloud_id is validated lazily when Forms API methods are called.
        """
        super().__init__(*args, **kwargs)

        # Get cloud_id from OAuth config if available, otherwise from environment variable
        if self.config.oauth_config and self.config.oauth_config.cloud_id:
            self._cloud_id: str | None = self.config.oauth_config.cloud_id
        else:
            # For non-OAuth auth types, check environment variable
            self._cloud_id = os.getenv("ATLASSIAN_OAUTH_CLOUD_ID")

    def _make_forms_api_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Forms API.

        Supports all authentication types: OAuth, PAT, and Basic Auth.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., '/issue/PROJ-123/form')
            data: Optional request body data

        Returns:
            Response data from the API as a dictionary

        Raises:
            ValueError: If cloud_id is not configured
            MCPAtlassianAuthenticationError: For 403 permission errors
            ValueError: For 404 not found errors
            Exception: For other HTTP errors
        """
        # Validate cloud_id is available
        if not self._cloud_id:
            error_msg = (
                "Forms API requires a cloud_id. "
                "For OAuth, this is automatically retrieved. "
                "For other auth types, provide it via ATLASSIAN_OAUTH_CLOUD_ID environment variable "
                "or X-Atlassian-Cloud-Id header."
            )
            raise ValueError(error_msg)

        url = f"https://api.atlassian.com/jira/forms/cloud/{self._cloud_id}{endpoint}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # Determine authentication method based on config
        auth = None
        if self.config.auth_type == "oauth":
            # For OAuth, use the session from the Jira client which has OAuth configured
            if hasattr(self.jira, "session") and self.jira.session:
                try:
                    response = self.jira.session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        timeout=30,
                    )
                    response.raise_for_status()

                    # Handle empty responses (like DELETE)
                    if not response.content:
                        return {}

                    json_response: dict[str, Any] = response.json()
                    return json_response
                except HTTPError as e:
                    logger.error(
                        f"HTTP error in Forms API (OAuth): {e} - Response: {e.response.text[:500]}"
                    )
                    raise handle_forms_http_error(
                        e, "Forms API request", endpoint
                    ) from e
                except requests.RequestException as e:
                    logger.error(
                        f"Request error making Forms API request to {endpoint}: {str(e)}"
                    )
                    raise
            else:
                error_msg = "OAuth session not available in Jira client"
                raise ValueError(error_msg)
        elif self.config.auth_type == "pat":
            # For PAT, use Bearer token authentication
            if self.config.personal_token:
                headers["Authorization"] = f"Bearer {self.config.personal_token}"
            else:
                error_msg = "Personal access token not configured"
                raise ValueError(error_msg)
        else:  # basic auth
            # For basic auth, use HTTPBasicAuth with username and API token
            username = self.jira.username or ""
            password = self.jira.password or ""
            auth = HTTPBasicAuth(username, password)

        # For PAT and basic auth, make the request with requests library
        if self.config.auth_type in ["pat", "basic"]:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    auth=auth,
                    headers=headers,
                    json=data,
                    timeout=30,
                )
                response.raise_for_status()

                # Handle empty responses (like DELETE)
                if not response.content:
                    return {}

                return response.json()

            except HTTPError as e:
                logger.error(
                    f"HTTP error in Forms API ({self.config.auth_type}): {e} - Response: {e.response.text[:500]}"
                )
                raise handle_forms_http_error(e, "Forms API request", endpoint) from e
            except requests.RequestException as e:
                logger.error(
                    f"Request error making Forms API request to {endpoint}: {str(e)}"
                )
                raise

        error_msg = f"Unsupported auth type: {self.config.auth_type}"
        raise ValueError(error_msg)

    def get_issue_forms(self, issue_key: str) -> list[ProFormaForm]:
        """Get all forms associated with an issue.

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')

        Returns:
            List of ProFormaForm objects

        Raises:
            Exception: If there is an error getting forms
        """
        try:
            response = self._make_forms_api_request("GET", f"/issue/{issue_key}/form")

            # API returns a plain array of forms
            forms_data = (
                response if isinstance(response, list) else response.get("forms", [])
            )

            forms = []
            for form_data in forms_data:
                try:
                    # API returns a simplified list format
                    # We'll need to fetch details for each form to get full data
                    form = ProFormaForm.from_api_response(
                        form_data, issue_key=issue_key
                    )
                    forms.append(form)
                except (KeyError, TypeError, ValueError) as e:
                    logger.error(f"Error parsing form data: {str(e)}")
                    continue

            return forms

        except ValueError as e:
            # Re-raise configuration errors (e.g., missing cloud_id) to fail fast
            if "cloud_id" in str(e).lower() or "forms api requires" in str(e).lower():
                raise
            # 404 - no forms found, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting forms for issue {issue_key}: {str(e)}")
            raise

    def get_form_details(self, issue_key: str, form_id: str) -> ProFormaForm | None:
        """Get detailed information about a specific form.

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')
            form_id: The form UUID (e.g. '1946b8b7-8f03-4dc0-ac2d-5fac0d960c6a')

        Returns:
            ProFormaForm object or None if not found

        Raises:
            Exception: If there is an error getting form details
        """
        try:
            response = self._make_forms_api_request(
                "GET", f"/issue/{issue_key}/form/{form_id}"
            )

            # API returns ADF (Atlassian Document Format) structure
            form = ProFormaForm.from_api_response(response, issue_key=issue_key)
            return form

        except ValueError as e:
            # Re-raise configuration errors (e.g., missing cloud_id) to fail fast
            if "cloud_id" in str(e).lower() or "forms api requires" in str(e).lower():
                raise
            # 404 - form not found, return None
            return None
        except Exception as e:
            logger.error(
                f"Error getting form details for {issue_key}/{form_id}: {str(e)}"
            )
            raise

    def update_form_answers(
        self, issue_key: str, form_id: str, answers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Update form field answers directly via the Forms API.

        **Known Limitation - DATETIME fields:**
        The Jira Forms API does not properly preserve time components in DATETIME fields.
        When updating DATETIME fields through this method, only the date is stored and the
        time is reset to midnight (00:00:00).

        **Workaround for DATETIME fields:**
        Use the regular Jira API to update the underlying custom fields directly:
        ```python
        jira.update_issue(issue_key, fields={
            "customfield_XXXXX": "2026-01-09T11:50:00-08:00"
        })
        ```
        The custom field ID can be found in the form's question definition (jiraField property).

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')
            form_id: The form UUID
            answers: List of answer objects, each with:
                - questionId: ID of the question to answer
                - type: Answer type (TEXT, NUMBER, DATE, etc.)
                - value: The answer value

        Returns:
            Response data from the API

        Raises:
            Exception: If there is an error updating the form
        """
        try:
            # Transform answers from list format to the API's expected object format
            # API expects: {"answers": {"questionId": {"type": value}, ...}}
            # We receive: [{"questionId": "1", "type": "TEXT", "value": "foo"}, ...]
            answers_dict = {}
            for answer in answers:
                question_id = answer.get("questionId")
                answer_type = answer.get("type", "TEXT")
                value = answer.get("value")

                # Map answer types to API field names
                # NOTE: DATETIME maps to "date" because the Forms API doesn't support
                # separate datetime fields. This is a known API limitation - only the
                # date portion is stored and time is lost. For datetime fields that need
                # time precision, use the regular Jira API to update the custom field directly.
                type_mapping = {
                    "TEXT": "text",
                    "NUMBER": "number",
                    "DATE": "date",
                    "DATETIME": "date",  # ⚠️ API limitation: loses time component
                    "TIME": "time",
                    "SELECT": "choices",
                    "MULTI_SELECT": "choices",
                    "CHECKBOX": "choices",
                    "USER": "users",
                    "MULTI_USER": "users",
                }

                field_name = type_mapping.get(answer_type, "text")

                # For choices/use
... [truncated]
```

### scripts/generate_tool_docs.py
```
#!/usr/bin/env python3
"""Generate MDX documentation for all MCP tools.

Introspects the FastMCP server instances (jira_mcp, confluence_mcp) to extract
tool metadata, then renders per-category MDX pages via a Jinja2 template.

Usage:
    python scripts/generate_tool_docs.py           # generate docs/tools/*.mdx
    python scripts/generate_tool_docs.py --check   # verify all tools are mapped

CI usage:
    python scripts/generate_tool_docs.py --check   # exits 1 if any tool is undocumented
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------

CATEGORY_TOOLS: dict[str, list[str]] = {
    "jira-issues": [
        "jira_get_issue",
        "jira_create_issue",
        "jira_update_issue",
        "jira_delete_issue",
        "jira_assign_issue",
        "jira_move_issue",
        "jira_batch_create_issues",
        "jira_transition_issue",
        "jira_get_transitions",
        "jira_get_all_projects",
        "jira_get_project_issues",
    ],
    "jira-search-fields": [
        "jira_search",
        "jira_search_fields",
        "jira_get_field_options",
        "jira_get_project_issue_types",
        "jira_get_create_fields",
        "jira_get_project_fields",
        "jira_search_projects",
    ],
    "jira-agile": [
        "jira_get_agile_boards",
        "jira_get_board_issues",
        "jira_get_sprints_from_board",
        "jira_get_sprint_issues",
        "jira_create_sprint",
        "jira_update_sprint",
        "jira_add_issues_to_sprint",
        "jira_move_issues_to_backlog",
    ],
    "jira-comments-worklogs": [
        "jira_add_comment",
        "jira_edit_comment",
        "jira_get_worklog",
        "jira_add_worklog",
        "jira_batch_get_changelogs",
        "jira_get_user_profile",
        "jira_search_assignable_users",
        "jira_get_issue_watchers",
        "jira_add_watcher",
        "jira_remove_watcher",
    ],
    "jira-links-versions": [
        "jira_get_link_types",
        "jira_create_issue_link",
        "jira_remove_issue_link",
        "jira_link_to_epic",
        "jira_create_remote_issue_link",
        "jira_get_project_versions",
        "jira_get_project_components",
        "jira_create_version",
        "jira_batch_create_versions",
        "jira_update_version",
    ],
    "jira-attachments": [
        "jira_download_attachments",
        "jira_get_issue_images",
    ],
    "jira-service-desk": [
        "jira_get_service_desk_for_project",
        "jira_get_service_desk_queues",
        "jira_get_queue_issues",
    ],
    "jira-forms-metrics": [
        "jira_get_issue_proforma_forms",
        "jira_get_proforma_form_details",
        "jira_update_proforma_form_answers",
        "jira_get_issue_dates",
        "jira_get_issue_sla",
        "jira_get_issue_development_info",
        "jira_get_issues_development_info",
    ],
    "confluence-pages": [
        "confluence_get_page",
        "confluence_create_page",
        "confluence_update_page",
        "confluence_delete_page",
        "confluence_get_page_children",
        "confluence_get_space_page_tree",
        "confluence_get_page_history",
        "confluence_update_page_section",
        "confluence_move_page",
        "confluence_copy_page",
        "confluence_get_page_restrictions",
        "confluence_set_page_restrictions",
        "confluence_get_page_diff",
    ],
    "confluence-search": [
        "confluence_search",
        "confluence_search_user",
    ],
    "confluence-attachments": [
        "confluence_upload_attachment",
        "confluence_upload_attachments",
        "confluence_get_attachments",
        "confluence_download_attachment",
        "confluence_download_content_attachments",
        "confluence_delete_attachment",
        "confluence_get_page_images",
    ],
    "confluence-comments": [
        "confluence_add_comment",
        "confluence_get_comments",
        "confluence_reply_to_comment",
        "confluence_get_inline_comments",
        "confluence_add_inline_comment",
        "confluence_get_labels",
        "confluence_add_label",
        "confluence_get_page_views",
    ],
    "confluence-permissions": [
        "confluence_check_content_permissions",
        "confluence_get_space_permissions",
    ],
}

CATEGORY_META: dict[str, dict[str, str]] = {
    "jira-issues": {
        "title": "Jira Issues",
        "description": ("Create, read, update, delete, and transition Jira issues"),
    },
    "jira-search-fields": {
        "title": "Jira Search & Fields",
        "description": ("Search issues with JQL, explore fields and field options"),
    },
    "jira-agile": {
        "title": "Jira Agile",
        "description": "Boards, sprints, and agile project management",
    },
    "jira-comments-worklogs": {
        "title": "Jira Comments & Worklogs",
        "description": ("Comments, worklogs, changelogs, and user profiles"),
    },
    "jira-links-versions": {
        "title": "Jira Links & Versions",
        "description": (
            "Issue links, epic links, remote links, versions, and components"
        ),
    },
    "jira-attachments": {
        "title": "Jira Attachments",
        "description": "Download attachments and render issue images",
    },
    "jira-service-desk": {
        "title": "Jira Service Desk",
        "description": "Service desk queues and queue issues",
    },
    "jira-forms-metrics": {
        "title": "Jira Forms & Metrics",
        "description": ("ProForma forms, SLA metrics, dates, and development info"),
    },
    "confluence-pages": {
        "title": "Confluence Pages",
        "description": ("Create, read, update, delete pages, and navigate page trees"),
    },
    "confluence-search": {
        "title": "Confluence Search",
        "description": "Search content with CQL and find users",
    },
    "confluence-attachments": {
        "title": "Confluence Attachments",
        "description": ("Upload, download, list, and manage page attachments"),
    },
    "confluence-comments": {
        "title": "Confluence Comments & Labels",
        "description": "Comments, labels, and page analytics",
    },
    "confluence-permissions": {
        "title": "Confluence Permissions",
        "description": "Inspect content and space permissions",
    },
}

# Build reverse lookup: tool_name -> category (with duplicate detection)
_TOOL_TO_CATEGORY: dict[str, str] = {}
for _cat, _tools in CATEGORY_TOOLS.items():
    for _t in _tools:
        if _t in _TOOL_TO_CATEGORY:
            raise ValueError(
                f"Tool '{_t}' is mapped to both '{_TOOL_TO_CATEGORY[_t]}' and '{_cat}'"
            )
        _TOOL_TO_CATEGORY[_t] = _cat


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ToolParam:
    """A single tool parameter."""

    name: str
    type: str
    required: bool
    description: str


@dataclass
class ToolOverride:
    """Optional YAML sidecar overrides for a tool."""

    example: str | None = None
    tips: str | None = None
    platform_notes: str | None = None


@dataclass
class ToolDoc:
    """Processed documentation for a single tool."""

    name: str
    display_name: str
    description: str
    is_write: bool
    parameters: list[ToolParam] = field(default_factory=list)
    override: ToolOverride | None = None


# ---------------------------------------------------------------------------
# Tool introspection
# ---------------------------------------------------------------------------


def _resolve_type(schema: dict[str, Any]) -> str:
    """Extract a human-readable type string from a JSON Schema property."""
    if "anyOf" in schema:
        types = [
            t.get("type", "object") for t in schema["anyOf"] if t.get("type") != "null"
        ]
        return types[0] if types else "any"
    return schema.get("type", "object")


def _first_line(text: str | None) -> str:
    """Return the first non-empty line of a docstring."""
    if not text:
        return ""
    for line in text.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _make_display_name(tool_name: str, annotations: Any) -> str:
    """Build a human-readable display name for a tool.

    Prefers the ``title`` from ToolAnnotations when available.
    Falls back to converting the prefixed tool name to title case.
    """
    title: str | None = None
    if annotations is not None:
        if hasattr(annotations, "title"):
            title = annotations.title
        elif isinstance(annotations, dict):
            title = annotations.get("title")
    if title:
        return title
    # Fallback: jira_get_issue -> Get Issue
    parts = tool_name.split("_")
    # Drop service prefix
    if parts and parts[0] in ("jira", "confluence"):
        parts = parts[1:]
    return " ".join(p.capitalize() for p in parts)


async def get_all_tools() -> dict[str, dict[str, Any]]:
    """Extract tools from both FastMCP server instances."""
    from mcp_atlassian.servers.confluence import confluence_mcp
    from mcp_atlassian.servers.jira import jira_mcp

    jira_tools = await jira_mcp.get_tools()
    confluence_tools = await confluence_mcp.get_tools()

    all_tools: dict[str, dict[str, Any]] = {}

    for name, tool in jira_tools.items():
        prefixed = f"jira_{name}"
        mcp_tool = tool.to_mcp_tool(name=prefixed)
        all_tools[prefixed] = {
            "mcp_tool": mcp_tool,
            "tags": tool.tags if hasattr(tool, "tags") else set(),
            "annotations": getattr(tool, "annotations", None),
            "is_write": "write" in (tool.tags if hasattr(tool, "tags") else set()),
        }

    for name, tool in confluence_tools.items():
        prefixed = f"confluence_{name}"
        mcp_tool = tool.to_mcp_tool(name=prefixed)
        all_tools[prefixed] = {
            "mcp_tool": mcp_tool,
            "tags": tool.tags if hasattr(tool, "tags") else set(),
            "annotations": getattr(tool, "annotations", None),
            "is_write": "write" in (tool.tags if hasattr(tool, "tags") else set()),
        }

    return all_tools


# ---------------------------------------------------------------------------
# Override loading
# ---------------------------------------------------------------------------


def load_overrides(overrides_dir: Path) -> dict[str, ToolOverride]:
    """Load YAML sidecar overrides from a directory."""
    overrides: dict[str, ToolOverride] = {}
    if not overrides_dir.is_dir():
        return overrides

    for yaml_file in sorted(overrides_dir.glob("*.yaml")):
        tool_name = yaml_file.stem
        with open(yaml_file) as f:
            data = yaml.safe_load(f) or {}
        overrides[tool_name] = ToolOverride(
            example=data.get("example"),
            tips=data.get("tips"),
            platform_notes=data.get("platform_notes"),
        )

    return overrides


# ---------------------------------------------------------------------------
# Tool processing
# ---------------------------------------------------------------------------


def build_tool_docs(
    tools: dict[str, dict[str, Any]],
    overrides: dict[str, ToolOverride],
) -> dict[str, list[ToolDoc]]:
    """Build per-category lists of ToolDoc objects."""
    category_docs: dict[str, list[ToolDoc]] = {cat: [] for cat in CATEGORY_TOOLS}

    for cat, tool_names in CATEGORY_TOOLS.items():
        for tool_name in tool_names:
            if tool_name not in tools:
                print(
                    f"WARNING: {tool_name} liste
... [truncated]
```

(+52 more files reference the changed code)
Repository Map
scripts/generate_tool_docs.py
scripts/oauth_authorize.py
src/mcp_atlassian/__init__.py
src/mcp_atlassian/confluence/__init__.py
src/mcp_atlassian/confluence/analytics.py
src/mcp_atlassian/confluence/attachments.py
src/mcp_atlassian/confluence/client.py
src/mcp_atlassian/confluence/comments.py
src/mcp_atlassian/confluence/config.py
src/mcp_atlassian/confluence/constants.py
src/mcp_atlassian/confluence/labels.py
src/mcp_atlassian/confluence/pages.py
src/mcp_atlassian/confluence/permissions.py
src/mcp_atlassian/confluence/protocols.py
src/mcp_atlassian/confluence/restrictions.py
src/mcp_atlassian/confluence/search.py
src/mcp_atlassian/confluence/spaces.py
src/mcp_atlassian/confluence/users.py
src/mcp_atlassian/confluence/utils.py
src/mcp_atlassian/confluence/v2_adapter.py
src/mcp_atlassian/exceptions.py
src/mcp_atlassian/jira/__init__.py
src/mcp_atlassian/jira/attachments.py
src/mcp_atlassian/jira/boards.py
src/mcp_atlassian/jira/client.py
src/mcp_atlassian/jira/comments.py
src/mcp_atlassian/jira/config.py
src/mcp_atlassian/jira/constants.py
src/mcp_atlassian/jira/development.py
src/mcp_atlassian/jira/epics.py
src/mcp_atlassian/jira/field_options.py
src/mcp_atlassian/jira/fields.py
src/mcp_atlassian/jira/formatting.py
src/mcp_atlassian/jira/forms.py
src/mcp_atlassian/jira/forms_api.py
src/mcp_atlassian/jira/forms_common.py
src/mcp_atlassian/jira/issues.py
src/mcp_atlassian/jira/links.py
src/mcp_atlassian/jira/metrics.py
src/mcp_atlassian/jira/projects.py
src/mcp_atlassian/jira/protocols.py
src/mcp_atlassian/jira/queues.py
src/mcp_atlassian/jira/search.py
src/mcp_atlassian/jira/sla.py
src/mcp_atlassian/jira/sprints.py
src/mcp_atlassian/jira/transitions.py
src/mcp_atlassian/jira/users.py
src/mcp_atlassian/jira/utils.py
src/mcp_atlassian/jira/watchers.py
src/mcp_atlassian/jira/worklog.py
src/mcp_atlassian/models/__init__.py
src/mcp_atlassian/models/base.py
src/mcp_atlassian/models/confluence/__init__.py
src/mcp_atlassian/models/confluence/analytics.py
src/mcp_atlassian/models/confluence/comment.py
src/mcp_atlassian/models/confluence/common.py
src/mcp_atlassian/models/confluence/label.py
src/mcp_atlassian/models/confluence/page.py
src/mcp_atlassian/models/confluence/search.py
src/mcp_atlassian/models/confluence/space.py
src/mcp_atlassian/models/confluence/user_search.py
src/mcp_atlassian/models/constants.py
src/mcp_atlassian/models/jira/__init__.py
src/mcp_atlassian/models/jira/adf.py
src/mcp_atlassian/models/jira/agile.py
src/mcp_atlassian/models/jira/comment.py
src/mcp_atlassian/models/jira/common.py
src/mcp_atlassian/models/jira/field_option.py
src/mcp_atlassian/models/jira/forms.py
src/mcp_atlassian/models/jira/issue.py
src/mcp_atlassian/models/jira/link.py
src/mcp_atlassian/models/jira/metrics.py
src/mcp_atlassian/models/jira/project.py
src/mcp_atlassian/models/jira/queue.py
src/mcp_atlassian/models/jira/search.py
src/mcp_atlassian/models/jira/sla.py
src/mcp_atlassian/models/jira/version.py
src/mcp_atlassian/models/jira/workflow.py
src/mcp_atlassian/models/jira/worklog.py
src/mcp_atlassian/preprocessing/__init__.py
src/mcp_atlassian/preprocessing/base.py
src/mcp_atlassian/preprocessing/confluence.py
src/mcp_atlassian/preprocessing/jira.py
src/mcp_atlassian/servers/__init__.py
src/mcp_atlassian/servers/client_storage.py
src/mcp_atlassian/servers/confluence.py
src/mcp_atlassian/servers/context.py
src/mcp_atlassian/servers/dependencies.py
src/mcp_atlassian/servers/jira.py
src/mcp_atlassian/servers/main.py
src/mcp_atlassian/servers/oauth_proxy.py
src/mcp_atlassian/utils/__init__.py
src/mcp_atlassian/utils/date.py
src/mcp_atlassian/utils/decorators.py
src/mcp_atlassian/utils/env.py
src/mcp_atlassian/utils/environment.py
src/mcp_atlassian/utils/http.py
src/mcp_atlassian/utils/io.py
src/mcp_atlassian/utils/lifecycle.py
src/mcp_atlassian/utils/logging.py
src/mcp_atlassian/utils/media.py
src/mcp_atlassian/utils/oauth.py
src/mcp_atlassian/utils/oauth_setup.py
src/mcp_atlassian/utils/pagination.py
src/mcp_atlassian/utils/ssl.py
src/mcp_atlassian/utils/token_verifier.py
src/mcp_atlassian/utils/tools.py
src/mcp_atlassian/utils/toolsets.py
src/mcp_atlassian/utils/urls.py
src/mcp_atlassian/utils/user_agent.py
tests/__init__.py
tests/conftest.py
tests/e2e/__init__.py
tests/e2e/cloud/__init__.py
tests/e2e/cloud/conftest.py
tests/e2e/cloud/test_adf_write.py
tests/e2e/cloud/test_confluence_auth_matrix.py
tests/e2e/cloud/test_confluence_cloud_operations.py
tests/e2e/cloud/test_confluence_dates.py
tests/e2e/cloud/test_confluence_page_metadata.py
tests/e2e/cloud/test_images_cloud.py
tests/e2e/cloud/test_jira_auth_matrix.py
tests/e2e/cloud/test_jira_cloud_operations.py
tests/e2e/cloud/test_jira_issue_creation_workflow.py
tests/e2e/cloud/test_jira_issue_include.py
tests/e2e/cloud/test_jira_user_profile_me.py
tests/e2e/cloud/test_jira_watchers.py
tests/e2e/cloud/test_mcp_tools_cloud.py
tests/e2e/conftest.py
tests/e2e/test_confluence_auth_matrix.py
tests/e2e/test_confluence_dc_operations.py
tests/e2e/test_images_dc.py
tests/e2e/test_jira_auth_matrix.py
tests/e2e/test_jira_dc_operations.py
tests/e2e/test_mcp_tools_dc.py
tests/e2e/test_user_lookup_dc.py
tests/integration/conftest.py
tests/integration/test_real_api.py
tests/integration/test_ssl_verification.py
tests/unit/auth/__init__.py
tests/unit/auth/test_authentication.py
tests/unit/confluence/__init__.py
tests/unit/confluence/conftest.py
tests/unit/confluence/test_analytics.py
tests/unit/confluence/test_attachments.py
tests/unit/confluence/test_client.py
tests/unit/confluence/test_client_oauth.py
tests/unit/confluence/test_comments.py
tests/unit/confluence/test_config.py
tests/unit/confluence/test_constants.py
tests/unit/confluence/test_custom_headers.py
tests/unit/confluence/test_labels.py
tests/unit/confluence/test_pages.py
tests/unit/confluence/test_permissions.py
tests/unit/confluence/test_restrictions.py
tests/unit/confluence/test_search.py
tests/unit/confluence/test_spaces.py
tests/unit/confluence/test_users.py
tests/unit/confluence/test_utils.py
tests/unit/confluence/test_v2_adapter.py
tests/unit/jira/conftest.py
tests/unit/jira/test_attachments.py
tests/unit/jira/test_boards.py
tests/unit/jira/test_client.py
tests/unit/jira/test_client_oauth.py
tests/unit/jira/test_comments.py
tests/unit/jira/test_config.py
tests/unit/jira/test_constants.py
tests/unit/jira/test_custom_headers.py
tests/unit/jira/test_development.py
tests/unit/jira/test_epics.py
tests/unit/jira/test_field_options.py
tests/unit/jira/test_fields.py
tests/unit/jira/test_format_conversion.py
tests/unit/jira/test_formatting.py
tests/unit/jira/test_forms_api.py
tests/unit/jira/test_issue_creation_logic.py
tests/unit/jira/test_issues.py
tests/unit/jira/test_issues_markdown.py
tests/unit/jira/test_jql_utils.py
tests/unit/jira/test_links.py
tests/unit/jira/test_metrics.py
tests/unit/jira/test_projects.py
tests/unit/jira/test_protocols.py
tests/unit/jira/test_queues.py
tests/unit/jira/test_search.py
tests/unit/jira/test_sla.py
tests/unit/jira/test_sprints.py
tests/unit/jira/test_transitions.py
tests/unit/jira/test_users.py
tests/unit/jira/test_watchers.py
tests/unit/jira/test_worklog.py
tests/unit/models/__init__.py
tests/unit/models/conftest.py
tests/unit/models/test_adf.py
tests/unit/models/test_base_models.py
tests/unit/models/test_confluence_common_models.py
tests/unit/models/test_confluence_page_model.py
tests/unit/models/test_confluence_real_data.py
tests/unit/models/test_confluence_search_model.py
tests/unit/models/test_constants.py
tests/unit/models/test_jira_comment_model.py
tests/unit/models/test_jira_common_models.py
tests/unit/models/test_jira_issue_model.py
tests/unit/models/test_jira_link_models.py
tests/unit/models/test_jira_project_model.py
tests/unit/models/test_jira_real_data.py
tests/unit/models/test_jira_search_model.py
tests/unit/models/test_jira_workflow_model.py
tests/unit/models/test_jira_worklog_model.py
tests/unit/preprocessing/__init__.py
tests/unit/preprocessing/test_content_processing.py
tests/unit/preprocessing/test_markdown_table_to_jira.py
tests/unit/preprocessing/test_preprocessing.py
tests/unit/servers/__init__.py
tests/unit/servers/test_client_storage.py
tests/unit/servers/test_confluence_server.py
tests/unit/servers/test_context.py
tests/unit/servers/test_cross_service.py
tests/unit/servers/test_datetime_conversion.py
tests/unit/servers/test_dependencies.py
tests/unit/servers/test_jira_server.py
tests/unit/servers/test_main_server.py
tests/unit/servers/test_mcp_protocol.py
tests/unit/servers/test_oauth_proxy_build.py
tests/unit/servers/test_schema_compatibility.py
tests/unit/servers/test_transport_lifecycle.py
tests/unit/test_exceptions.py
tests/unit/test_main_transport_selection.py
tests/unit/test_project_dependencies.py
tests/unit/test_stdin_monitoring_fix.py
tests/unit/test_stdio_lifecycle.py
tests/unit/test_truststore_env.py
tests/unit/utils/__init__.py
tests/unit/utils/test_custom_headers.py
tests/unit/utils/test_date.py
tests/unit/utils/test_decorators.py
tests/unit/utils/test_env.py
tests/unit/utils/test_environment.py
tests/unit/utils/test_http.py
tests/unit/utils/test_io.py
tests/unit/utils/test_lifecycle.py
tests/unit/utils/test_logging.py
tests/unit/utils/test_masking.py
tests/unit/utils/test_media.py
tests/unit/utils/test_oauth.py
tests/unit/utils/test_oauth_setup.py
tests/unit/utils/test_pagination.py
tests/unit/utils/test_proxy.py
tests/unit/utils/test_ssl.py
tests/unit/utils/test_token_verifier.py
tests/unit/utils/test_tools.py
tests/unit/utils/test_toolsets.py
tests/unit/utils/test_urls.py
tests/utils/__init__.py
tests/utils/assertions.py
tests/utils/base.py
tests/utils/factories.py
tests/utils/mocks.py
Package Manifests (Dependencies, scripts, build configuration)
### pyproject.toml
```
[project]
name = "mcp-atlassian"
dynamic = ["version"]
description = "The Model Context Protocol (MCP) Atlassian integration is an open-source implementation that bridges Atlassian products (Jira and Confluence) with AI language models following Anthropic's MCP specification. This project enables secure, contextual AI interactions with Atlassian tools while maintaining data privacy and security. Key features include:"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "atlassian-python-api>=4.0.0",
    "requests[socks]>=2.31.0",
    "beautifulsoup4>=4.12.3",
    "httpx>=0.28.0",
    "mcp>=1.8.0,<2.0.0",
    "fastmcp>=2.14.0,<2.15.0",
    "fakeredis>=2.32.1,<2.35.0",
    "python-dotenv>=1.0.1",
    "markdownify>=0.11.6",
    "markdown>=3.7.0",
    "markdown-to-confluence>=0.3.4,<0.4.0",
    "pydantic>=2.10.6,<3.0",
    "trio>=0.29.0",
    "click>=8.1.7",
    "uvicorn>=0.27.1",
    "starlette>=0.49.1",
    "urllib3>=2.6.3",
    "thefuzz>=0.22.1",
    "python-dateutil>=2.9.0.post0",
    "types-python-dateutil>=2.9.0.20241206",
    "keyring>=25.6.0",
    "cachetools>=5.0.0",
    "types-cachetools>=5.5.0.20240820",
    "unidecode>=1.3.0",
    "truststore>=0.10.0",
    "tzdata>=2024.1; platform_system=='Windows'",
]
[[project.authors]]
name = "sooperset"
email = "soomiles.dev@gmail.com"

[build-system]
requires = ["hatchling", "uv-dynamic-versioning>=0.7.0"]
build-backend = "hatchling.build"

[project.scripts]
mcp-atlassian = "mcp_atlassian:main"

[dependency-groups]
dev = [
    "uv>=0.1.0",
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-anyio>=0.0.0",
    "pre-commit>=3.6.0",
    "ruff>=0.3.0",
    "black>=24.2.0",
    "mypy>=1.8.0",
    "mcp[cli]>=1.3.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "types-pyyaml>=6.0"
]

[tool.pytest.ini_options]
markers = [
    "integration: mark test as requiring integration with real services",
    "dc_e2e: mark test as requiring DC instances (Jira DC + Confluence DC)",
    "cloud_e2e: mark test as requiring Cloud instances (Jira Cloud + Confluence Cloud)",
]

[tool.ruff]
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]
line-length = 88
indent-width = 4
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "B", "W", "I", "N", "UP", "ANN", "S", "BLE", "FBT", "C4", "DTZ", "T10", "EM", "ISC", "ICN"]
ignore = ["ANN401", "EM101"]
fixable = ["ALL"]
unfixable = []
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S", "ANN", "B017"]
"tests/fixtures/*.py" = ["E501"]
"src/mcp_atlassian/server.py" = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = false
warn_no_return = true
warn_unreachable = true
strict_equality = true
strict_optional = true
disallow_subclassing_any = true
warn_incomplete_stub = true
exclude = "^src/"
explicit_package_bases = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
check_untyped_defs = false

[[tool.mypy.overrides]]
module = "atlassian.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "markdownify.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "src.mcp_atlassian.*"
disallow_untyped_defs = false

[tool.hatch.version]
source = "uv-dynamic-versioning"

[tool.uv-dynamic-versioning]
vcs = "git"
style = "pep440"
bump = true
fallback-version = "0.0.0"

```
Context & Existing Test Patterns
Existing test files touched by the patch: tests/e2e/cloud/test_confluence_cloud_operations.py, tests/e2e/cloud/test_mcp_tools_cloud.py, tests/e2e/conftest.py, tests/e2e/test_confluence_dc_operations.py, tests/e2e/test_mcp_tools_dc.py, tests/unit/confluence/test_attachments.py, tests/unit/confluence/test_client.py, tests/unit/confluence/test_search.py, tests/unit/jira/test_attachments.py, tests/unit/jira/test_client.py, tests/unit/jira/test_search.py, tests/unit/servers/test_confluence_server.py, tests/unit/servers/test_dependencies.py, tests/unit/servers/test_main_server.py, tests/unit/servers/test_mcp_protocol.py, tests/unit/utils/test_oauth.py, tests/unit/utils/test_oauth_setup.py, tests/unit/utils/test_ssrf_adapter.py, tests/unit/utils/test_urls.py
Repository top-level entries: .claude, .devcontainer, .dockerignore, .env.example, .github, .gitignore, .mintignore, .pre-commit-config.yaml, .worktreeinclude, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, Dockerfile, LICENSE, README.md, SECURITY.md, docs, docs.json, helm, pyproject.toml, scripts, smithery.yaml, src, tests, uv.lock
Project's own test patterns and conventions:
### tests/conftest.py
```
"""
Root pytest configuration file for MCP Atlassian tests.

This module provides session-scoped fixtures and utilities that are shared
across all test modules. It integrates with the new test utilities framework
to provide efficient, reusable test fixtures.
"""

import pytest

from tests.utils.factories import (
    AuthConfigFactory,
    ConfluencePageFactory,
    ErrorResponseFactory,
    JiraIssueFactory,
)
from tests.utils.mocks import MockAtlassianClient, MockEnvironment

# Restrict anyio tests to asyncio backend only (FastMCP client requires asyncio)
pytest_plugins = ("anyio",)


@pytest.fixture(params=["asyncio"])
def anyio_backend(request):
    """Override anyio backend to only use asyncio."""
    return request.param


def pytest_addoption(parser):
    """Add command-line options for tests."""
    parser.addoption(
        "--use-real-data",
        action="store_true",
        default=False,
        help="Run tests that use real API data (requires env vars)",
    )


# ============================================================================
# Session-Scoped Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def session_auth_configs():
    """
    Session-scoped fixture providing authentication configuration templates.

    This fixture is computed once per test session and provides standard
    authentication configurations for OAuth and basic auth scenarios.

    Returns:
        Dict[str, Dict[str, str]]: Authentication configuration templates
    """
    return {
        "oauth": AuthConfigFactory.create_oauth_config(),
        "basic_auth": AuthConfigFactory.create_basic_auth_config(),
        "jira_basic": {
            "url": "https://test.atlassian.net",
            "username": "test@example.com",
            "api_token": "test-jira-token",
        },
        "confluence_basic": {
            "url": "https://test.atlassian.net/wiki",
            "username": "test@example.com",
            "api_token": "test-confluence-token",
        },
    }


@pytest.fixture(scope="session")
def session_mock_data():
    """
    Session-scoped fixture providing mock data templates.

    This fixture creates mock data templates once per session to avoid
    recreating expensive mock objects for every test.

    Returns:
        Dict[str, Any]: Mock data templates for various API responses
    """
    return {
        "jira_issue": JiraIssueFactory.create(),
        "jira_issue_minimal": JiraIssueFactory.create_minimal(),
        "confluence_page": ConfluencePageFactory.create(),
        "api_error": ErrorResponseFactory.create_api_error(),
        "auth_error": ErrorResponseFactory.create_auth_error(),
        "jira_search_results": {
            "issues": [
                JiraIssueFactory.create("TEST-1"),
                JiraIssueFactory.create("TEST-2"),
                JiraIssueFactory.create("TEST-3"),
            ],
            "total": 3,
            "startAt": 0,
            "maxResults": 50,
        },
    }


# ============================================================================
# Environment and Configuration Fixtures
# ============================================================================


@pytest.fixture
def clean_environment():
    """
    Fixture that provides a clean environment with no auth variables.

    This is useful for testing error conditions and configuration validation.
    """
    with MockEnvironment.clean_env() as env:
        yield env


@pytest.fixture
def oauth_environment():
    """
    Fixture that provides a complete OAuth environment setup.

    This sets up all necessary OAuth environment variables for testing
    OAuth-based authentication flows.
    """
    with MockEnvironment.oauth_env() as env:
        yield env


@pytest.fixture
def basic_auth_environment():
    """
    Fixture that provides basic authentication environment setup.

    This sets up username/token authentication for both Jira and Confluence.
    """
    with MockEnvironment.basic_auth_env() as env:
        yield env


# ============================================================================
# Factory-Based Fixtures
# ============================================================================


@pytest.fixture
def make_jira_issue():
    """
    Factory fixture for creating Jira issues with customizable properties.

    Returns:
        Callable: Factory function that creates Jira issue data

    Example:
        def test_issue_creation(make_jira_issue):
            issue = make_jira_issue(key="CUSTOM-123",
                                  fields={"priority": {"name": "High"}})
            assert issue["key"] == "CUSTOM-123"
    """
    return JiraIssueFactory.create


@pytest.fixture
def make_confluence_page():
    """
    Factory fixture for creating Confluence pages with customizable properties.

    Returns:
        Callable: Factory function that creates Confluence page data

    Example:
        def test_page_creation(make_confluence_page):
            page = make_confluence_page(title="Custom Page",
                                      space={"key": "CUSTOM"})
            assert page["title"] == "Custom Page"
    """
    return ConfluencePageFactory.create


@pytest.fixture
def make_auth_config():
    """
    Factory fixture for creating authentication configurations.

    Returns:
        Dict[str, Callable]: Factory functions for different auth types

    Example:
        def test_oauth_config(make_auth_config):
            config = make_auth_config["oauth"](client_id="custom-id")
            assert config["client_id"] == "custom-id"
    """
    return {
        "oauth": AuthConfigFactory.create_oauth_config,
        "basic": AuthConfigFactory.create_basic_auth_config,
    }


@pytest.fixture
def make_api_error():
    """
    Factory fixture for creating API error responses.

    Returns:
        Callable: Factory function that creates error response data

    Example:
        def test_error_handling(make_api_error):
            error = make_api_error(status_code=404, message="Not Found")
            assert error["status"] == 404
    """
    return ErrorResponseFactory.create_api_error


# ============================================================================
# Mock Client Fixtures
# ============================================================================


@pytest.fixture
def mock_jira_client():
    """
    Fixture providing a pre-configured mock Jira client.

    The client comes with sensible defaults for common operations
    but can be customized per test as needed.

    Returns:
        MagicMock: Configured mock Jira client
    """
    return MockAtlassianClient.create_jira_client()


@pytest.fixture
def mock_confluence_client():
    """
    Fixture providing a pre-configured mock Confluence client.

    The client comes with sensible defaults for common operations
    but can be customized per test as needed.

    Returns:
        MagicMock: Configured mock Confluence client
    """
    return MockAtlassianClient.create_confluence_client()


# ============================================================================
# Compatibility Fixtures (maintain backward compatibility)
# ============================================================================


@pytest.fixture
def use_real_jira_data(request):
    """
    Check if real Jira data tests should be run.

    This will be True if the --use-real-data flag is passed to pytest.

    Note: This fixture is maintained for backward compatibility.
    """
    return request.config.getoption("--use-real-data")


@pytest.fixture
def use_real_confluence_data(request):
    """
    Check if real Confluence data tests should be run.

    This will be True if the --use-real-data flag is passed to pytest.

    Note: This fixture is maintained for backward compatibility.
    """
    return request.config.getoption("--use-real-data")


# ============================================================================
# Advanced Environment Utilities
# ============================================================================


@pytest.fixture
def env_var_manager():
    """
    Fixture providing utilities for managing environment variables in tests.

    Returns:
        MockEnvironment: Environment management utilities

    Example:
        def test_with_custom_env(env_var_manager):
            with env_var_manager.oauth_env():
                # Test OAuth functionality
                pass
    """
    return MockEnvironment


@pytest.fixture
def parametrized_auth_env(request):
    """
    Parametrized fixture for testing with different authentication environments.

    This fixture can be used with pytest.mark.parametrize to test the same
    functionality with different authentication setups.

    Example:
        @pytest.mark.parametrize("parametrized_auth_env",
                               ["oauth", "basic_auth"], indirect=True)
        def test_auth_scenarios(parametrized_auth_env):
            # Test will run once for OAuth and once for basic auth
            pass
    """
    auth_type = request.param

    if auth_type == "oauth":
        with MockEnvironment.oauth_env() as env:
            yield env
    elif auth_type == "basic_auth":
        with MockEnvironment.basic_auth_env() as env:
            yield env
    elif auth_type == "clean":
        with MockEnvironment.clean_env() as env:
            yield env
    else:
        raise ValueError(f"Unknown auth type: {auth_type}")


# ============================================================================
# Session Validation and Health Checks
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def validate_test_environment():
    """
    Session-scoped fixture that validates the test environment setup.

    This fixture runs automatically and ensures that the test environment
    is properly configured for running the test suite.
    """
    # Validate that test utilities are importable
    try:
        import importlib.util

        # Check if modules can be imported
        for module_name in [
            "tests.fixtures.confluence_mocks",
            "tests.fixtures.jira_mocks",
            "tests.utils.base",
            "tests.utils.factories",
            "tests.utils.mocks",
        ]:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                pytest.fail(f"Failed to find module: {module_name}")
    except ImportError as e:
        pytest.fail(f"Failed to import test utilities: {e}")

    # Log session start
    print("\n🧪 Starting MCP Atlassian test session with enhanced fixtures")

    yield

    # Log session end
    print("\n✅ Completed MCP Atlassian test session")

```

### tests/e2e/cloud/conftest.py
```
"""Cloud E2E test configuration for Jira Cloud and Confluence Cloud.

Provides fixtures for running tests against real Atlassian Cloud instances.
Tests require the --cloud-e2e flag and valid Cloud credentials via env vars.

Pytest hooks (--cloud-e2e option, cloud_e2e marker, auto-skip) are registered
in the parent tests/e2e/conftest.py — NOT here. Pytest loads subdirectory
conftest files lazily after argument parsing.
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
import requests

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.utils.oauth import BYOAccessTokenOAuthConfig

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_PROJECT_KEY = "E2E"
DEFAULT_SPACE_KEY = "E2E"


# --- Data Classes ---


@dataclass
class CloudInstanceInfo:
    """Connection info for Cloud instances, loaded from environment."""

  
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

