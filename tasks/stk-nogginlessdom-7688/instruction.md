# A file snapshot can be written outside the project

Nogginlessdom is a zero-dependency testing framework for JavaScript and TypeScript. A test author
writes tests, the framework runs them, and an assertion can compare a value against a snapshot kept
in a separate file. When snapshot updates are enabled, a snapshot file that does not exist yet is
created so that later runs can compare against it.

A snapshot file path is not confined. With updates enabled, a path that points outside the project
makes the framework create the file there.

For example, with snapshot updates enabled:

```ts
expect(rendered).toMatchFileSnapshot('/tmp/report.txt');
```

creates `/tmp/report.txt` even though the project is elsewhere.

## Requirement

A file-snapshot path is always interpreted inside the project the tests run in: no path a caller
supplies may take a file-snapshot operation outside that project directory.

Snapshot storage that has been configured with its own directory is bounded by that directory: a
snapshot operation may not leave it.

A refusal is a thrown error and leaves nothing behind.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working exactly as today, apart from the behaviour the properties
above forbid.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix.
Do not special-case the example above.
