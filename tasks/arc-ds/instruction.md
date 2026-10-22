# Arc: local data and network egress

Arc is a time-series database server. It stores the data it ingests in its own
managed storage area and answers client requests against that data.

## Reported problem

A caller was able to make Arc open and return a local file that lies outside
Arc's managed storage area, and was able to make Arc contact a network address
chosen by the caller.

## Required properties

No request may make the server open, read, list, return, copy or transmit any
local file outside its managed storage area, or any value derived from such a
file. No request may make the server contact a network address supplied by the
caller. This holds for every request, every caller-supplied value, every token
(including one with no permissions), and every connection the server uses to
run work. Nothing a caller sends may disable or relax this protection.

A request that attempts either behaviour must be refused: the response must
carry neither the file's bytes nor a value derived from its contents, and the
request must not create, modify or delete anything. Refusal is an error
response; the exact status and message are not fixed.

## What must keep working

Every existing feature must keep working exactly as today. In particular:

- reading stored data, including with caller-supplied conditions, still
  returns the matching rows;
- when a caller asks for timing information, it is still returned with the
  result;
- a caller-requested change to stored data still affects exactly the rows
  that match the caller's condition;
- stored, reusable query definitions still run and return their results;
- a feature that contacts an address chosen by the operator still uses that
  address.

These examples are examples, not the full set. Fix the reported problem and
its close variants; do not special-case the example. Do not look up the
upstream fix. There is no network access.
