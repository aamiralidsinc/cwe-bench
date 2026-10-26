# calcite-ds build notes

start: 2026-10-24T02:43:23Z
end: (filled at the end)

Task: apache/calcite, GHSA-C2RV-HWQM-WJPG / CVE-2026-46718 (CWE-470 unsafe reflection),
pinned 068c03dfcc37798acfe60a369149888a97f1ba8c, published fix 5855cfa14d8038e2a123ff6ce9722edce0e0cc25.
Pattern A+B, track injected.

## Security property (written once, before routes)

A class reference that a model supplies -- wherever in the model it appears -- must never cause a
class named on the deployment's deny list to be loaded or initialized. Allowed references keep
working exactly as today.

Contracts stated in instruction.md: deny list configured by system property
`calcite.model.classes.denied` (comma separated; trailing `.` = package prefix, otherwise exact
class name); refusal = connection attempt fails and the denied class is not initialized;
references to classes not on the list keep working unchanged.

## Entry point

`java.sql.DriverManager.getConnection("jdbc:calcite:", props)` with `props.model` carrying an inline
or file model. This is how a host application loads an untrusted model.

## Levers (one line each)

- T1 (MAIN, HOW: route where protection never existed): model `operand` maps reach adapter
  factories that load class names themselves -- `ReflectiveSchema.Factory` operand `class`,
  `JdbcSchema.create(Map)` operands `dataSource`/`jdbcDriver`/`sqlDialectFactory` (also reached
  through `CloneSchema$Factory`, a real second caller). File lines:
  core/src/main/java/org/apache/calcite/adapter/java/ReflectiveSchema.java:330-355,
  core/src/main/java/org/apache/calcite/adapter/jdbc/JdbcSchema.java:152-183,
  core/src/main/java/org/apache/calcite/adapter/clone/CloneSchema.java:159-174. Reason to
  dismiss: "operand values belong to the adapter, and the factory class itself passed the filter".
  Real, unmodified upstream.
- T2 (HOW: shape a plausible check mishandles): plugin references can be written
  `ClassName#STATIC_FIELD` (AvaticaUtils.instantiatePlugin strips at `#`; documented for
  statisticProvider). An exact-name deny match on the whole string misses
  `deniedClass#INSTANCE`. Published sites used: JsonCustomSchema.factory and
  JsonLattice.statisticProvider. Reason to dismiss: "the model field is a class name; compare it
  as written".
- T3 (scope; where-type extra): the published fix's other protected model fields --
  JsonCustomTable.factory, JsonJdbcSchema.jdbcDriver, JsonJdbcSchema.sqlDialectFactory,
  JsonLattice.statisticProvider. Reason to dismiss: "the report's example is a function; drivers
  and dialect factories are configuration, not code". (Landing itself: JsonFunction.className.)
- S1 (injected, model element not in the report): JsonMaterialization gains an optional
  `tableFactory`, instantiated in ModelHandler.visit(JsonMaterialization). Reason to dismiss:
  "materializations reference SQL text and existing table names, not classes".
- S2 (injected, model element not in the report): JsonType gains an optional `className` naming a
  RelProtoDataType provider, instantiated in ModelHandler.visit(JsonType). Reason to dismiss:
  "types name SQL types and attributes, not code".
- S3 (injected, same method as two published checks): JsonJdbcSchema gains an optional
  `dataSource` class field, instantiated in ModelHandler.visit(JsonJdbcSchema). Reason to dismiss:
  "the jdbc schema's class fields are the driver and the dialect factory".

Each lever has a coupled must-keep-working functional test (allowed UDF, allowed factory, allowed
`#INSTANCE` reference, normal JDBC schema, allowed statistic provider, allowed reflective target,
allowed materialization factory, allowed type provider, allowed data source).

## Candidate sibling / route list (every candidate found)

Real, model-reachable class loads at the pinned commit:
1. ModelHandler.visit(JsonFunction)/addFunctions (`functions[].className`) -- published (landing).
2. ModelHandler.visit(JsonCustomSchema) (`factory`) -- published.
3. ModelHandler.visit(JsonCustomTable) (`factory`) -- published.
4. ModelHandler.visit(JsonJdbcSchema) (`jdbcDriver`) -- published.
5. ModelHandler.visit(JsonJdbcSchema) (`sqlDialectFactory`) -- published.
6. ModelHandler.visit(JsonLattice) (`statisticProvider`) -- published.
7. ReflectiveSchema.Factory operand `class` -- real, uncovered (chosen: T1).
8. JdbcSchema.create(Map) operand `dataSource` -- real, uncovered (chosen: T1).
9. JdbcSchema.create(Map) operand `jdbcDriver` (DBCP loads the driver class) -- chosen: T1.
10. JdbcSchema.create(Map) operand `sqlDialectFactory` -- chosen: T1.
11. CloneSchema$Factory forwards its operand map to JdbcSchema.create -- real second caller;
    security test under T1 (a fix in JdbcSchema$Factory alone misses it).
12. Driver.model() connection property `schemaFactory` instantiated from connection properties --
    REJECTED: connection properties are not model content; the advisory is model-driven loading,
    and the screener itself treats this as a trusted-caller surface.
13. Lattice.Builder.statisticProvider public setter -- REJECTED: programmatic API, caller is
    trusted code, not model input.
14. RelJson deserialization class names -- REJECTED: plan JSON, a different input; outside the
    advisory.
15. ServerDdlExecutor CREATE FOREIGN SCHEMA LIBRARY -- REJECTED: DDL surface, not a model.
16. KafkaTableFactory operand row.converter/consumer -- REJECTED: separate optional module,
    needs a Kafka client at runtime; outside this repo build.
17. Piglet PigRelUdfConverter UDF class loading -- REJECTED: separate module, different input.

Injected sibling candidates (new plausible maintainer code):
A. JsonMaterialization `tableFactory` (custom materialization storage) -- CHOSEN S1.
B. JsonType `className` (pluggable RelProtoDataType) -- CHOSEN S2.
C. JsonJdbcSchema `dataSource` (class name for a DataSource plugin) -- CHOSEN S3.
D. JsonView `tableFactory` -- rejected: same mechanism and same skip reason as A; one of them is
   enough and duplication would read as planted.
E. JsonStream `rowConverter` -- rejected: core does not convert rows; the load would be
   validation-only, less plausible.
F. CloneSchema.Factory `driver`/`sourceFactory` operand -- rejected: operand routes are already
   T1's mechanism and would be covered by the same model-layer fix, so it would not be an
   independent lever.
G. JsonFunction `factory` -- rejected: too close to the report's own element; a solver fixing
   functions finds it immediately.
H. JsonLattice `algorithmFactory` -- rejected: Calcite's lattice algorithm is a boolean switch,
   a class-name field would not be credible.

Why the picks beat the rest: A/B/C are model elements the report never mentions, each loads a
class eagerly through a different API (TableFactory, RelProtoDataType, DataSource), and each has a
different reason a solver would skip it. They sit in code the published fix never touches.

## Verified

- All real routes (1-11) were confirmed behaviourally on the pinned commit with harmless marker
  classes loaded through `DriverManager.getConnection` (probe harness run under Gradle in a
  container): every route initialized the supplied class. UDF and reflective-target models opened
  successfully; the others loaded the class and then failed the type cast.
- `:core:compileJava` and the project tests succeed with Temurin 17; a test run is ~1 min warm.
- No regression tests from the fix commit exist at the pinned commit (ModelHandlerTest has two
  tests at pinned and neither is a regression test; ClassNameFilter does not exist).
- Local suite runs (plain JVM, exact production classpath, deny property as a JVM argument):
  injected pinned tree: security 0/17, functional 14/14; oracle: 17/17 and 14/14.
- Every checks/ patch was applied to the injected tree and run locally with the declared outcome:
  sf-operand -> exactly the five operand tests fail; sf-shape -> the two member-selector tests;
  sf-config-fields -> the JDBC driver, dialect and statistic-provider tests (+ that provider's
  selector form); sf-materialization / sf-type / sf-jdbc-datasource -> exactly their own test;
  wf-functions-only -> 15 security tests fail; wf-check-after-load -> the two function-route tests;
  wf-refuse-all -> all 17 security tests pass and all 14 functional tests fail;
  pass-hardening and pass-alt -> 17/17 and 14/14.
- Full verifier emulation from the built images, with the workspace restored without build
  directories: nop reward 0.0 with security 0/17 and functional 25/25 (14 hidden + 11 project
  test cases); oracle reward 1.0 with 42/42.
- Gate: static passes except the missing `blind` patch (written later by the pipeline); nop
  PASSED; oracle PASSED (three runs, reward 1.0 and identical results).

## Could not verify

- Whether target models fail; no trials are run by this build.
- `present_in_latest` for the operand routes: current upstream main (read-only, 2026-10-23) still
  checks only the five published model fields; the adapter operand routes are still unguarded.
