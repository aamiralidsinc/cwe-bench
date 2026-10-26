# MongoDB PHP library: database and collection names

## The system

This project is a PHP client library for MongoDB. An application creates a client, obtains a
database handle or a collection handle from it, and reads and writes documents through that
handle. A database and a collection are identified by names supplied by the application — often
values that originate from a user (request parameters, tenant labels, configuration entries)
rather than from the library itself. Those names are what tells every later operation where its
data lives.

## Observed impact

An application takes a database label from a user and opens that database, then writes a document
into its `records` collection: the user supplies `prod.audit`, the application calls

```php
$client->getDatabase('prod.audit')->getCollection('records')->insertOne(['marker' => 'writer']);
```

and the library accepts it without complaint. The document does not land in the database the
application asked for: it is written to the database `prod`, into a collection named
`audit.records`. A name supplied by the caller silently changed which database and collection
the operation addressed.

## What must hold (invariant)

A database and a collection are addressed by exactly the names the caller supplied. A supplied
name is one opaque identifier: neither the library nor the driver/server may split it, truncate
it, or otherwise reinterpret it, and no supplied name may make an operation read or write a
different database or collection than the one it names. This holds no matter how the name
reaches the operation and no matter what bytes the name contains.

## Contracts the fix must honour

- **Refusal.** A name that cannot be used verbatim must be refused with the library's
  invalid-argument error at the point the name is accepted, before any command is sent. Nothing
  may be read, written, created or queued as a side effect of the refused call.
- **Preservation.** Everything that works today keeps working exactly as today for valid names.
  In particular, a collection name may contain periods: in a `database.collection` namespace the
  database part is the text before the first period and the collection part is everything after
  it, and such a name must keep resolving to exactly that collection. An empty database or
  collection name remains invalid, as today.
- **Ordinary names.** A magnitude check on the other side: `prod`, `app_2026` and `tenant-7` are
  ordinary database names, and `records`, `fs.files` and `tenant7.orders` are ordinary
  collection names; all of them must keep working.

The examples above are examples, not the complete set of names, forms or call paths the fix must
handle.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep every legitimate use working.
- Do not look up the upstream advisory or fix; solve it from the code.
- Do not special-case the example inputs.
