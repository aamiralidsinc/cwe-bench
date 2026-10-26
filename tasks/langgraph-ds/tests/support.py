"""Small helpers shared by the behavioural suites; no product code is used here."""

from __future__ import annotations

import uuid

PG_URI = "postgresql://postgres:postgres@localhost:5441/postgres?sslmode=disable"


def unique(prefix: str) -> str:
    """A label that is unique across the whole test run."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def namespaces(items) -> list[tuple[str, ...]]:
    """The namespace of each returned item, as a tuple."""
    return [tuple(item.namespace) for item in items]
