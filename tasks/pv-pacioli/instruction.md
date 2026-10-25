# Pacioli Guard — consent enforcement

Pacioli Guard is a Frappe/ERPNext app installed on an accounting site. When a credential's grant
requires consent, the app refuses a lifecycle act on a bookkeeping document — posting it, reversing
it, or erasing it — unless the request presents a single-use consent marker that a human minted, out
of band, for that exact document and that exact act, by a hand other than the one that spends it.
Markers travel in the `X-Pacioli-Consent` request header. The refusal is raised inside the document
lifecycle, so the gate covers every way a document is posted, including the paths an API-key check
never sees.

## What we observed

A credential held one marker, minted to post `ACC-SINV-0001`, and sent
`POST /api/resource/Sales Invoice/ACC-SINV-0001` carrying it, with a body that also named an
existing asset depreciation schedule. The invoice posted. The schedule was reversed in the same
request. No human had authorised reversing that schedule and no marker for it was ever minted, yet
it is now reversed and the ledger has moved.

## The property

**Consent is per act and per document.** A consent marker authorises exactly one act on exactly one
document, is minted by a hand other than the one that spends it, and is spent once.

An act may proceed without its own marker only when it is a consequence of an act that was already
authorised, and then only with that act's own authority: a document the authorised act itself
creates may be brought into existence as part of it, and a reversal may cascade into further
reversals of documents that already exist.

Authority never crosses to a different act; never carries to a document the authorised act did not
create; and never survives into an act other than the one that carried it. That holds however deeply
an act is nested and whatever a request body names.

## Contracts

- A refused act raises the site's permission error (`frappe.PermissionError`) and leaves both the
  document and every marker untouched.
- One request may perform more than one gated act and may present more than one marker in the
  consent header, separated by whitespace or commas. Every marker presented is still bound to one
  document and one act and is spent once; an empty entry is never a marker. Carrying several markers
  is legitimate — each act still has to find the one minted for it.
- Everything that works today keeps working exactly as today: an act with its own marker; the
  framework's own consequences of an authorised act, including a ledger document the act creates
  while posting and an undo that cascades into further undos; and every credential whose grant does
  not require consent.

The request above is one example, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.
