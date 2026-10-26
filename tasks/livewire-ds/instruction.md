# A page link can change what a Livewire page does

Livewire is a Laravel framework for building dynamic interfaces. A component's data lives in
the page. After an interaction the browser posts to the server and the server answers with the
component's current data and the instructions the page should carry out. A component property
can also be bound to the page's address, so the address is read when the page loads and kept up
to date as the property changes.

A visitor who follows a link whose address stores a value for a bound property can make the page
carry out an instruction the server never sent. Opening a link such as

```
/orders?filters[__proto__][html]=<div class="probe">x</div>
```

renders that markup in the page although the response contains no instruction to render it.

## What must hold

No value that arrives in a page's address may be written onto a built-in object's prototype or
replace the prototype of an object the page builds. A page must only act on component data and
instructions that the server actually included in the response it is handling: an address value
must never make the page carry out anything the server did not send.

This holds for every part of the address and for every bound property, however the value is
written. It is an invariant, not a list of cases. The link above is one example.

## Behaviour that must not change

- Everything that works today keeps working exactly as today. A property bound to the address
  still reads its value on load and writes its changes back; nested object and list values keep
  their shape and still round-trip through the address; ordinary scalar values, empty values and
  names that merely resemble a built-in object's name still bind.
- Every instruction the server does send is still applied exactly as today, and an instruction
  that is absent or empty is still skipped.
- When a page declines to use an address value, skipping that value is fine; the rest of the
  page keeps working and the page must not fail to load or lose its other bindings.
- A legitimate bound value of any ordinary size and shape, next to the example above, still
  binds.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. There is no network access.
Do not look up the upstream fix or any published version of it. Do not special-case the example
above.
