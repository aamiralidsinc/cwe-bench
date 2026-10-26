# A model's saved configuration must not be able to run arbitrary code

sentence-transformers loads embedding and reranking models from the Hugging Face Hub or from a
directory on this machine. A saved model is more than weights: it carries configuration that tells
the library which components to build, and some components are identified by naming the class that
implements them. Loading a model therefore reads configuration authored by whoever published the
model.

## Observed impact

A model directory downloaded from an untrusted source was loaded with

```python
SentenceTransformer("models/some-downloaded-model")
```

The caller did not allow untrusted code, and nothing about the call said it would run any. While
loading, the library imported and executed a Python module named by that directory's saved
configuration, before the caller ever had a working model.

## The property

A class reference carried by a model's stored configuration must never cause code outside the
sentence-transformers package to be imported or executed unless that particular load explicitly
allows untrusted code. This holds whether the model is identified by a Hub repository id or by a
path on this machine, and wherever the stored configuration is consulted.

An allowance is per load and per caller. A location that merely exists on this machine is not an
allowance, and neither is an absent trust decision.

## What must keep working

- Models that use only the library's own classes keep loading with no opt-in, exactly as today.
- A caller that explicitly allows untrusted code can still load a model's own modeling file and get
  a usable model.
- Programmatic class lookups that do not involve a model keep working as today.
- Everything else that works today keeps working exactly as today. State that the program produced
  itself is trusted: a run that restores state it saved earlier keeps working without a new
  opt-in, while configuration that came from somewhere else still needs one.

## Refusal contract

When a load cannot resolve a configuration-supplied reference without untrusted code, it fails with
a clear error before the referenced code is imported or run. Where the component has a documented
default, the load may use that default instead. Either way, nothing named by the configuration is
executed.

## Constraints

The example above is one example, not the full set: fix the problem and its close variants wherever
a model's stored configuration can select code. Keep legitimate use working; do not remove features
to avoid the problem. Do not look up or copy the upstream fix. Do not special-case the example.
