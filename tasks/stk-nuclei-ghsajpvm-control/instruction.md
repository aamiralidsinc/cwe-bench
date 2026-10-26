# Scanner template engine: target data must stay data

Nuclei is a template-driven security scanner. An operator writes templates that describe requests,
and at scan time the engine renders the template text and sends requests. When the
environment-variable option is enabled, the scanner process's environment is made available as
template variables.

A scanner host's environment variables can be disclosed to an untrusted target: text the target
supplied is rendered as template source, and the environment variable it names is sent to the target
in place of that text.

**Security property (invariant).** Template-authored text may be rendered. Anything that entered
from the scan target — the target's own request data, its responses, and anything taken or derived
from them — must be treated as terminal, literal data. It must never be rendered, substituted or
evaluated as template source. When the template inserts such a value into a request in literal form,
any request that is sent must carry its bytes unchanged.

**Contracts**

- Refusal is a request-level error: the engine may decline to send a request whose template-authored
  syntax is still unresolved, report it, and continue the scan. Otherwise the request is sent with
  the target's bytes unchanged. In neither case may the re-interpreted value reach the target.
- The environment-variable option remains an operator opt-in.
- Everything that works today keeps working exactly as it does today.

This is one instance, not the full set. Fix the problem and its close variants; do not special-case
the example; do not look up the upstream fix.
