# Public FAQ reads disclose records that are not published

phpMyFAQ is a self-hosted FAQ and knowledge-base application. Every FAQ record carries an
enabled flag and a publication window with a start and an end date, so editors can prepare an
entry ahead of its publication, disable one temporarily, or stop showing one after a date.

## What happens today

A visitor who is not logged in can read a record that is disabled or outside its publication
window by asking the public API for it. For example:

```
curl -s https://faq.example.org/api/v3.1/faq/1/12
```

returns the complete answer of record 12, together with its keywords, author, e-mail address and
publication dates, even though the record is disabled or not yet published. The record is not
listed in the public category overview, and a visitor has no way to tell from the overview that
it exists.

## What must hold

For a visitor who is not an administrator or an FAQ editor, a FAQ record is visible only while
it is enabled and the current time lies between its publication start and end dates, both
inclusive. No read surface available to such a visitor may disclose any part of a record that is
not visible at that moment: not its question, answer or any excerpt of the answer, and not its
identifiers, keywords, author, contact address, dates or notes. A record that is not visible must
be indistinguishable from a record that does not exist. When a response carries several records,
it carries the visible ones only, with no trace of the others.

Requests for a record that is not visible are answered with a client error or with an empty
result; they never contain data taken from the record. Responses for visible records keep their
current shape and fields.

Records that use the installation's default publication dates stay visible, and a record whose
publication window is currently open stays visible. Anything an administrator or an FAQ editor
can see or extract today, including records that are disabled, scheduled or expired, keeps
working exactly as today. That privileged behaviour is reserved for callers who really hold
those roles; an ordinary visitor must not obtain it by any request.

The request above is one example, not the full set: the same rule applies to every public way of
reading FAQ data.

## Constraints

- Fix the reported problem and its close variants.
- Keep legitimate use working exactly as today.
- Do not look up the advisory or the upstream fix.
- Do not special-case the example.
