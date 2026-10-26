# Opening a saved detector runs the file author's code

## System

PyOD is a Python library for anomaly detection. A user fits a detector and saves it to
a file, then later — in another process, on another machine, or after receiving the
file from a colleague or a model exchange — reads it back. The library offers several
public ways to read a saved object back.

## Observed impact

A user was handed a detector file by an outside party and opened it with the library's
public loader:

```python
from pyod.utils.persistence import load

detector = load("/models/vendor-detector.bin")
```

The call returned a detector and reported nothing unusual, but code chosen by the
file's author had already run inside the user's process with the user's privileges: it
could read files, send network requests, or overwrite anything the process could reach.
Nothing in the call asked the user whether the file could be trusted.

## Security property

No file may run code, or create or change anything on disk, merely because the library
reads it. A read must fail with an exception, before any of the file's content is
deserialized, unless the caller has explicitly vouched for the artifact's source. This
holds for every public way the library reads a saved object, for every shape of file
the library accepts, and whether or not the caller asks for stricter version checking.

## Contracts the fix must honor

- **Vouching.** A call that hands the library a saved object accepts a keyword argument
  `trusted`, false by default. `trusted=True` means the caller vouches for the source,
  and the call must then behave exactly as it does today. Without it, the call must
  raise an ordinary Python exception and leave no side effect; it must not end the
  process, and it must not return a placeholder in place of the object.
- **Preservation.** A caller that vouches must still be able to read every file the
  library reads today and get the same result — whatever release wrote the file,
  whatever state its stored representation is in, and however the path is supplied.
  Saving must keep producing files that today's readers accept.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the call shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
