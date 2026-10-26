# A model can make the interpreter read a tensor that was never given data

TensorFlow Lite is an inference runtime. A model describes a graph: tensors, each with a type, a
shape and, for constants, its data, plus the nodes that consume input tensors and produce output
tensors. An application loads such a model and runs it, and the runtime allocates the memory the
graph needs.

## Impact

We have a model that crashes the process instead of running it. The model declares a tensor that a
node consumes but that no memory is ever provided for: the tensor has a size, it has no data
buffer, and nothing in the graph produces it. Running the model dereferences that missing buffer,
and the process dies on an access at address zero instead of reporting that the graph cannot run.

## Requirement

Running or setting up a graph must never read through a tensor that carries no data. Wherever a
node would consume an input that has no data buffer, the runtime must refuse with an error rather
than dereference it, whatever the operator involved and however the graph was produced or supplied
to the runtime.

A node input that is declared but absent must likewise never be dereferenced: the node must either
proceed without it, when the operator can, or refuse cleanly.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

- An input that an operator never reads may be left without data; a model that does this keeps
  running exactly as today.
- A tensor that legitimately holds no elements has no data buffer either; graphs over empty
  tensors keep working.
- Everything else that works today keeps working exactly as today, including how a call reports
  its status and the values a graph produces.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
