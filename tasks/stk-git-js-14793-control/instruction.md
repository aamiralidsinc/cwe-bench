# A caller-supplied value can still turn into a program `git` runs

`simple-git` is a Node.js library that applications use to run `git`. Values that an application's
callers supply reach the library and are passed into repository operations. The library already
refuses values that would let such an input become a program `git` runs, unless the application has
explicitly opted in to that behaviour.

That protection is incomplete. A caller-supplied value can still be recorded in the repository's
configuration as a command that a later ordinary operation runs. For example:

```js
await git.raw(['config', 'trailer.summary.command', value]);
```

records a value that a later log invocation executes as a program.

**Property.** For every invocation the library builds, a value supplied by the application's caller
must never cause `git` to run a program of the caller's choosing, however the library passes that
value to `git`, unless the application has enabled the existing opt-in that permits caller-chosen
programs. Every such value must be refused before `git` is started.

**Contracts.**

- A refused call must fail with a client error before `git` is started and must leave the
  repository and the environment unchanged.
- Everything that works today keeps working exactly as today, and an application that has enabled
  an opt-in must still be able to do exactly what that opt-in permits.
- The example above is an example, not the full set.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.
