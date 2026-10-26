# Grid column names are executed as SQL

The Studio backend powers Pimcore's data grids. A collection request asks for a page of items and
may also carry grid filters: each filter names a column, says what kind of filter it is and gives a
value. The backend turns those filters into the condition of the database query that lists the
page.

**Impact.** A user who is allowed to open a grid can send a filter whose column name is not a real
column. The backend pastes that name straight into the query, so the request runs SQL the user
chose instead of merely selecting rows.

**Trigger (one example, not the full set).** A signed-in user lists a collection and sends one
filter whose column name is

```
creationDate` OR (SELECT 1) OR `x
```

with an ordinary filter value. The name reaches the database as statement text, so the query
evaluates an expression no column filter should have been able to add.

**The rule.** A column or field name supplied by a request is data. Whatever characters it
contains, whichever request field, filter kind or collection it arrives through, the name must be
treated as exactly one column identifier - or as one table-qualified identifier written
`alias.column`. It must never become part of the SQL text: it may not add, remove or change
clauses, operators, comments, literals or parameter placeholders, and it may not decide how a
value is bound.

**Contracts.**
- If a supplied name cannot be honoured, refusing the request with a client error is acceptable,
  and so is treating the name as one that matches nothing. In neither case may any part of it act
  as SQL, and no data may be read or changed because of it.
- Everything that works today keeps working exactly as today: plain names, mixed-case names,
  table-qualified names written `alias.column`, every existing filter kind and operator, the values
  those filters bind, and the result of a legitimate filter on a legitimate column.
- Filters stay usable through the same request shape and fields as today; do not remove a filter
  kind, a column or a collection to make the problem go away.

The example above is an example: a correct fix closes the whole class of input on every collection
and every filter kind, not only the one shown.

**Constraints.**
- Fix the reported problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or the advisory.
- Do not special-case the example input.
