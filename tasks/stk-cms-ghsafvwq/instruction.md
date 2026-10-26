# Craft CMS hands the browser an unsafe destination it was asked to return to

## System

This project is a content management system with a browser-based control panel.
Requests regularly carry an address that the product uses later to send the
browser somewhere. The product stores some of these addresses and returns others
to the browser, and it processes them before doing so.

## Observed impact

A visitor follows a control-panel link that asks to be returned to a
`javascript:` address and then signs in. The product stores that address as the
destination to return to and, after authentication, sends the browser there, so
the attacker's script runs with the control panel's origin. The same kind of
value reaches the browser through other places where the product uses a
requested address as a destination.

## Security property that must hold

Whatever the product accepts as a destination, whoever supplies it and however
it arrives, the product must never store, return or send the browser to a value
that can execute code: neither a navigable address whose scheme a browser runs
rather than fetches, nor markup that would be written into stored state. This
holds for the value as the product finally produces it, including whenever the
product's own handling changes the value on the way. A request whose destination is of that kind is refused with a client
error, or the product substitutes a safe destination; either way the unsafe value
never takes effect.

## Contracts the fix must honor

- **Refusal form.** A refused request returns a client error (any 4xx) and has no
  effect; a server error is not a refusal.
- **Preservation.** Everything that works today keeps working exactly as today.
  Absolute http and https addresses, upper- and lower-case schemes, root-relative
  addresses, protocol-relative addresses, bare control-panel paths, and addresses
  with query strings or fragments all keep being stored, returned and followed
  unchanged.
- **Examples are examples.** The address above is one illustration, not the full
  set; the property covers every place where a requested address becomes a
  destination.

Fix the problem and its close variants. Keep legitimate use working. Do not look
up the upstream fix, and do not special-case the example.
