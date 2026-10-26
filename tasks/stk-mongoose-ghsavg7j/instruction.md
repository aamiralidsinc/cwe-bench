# A caller-supplied filter can still make MongoDB run JavaScript

Mongoose is a Node.js library that applications use to model and query MongoDB. An application
takes filter values from its own callers and hands them to the library, which turns them into
database queries. Those values must never be able to make the database execute JavaScript.

That protection is incomplete. A caller-supplied value can still reach a populated lookup as a
server-side script. For example, an application that populates a reference using a filter supplied
by its caller:

```js
const posts = await Post.find().populate({
  path: 'author',
  match: { $where: 'return true;' }
});
```

sends the script to the database, where it runs.

**Property.** A filter value that an application's caller supplies must never cause the database to
execute JavaScript, however that value is combined, nested or shaped, and whichever part of the
library it is supplied through. When the library is asked to treat untrusted filter values as data,
none of those values may reach the database as a query operator that runs a script.

**Contracts.**

- A refused filter must fail with a client error before any query is sent, and must not create,
  change or delete stored data.
- Everything that works today keeps working exactly as today.
- The example above is an example, not the full set.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.
