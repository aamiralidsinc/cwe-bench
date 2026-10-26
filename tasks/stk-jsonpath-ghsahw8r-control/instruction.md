# Untrusted query expressions must not run as application code

## System

JSONPath-Plus is a query library for JSON documents. An application gives it a document and a
query string and receives the values that query selects. Expressions embedded in a query are
evaluated by the library, so the query text is untrusted input from whoever supplied it.

## Observed impact

A caller can execute arbitrary code inside the application's process. For example, evaluating a
filter expression supplied by a caller over an ordinary document such as `[{"a": 1}]` can invoke a
function chosen by the caller, and that code runs while the query is being evaluated.

## Security properties

1. **Evaluation stays restricted.** Every expression evaluated as part of a query is interpreted by
   the library's own restricted evaluator. The library never hands a caller-supplied expression to
   the host language engine.

2. **No route to executable code.** Evaluating a query never reaches or invokes an object that
   constructs executable code from text, and code obtained that way never runs. The decision rests
   on the value that is reached and what it can do.

## Contracts the fix must honor

- **Refusal.** A query that would violate either property fails with an error and has no effect: no
  caller-supplied code runs and no match is returned for it.
- **Preservation.** Everything that works today keeps working exactly as today.
- **Explicit choices.** Where the library documents a particular evaluation behaviour for callers
  who explicitly ask for it, that behaviour is unchanged.

## Constraints

- Fix the flaw and its close variants, not just the example shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
