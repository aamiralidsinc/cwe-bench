"""Headless Claude Code client (`claude -p`) shared by task generation, rubric check and trial analysis.

Uses the logged-in subscription session - no API key. Quota exhaustion raises QuotaExhausted so callers can stop
cleanly (pipeline state makes the run resumable).
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Optional

log = logging.getLogger(__name__)


class QuotaExhausted(Exception):
    """Subscription/API quota is used up; continuing would only burn retries."""


class SafeguardsFlagged(Exception):
    """Anthropic's safeguards flagged the session under the Acceptable Use Policy. This is an account-level enforcement
    signal, not an output filter: never retried and never routed to another model - the candidate is retired and a
    human reviews the account's usage."""


def normalize_model(name: str) -> str:
    """'opus-5.5' -> 'claude-opus-5-5'; full ids and CLI aliases ('opus') pass through."""
    m = re.fullmatch(r"(opus|sonnet|haiku|fable)-(\d+)\.(\d+)", name.strip().lower())
    return f"claude-{m[1]}-{m[2]}-{m[3]}" if m else name


class CliBackend:
    """Headless Claude Code (`claude -p`) using the logged-in subscription session.

    * prompt goes via stdin (no argv length limit); all tools are disabled; cwd is an empty temp dir
      so no project CLAUDE.md / settings leak into the generation
    * ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN are removed from the child environment, otherwise the CLI
      would bill that key instead of using the subscription login
    """
    _QUOTA_MARKERS = ("usage limit", "limit reached", "quota", "credit balance")
    _TRANSIENT_MARKERS = ("overloaded", "rate limit", "529", "503", "timed out", "temporarily", "econnreset")

    def __init__(self, claude_bin: str, timeout: float, retries: int = 3):
        if not shutil.which(claude_bin):
            raise SystemExit(f"`{claude_bin}` not found on PATH (is Claude Code installed and logged in?)")
        self.claude_bin, self.timeout, self.retries = claude_bin, timeout, retries

    @staticmethod
    def _flatten(messages: list[dict]) -> str:
        if len(messages) == 1:
            return messages[0]["content"]
        # Retry turn: original request, the previous output, then the validator's complaint.
        return (messages[0]["content"] + "\n\n# Your previous output\n" + messages[1]["content"]
                + "\n\n# Feedback\n" + messages[2]["content"])

    def complete(self, model: str, system: str, messages: list[dict], max_tokens: int) -> tuple[str, dict]:
        env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
        # On the host, always use the normal logged-in session; the OAuth token (from `claude setup-token`) is only for
        # containers, which have no access to the Mac keychain. A stale/invalid token must not break host runs.
        if not os.path.exists("/.dockerenv"):
            env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(max_tokens)
        cmd = [self.claude_bin, "-p", "--model", normalize_model(model), "--output-format", "json",
               "--tools", "", "--system-prompt", system, "--no-session-persistence"]
        last = "unknown"
        for attempt in range(1, self.retries + 1):
            with tempfile.TemporaryDirectory(prefix="taskgen_") as cwd:
                try:
                    proc = subprocess.run(cmd, input=self._flatten(messages), capture_output=True, text=True,
                                          timeout=self.timeout, cwd=cwd, env=env)
                except subprocess.TimeoutExpired:
                    last = f"claude CLI timed out after {self.timeout}s"
                    proc = None
            if proc is not None:
                text, usage, err = self._parse(proc)
                if not err:
                    return text, usage
                last = err
                low = err.lower()
                if "safeguards flagged" in low or "legal/aup" in low:
                    raise SafeguardsFlagged(err)
                if any(m in low for m in self._QUOTA_MARKERS):
                    raise QuotaExhausted(err)
                if not any(m in low for m in self._TRANSIENT_MARKERS) and proc.returncode == 0:
                    raise RuntimeError(err)  # e.g. refusal / invalid model: retrying will not help
            if attempt < self.retries:
                delay = 5 * 2 ** (attempt - 1)
                log.info("claude CLI call failed (attempt %d/%d), retrying in %ds: %s", attempt, self.retries, delay, last[:200])
                time.sleep(delay)
        raise RuntimeError(f"claude CLI failed after {self.retries} attempts: {last[:300]}")

    @staticmethod
    def _parse(proc: subprocess.CompletedProcess) -> tuple[str, dict, Optional[str]]:
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return "", {}, f"unparseable CLI output (exit {proc.returncode}): {(proc.stderr or proc.stdout)[-300:]}"
        if isinstance(data, list):  # stream-style array: take the final result object
            data = next((d for d in reversed(data) if isinstance(d, dict) and d.get("type") == "result"), {})
        if data.get("is_error") or proc.returncode != 0:
            return "", {}, str(data.get("result") or proc.stderr or "CLI reported an error")[:500]
        u = data.get("usage") or {}
        return data.get("result", ""), {"input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
                                         "cost_usd": data.get("total_cost_usd")}, None


def extract_json_object(text: str) -> dict:
    """First top-level JSON object in a model reply (tolerates prose and ``` fences around it)."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            depth += (text[i] == "{") - (text[i] == "}")
            if depth == 0:
                try:
                    obj = json.loads(text[start:i + 1])
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    pass
                break
        start = text.find("{", start + 1)
    raise ValueError("no JSON object found in model output")
