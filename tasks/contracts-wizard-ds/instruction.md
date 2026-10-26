# Generated projects must contain supplied values as data, not as code

The OpenZeppelin Contracts Wizard turns a set of options — a token's name, symbol, token URI and
the other fields shown in the form — into Solidity contracts and complete starter projects that a
user downloads or prints. It supports more than one project format and target language.

One observed impact: in the wizard, choose an ERC-20, set the token name to `My "Token"`, and
download the Hardhat starter project. The generated test file no longer parses as written: text
from the name is read as JavaScript instead of as a value. A value written this way would run as
part of the generated project.

The invariant: every value supplied to the wizard that it copies into generated source must be
emitted as data. After generation that value must decode back to exactly the text that was
supplied, must stay inside the string literal or comment it was placed in, and must not be able
to add, end or alter any source line, statement or comment. The generated file must remain a
valid program for its target language. This holds for every option and every file the wizard
produces.

Contracts:
- If a supplied value cannot be represented safely in the context it is emitted into, the
  generator must refuse the request with a client error (a thrown error) and must not emit a file
  containing that value. It must never emit source that the value introduced.
- Everything that works today keeps working exactly as today: ordinary ASCII names, token URIs
  and non-ASCII display text must keep appearing unchanged in the same generated files, and the
  set of files must not change. Text containing a double quote, a backslash, an accent or an
  emoji is legitimate input and must round-trip exactly.
- These examples are illustrations, not the full set: the invariant covers every option the
  wizard accepts and every file it generates.

Constraints: fix the problem and its close variants; keep legitimate use working; do not look up
the upstream fix; do not special-case the examples.
