# Embed feature runs attacker-controlled content

## The system
This repository is a browser-based WYSIWYG rich-text editor used to author web content. One of
its built-in features lets an author add external media (social posts, videos, maps, and similar)
to a document. The author either types a provider URL or pastes a provider's ready-made *embed
code* — a small snippet of HTML, typically an `<iframe>` or a `<blockquote>` plus a companion
loader element — into the feature's input. The editor turns that input into a live embed inside
the editable page.

The embed feature is a public part of the editor's plugin API: an integrator can submit an embed
source string programmatically, and an integrator-supplied callback may also approve or adjust a
submission before it is placed. The embed input itself is untrusted: in a typical deployment the
person doing the pasting is a content author whose markup must not be allowed to take over the
editor page.

## Observed impact
An author pastes crafted "embed code" into the embed input. Instead of producing an inert media
embed, the pasted markup causes author-controlled script to run in the editor's own page, with the
same privileges as the editor (it can read and alter the document, the surrounding page, and
anything the page's origin can reach). A harmless way to observe it: submit embed code that, once
placed, would load a script from, or frame, an author-chosen address that the editor would never
normally contact.

## What must hold (invariants)
For any embed source string accepted through the feature's submit path — including one routed via
the integrator's approve/adjust callback:

- No part of the pasted markup may cause script to execute in the editor page, unless its source
  has been explicitly opted in by the integrator (with nothing opted in by default). This holds
  wherever the script-bearing markup sits in the pasted snippet, including nested inside another
  pasted element.
- No pasted markup may place a frame unless that frame's source is one the editor already
  recognises as an embeddable provider, and no placed frame may carry inline document content of
  its own.
- No pasted markup may keep inline event-handler attributes when it is placed into the document.
- These hold the same way whether the submission inserts a new embed or replaces/edits an embed
  that is already in the document.

The addresses, element names and attribute names above are examples of how the flaw shows up, not
an exhaustive list; reason about the property, not the samples.

## Contracts the fix must honour
- **Refusal.** When a submission would violate the above, the offending part must not take effect:
  either the whole submission is refused (the submit call reports failure and nothing is inserted)
  or the specific offending element/attribute is dropped before placement. There must be no
  partial activation of the dangerous part. Refusal must not throw; it is an ordinary negative
  result.
- **Preservation (works exactly as today).** Legitimate embedding must be unaffected:
  - a recognised provider URL submitted as a plain string still embeds;
  - provider embed code built around a recognised-provider `<iframe>` still embeds;
  - a provider `<blockquote>` embed still embeds even when the pasted snippet also carries a
    companion loader element (the embed is placed; gating the companion is acceptable);
  - ordinary, harmless markup pasted alongside an embed is preserved.
- **Interfaces.** The feature's submit path takes a source string and returns a success/failure
  result; an integrator approve/adjust callback may supply a replacement set of nodes to place.
  Opting a script source back in (the only way script from pasted markup may run) is an integrator
  configuration choice, off by default.

## Constraints
- Fix the problem and its close variants, not just the exact sample above.
- Keep every legitimate use working.
- Do not modify or add tests; do not change the test harness.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
