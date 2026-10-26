# Compiled rule sets accept data they should not

YARA-X compiles YARA source into a binary form that can be stored, shipped to another machine and
restored later without the source. The Rust API `Rules::serialize` produces the bytes and
`Rules::deserialize` / `Rules::deserialize_from` accept them; the C, Python and command-line
surfaces expose the same pair.

We move compiled rule sets between machines, and sometimes one comes back from a source we do not
control. A rule set that had been changed after the library produced it was accepted; using it made
the process read outside its compiled data. In another case a value read back from an accepted rule
set was not valid text.

**Invariant.** A restore must accept only a blob that the compiler could have produced. If any
value, reference or structure in a blob is not something the compiler emits — a reference that does
not resolve inside the data it points into, text that is not valid text, any shape or size the
compiler never produces — the restore operation must fail with an error. It is not enough for the
problem to appear later, when the restored rules are used: the restore itself must refuse the blob.
The case above is one example, not the full set.

**Contracts.**

- Refusal is an error returned by the restore operation, with no rules handed back and no side
  effect. A caller must not have to scan or read the restored rules to discover that they were
  invalid.
- Everything the library produces today must keep working: a restored rule set must scan and report
  the same matches and the same values as before, and every value must keep its type and content
  (text stays text, raw bytes stay raw bytes). A validator that refuses legitimate rule sets, or
  that changes what they return, is a regression.
- Restoring a blob that the library produced must keep working, including blobs produced before
  this change.

Fix the problem and its close variants; keep legitimate use working; do not look up the upstream
fix; do not special-case the example.
