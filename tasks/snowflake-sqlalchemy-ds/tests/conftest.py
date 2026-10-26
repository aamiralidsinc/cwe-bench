"""Helpers shared by the hidden suites.

The security checks do not compare against one expected piece of SQL.  They lex
the compiled statement with Snowflake's string-literal rules (single quotes are
doubled; a backslash escapes the following character under the default
ESCAPE_STRING_LITERALS setting; double-quoted identifiers double their quotes)
and then assert two things about the attacker's value:

* it does not appear as bare SQL text (a keyword, punctuation or statement
  separator outside any literal/identifier), and
* where the dialect is supposed to preserve the value, it appears as exactly one
  literal/identifier whose decoded content is the value that was supplied.

This accepts any correct escaping spelling and rejects both "leave it raw" and
"drop the value" fixes.
"""

from __future__ import annotations

from snowflake.sqlalchemy import dialect as snowflake_dialect

MARKER = "PWNED_MARKER"

# Snowflake string-literal escapes (ESCAPE_STRING_LITERALS defaults to TRUE).
_ESCAPES = {
    "'": "'",
    '"': '"',
    "\\": "\\",
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "b": "\b",
    "f": "\f",
    "0": "\0",
}

_PUNCT = set("(),;=<>+-*/")


class Unterminated(Exception):
    """The statement contains a quote that is never closed: its structure broke."""


class Token:
    __slots__ = ("kind", "text", "value")

    def __init__(self, kind, text, value):
        self.kind = kind      # bare | literal | ident | punct
        self.text = text
        self.value = value

    def __repr__(self):
        return f"Token({self.kind!r}, {self.text!r})"


def lex(sql: str):
    """Split *sql* into bare words, literals, quoted identifiers and punctuation."""
    tokens = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c in " \t\r\n":
            i += 1
            continue
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            if j < 0:
                raise Unterminated("block comment")
            i = j + 2
            continue
        if c == "'":
            start = i
            i += 1
            out = []
            closed = False
            while i < n:
                ch = sql[i]
                if ch == "\\":
                    if i + 1 >= n:
                        raise Unterminated("escape at end of literal")
                    out.append(_ESCAPES.get(sql[i + 1], sql[i + 1]))
                    i += 2
                elif ch == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        out.append("'")
                        i += 2
                    else:
                        i += 1
                        closed = True
                        break
                else:
                    out.append(ch)
                    i += 1
            if not closed:
                raise Unterminated("string literal")
            tokens.append(Token("literal", sql[start:i], "".join(out)))
            continue
        if c == '"':
            start = i
            i += 1
            out = []
            closed = False
            while i < n:
                ch = sql[i]
                if ch == '"':
                    if i + 1 < n and sql[i + 1] == '"':
                        out.append('"')
                        i += 2
                    else:
                        i += 1
                        closed = True
                        break
                else:
                    out.append(ch)
                    i += 1
            if not closed:
                raise Unterminated("quoted identifier")
            tokens.append(Token("ident", sql[start:i], "".join(out)))
            continue
        if c in _PUNCT:
            tokens.append(Token("punct", c, c))
            i += 1
            continue
        j = i
        while j < n and sql[j] not in " \t\r\n'\"(),;=<>+-*/":
            j += 1
        tokens.append(Token("bare", sql[i:j], sql[i:j]))
        i = j
    return tokens


def compile_sql(statement, deterministic: bool = True) -> str:
    """Compile with the public Snowflake dialect object, as a downstream user would."""
    kwargs = {"literal_binds": True}
    if deterministic:
        kwargs["deterministic"] = True
    return str(statement.compile(dialect=snowflake_dialect(), compile_kwargs=kwargs))


def assert_inert(sql: str, marker: str = MARKER) -> None:
    """The marker must not survive as bare SQL text, and no statement separator either."""
    tokens = lex(sql)
    bare = " ".join(t.value for t in tokens if t.kind == "bare")
    assert marker not in bare, f"attacker marker is executable SQL: {sql!r}"
    assert not any(t.kind == "punct" and t.value == ";" for t in tokens), (
        f"attacker value introduced a statement separator: {sql!r}"
    )


def assert_literal(sql: str, value: str, marker: str = MARKER) -> None:
    """The value must end up as one string literal that decodes back to it."""
    assert_inert(sql, marker)
    literals = [t.value for t in lex(sql) if t.kind == "literal"]
    assert value in literals, f"value {value!r} not preserved as a literal; got {literals!r} in {sql!r}"


def assert_identifier(sql: str, value: str, marker: str = MARKER) -> None:
    """The value must end up as one quoted identifier that decodes back to it."""
    assert_inert(sql, marker)
    idents = [t.value for t in lex(sql) if t.kind == "ident"]
    assert value in idents, f"value {value!r} not preserved as an identifier; got {idents!r} in {sql!r}"


def assert_ident_parts(sql: str, parts, marker: str = MARKER) -> None:
    """Each dotted part must be present as an identifier (or a plain bare part)."""
    assert_inert(sql, marker)
    tokens = lex(sql)
    idents = [t.value for t in tokens if t.kind == "ident"]
    bare = [t.value for t in tokens if t.kind == "bare"]
    for part in parts:
        assert part in idents or part in bare, (
            f"qualified part {part!r} not preserved; idents={idents!r} bare={bare!r} in {sql!r}"
        )


def payload_literal(prefix: str = "x") -> str:
    """A harmless value that would add SQL text if the literal boundary broke."""
    return f"{prefix}\\'); {MARKER} --"


def payload_plain_quote(prefix: str = "x") -> str:
    return f"{prefix}'); {MARKER} --"


def payload_name(prefix: str = "x") -> str:
    return f"{prefix}, {MARKER}"

