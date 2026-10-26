# Removed subtrees stay active when a sanitizer runs in place

This project is a DOM-only HTML sanitizer. Besides cleaning a markup string and
returning it, it can sanitize a live DOM node in place: the cell receives the
same node back, cleaned, which is what applications do when they build markup
with DOM APIs and must have it sanitized synchronously.

## Observed impact

An application sanitizes a live element in place while an application hook it
registered removes an element the application's policy has decided to drop.
When the attacker-influenced markup puts a resource-loading element carrying an
inline event handler (for example an image with an error handler) inside that
element, the call returns and the visible tree looks clean, yet the removed
element and its descendants are still attached to the page and their queued
events still fire. The handler therefore executes in the victim's origin: script
execution in the victim's session, even though nothing executable appears in the
returned tree.

## Required property

Everything the library detaches from the caller's live tree during a call must
be inert before that call finishes. Concretely: once a call finishes, no node
it detached from the caller's live tree during that call may still carry an
attribute that can execute script.

The example above is one instance, not the whole set of cases the property
covers.

## Contracts

- A call that must refuse may throw. A throw is an acceptable outcome, but it is
  not an excuse to leave anything active behind.
- Everything that works today keeps working.
- Fix the reported problem and its close variants in this repository. Do not
  look up the upstream fix, and do not special-case the example.
