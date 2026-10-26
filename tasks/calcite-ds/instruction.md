# Model-supplied class references must respect the deployment's deny list

Apache Calcite is a SQL engine that a host application configures with a *model*: a JSON or YAML
document describing the schemas, tables, functions and related objects the application exposes.
Some values in a model name Java classes that Calcite loads and instantiates while it opens a
connection.

A service lets its clients supply the model and connects with it through the model connection
property of `jdbc:calcite:`. A model that names a JDK class as the implementation of a
model-defined function causes that class to be initialized while the connection is being opened.
Because the client chooses the class, a suitable class runs code of the client's choosing inside
the service's process.

## The security property

Every class reference a model supplies, wherever in the model it appears, must be checked against
the deployment's deny list before any class is loaded or initialized. A model must never succeed in
causing a class named on the deny list to be loaded, initialized or instantiated, whatever form the
reference takes.

## Deployment contract

The deny list is configured with the system property `calcite.model.classes.denied`. Its value is a
comma-separated list of patterns; blank entries and whitespace around commas are ignored. A pattern
that ends in `.` covers that package and every sub-package; any other pattern is a complete,
case-sensitive class name. The property adds to the protection the product ships with; it never
removes a built-in entry.

## Behaviour the fix must keep

- A model that supplies a reference which resolves to a denied class is refused: the connection
  attempt fails and the denied class is not initialized.
- Everything that works today for classes the deny list does not name keeps working exactly as
  today, including references that select a member of the class. A model whose references are all
  allowed opens exactly as before.
- The example above is an example, not the full set of ways a model can name a class.

## Constraints

Fix the problem and its close variants. Keep legitimate use of models working. Do not look up an
upstream fix. Do not special-case the example above.
