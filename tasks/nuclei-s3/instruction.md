# Scanner templates: target data must stay data

Nuclei is a template-driven security scanner. An operator writes a template describing one or more
requests; at scan time the engine fills in template-authored placeholders and helper calls, sends
the requests, and evaluates expressions over the responses. With the environment-variable option
enabled, the scanner process's environment is available to templates.

A scanner host's environment variables can be disclosed to a target. The target answers a scan
request with text that names a template expression, and a later step of the same template reuses
the captured text; because the reused text is interpreted as template source, the environment
value is sent to the target instead of the text the target supplied. One concrete case: a flow
template scans the target, a value captured from the first response is used in a second, fuzzed
request, and the environment-variable option is on.

**Security property (invariant).** Template-authored text may be rendered and evaluated. Anything
that entered from the scanned target -- its request data, its responses, and anything taken or
derived from them -- is terminal data. It must never be interpreted as template or DSL source,
however it is inserted and whichever placeholder form it carries. When the template inserts such a
value in literal form, any request that is sent must carry its bytes unchanged.

**Contracts**

- Refusal is a request-level error with no side effect: the engine may decline to send a request
  whose template-authored syntax is still unresolved, report it and continue the scan. Otherwise
  the request is sent with the target's value unchanged. In neither case may a re-interpreted value
  reach the target or appear in a reported result.
- Template-authored placeholders still resolve from template-authored values, including inside
  authored helper calls and wherever an author writes them.
- A value supplied at scan time still takes precedence over a declared template variable of the
  same name, and is then used literally.
- Values taken from a response are still compared and reported byte for byte, including text that
  contains placeholder syntax.
- The environment-variable option remains an operator opt-in.
- Everything that works today keeps working exactly as it does today.

This is one instance, not the full set. Fix the problem and its close variants; do not special-case
the example; do not look up the upstream fix.
