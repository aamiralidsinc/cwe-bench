# ruby-saml-inv: fairness audit of the rewritten instruction

Tests are unchanged from `tasks/ruby-saml/tests/`. The library's default maximum message
size is 250,000 bytes; the tests use default settings throughout.

## Per-test justification

| test (file::name) | what it asserts | sentence of the new instruction that makes it fair | risk |
|---|---|---|---|
| security/group.rb::wrapping: duplicate signed identifier on a second assertion is rejected | Signed fixture plus a copy of the signed assertion (same ID, NameID changed to attacker@evil.example) appended after it; `Response.new(b64).document.validate_document(fp, true)` must not return true (false or a raise both count) | The trigger example ("add, next to the signed assertion, a copy of it that carries the same identifier but names `attacker@evil.example`... still reports the response as validly signed") and "A document in which the signed identifier could refer to more than one element must never be reported as validly signed by any of the library's signature checks." | low |
| security/group.rb::wrapping: duplicate signed identifier on an injected element is rejected | A foreign-namespace `<Decoy ID="<signed id>">` element (not an assertion) appended to the response; same signature check must not return true | "A document in which the signed identifier could refer to more than one element must never be reported as validly signed by any of the library's signature checks." The wording covers any element, not only assertions. Standard expert knowledge: unique-ID enforcement is the textbook signature-wrapping defence. | low |
| security/group.rb::resource: decompression bomb via a redirect-binding message is rejected | ~0.8 KB deflated+base64 blob inflating to 600 KB, passed to `SloLogoutrequest.new(blob)` (default settings), must raise (any error except NoMemoryError/signals/exit), and no REXML/Nokogiri parse of a source of 600 KB or more may happen | "No message, however it is encoded or compressed, may lead the library to parse ... content larger than that maximum. A message ... that grows past it when decoded, is refused before it is parsed." plus "an error is raised when the message is handed to the library" and "at its current default" (600 KB > 250 KB default) | low |
| security/group.rb::resource: decompression bomb via a response message is rejected | Same bomb via `Response.new(blob, settings: Settings.new)`: must raise and not parse the expanded document | Same sentences, plus "applies to every kind of message, whatever form it arrives in." | low |
| security/group.rb::resource: oversized message is rejected before expensive processing | ~8.4 MB well-formed plain (non-base64) XML passed to `SloLogoutrequest.new`: must raise on both of 2 calls, must not be parsed, and the faster call must take < 0.2x one whitespace-stripping `gsub` pass over the same input | "A message that is over the maximum as received ... is refused before it is parsed." "Refusing a message that is over the maximum as received costs almost nothing: it happens before the library reads through the message's contents." "whatever form the message arrives in" covers plain XML. Raise form from the refusal bullet. | medium (see below) |
| functional/group.rb::a legitimately signed assertion verifies | `validate_document(fp, true) == true` on the repo's signed-assertion fixture | "Correctly signed responses still verify" | low |
| functional/group.rb::a legitimately signed message-and-assertion response verifies | `validate_document(fp, true) == true` on the fixture with both message and assertion signed | "Correctly signed responses still verify" (standard expert knowledge: a response signed at both levels is a normal, valid SAML form) | low |
| functional/group.rb::full relying-party validation accepts a valid signed response | `Response#is_valid?` is true with `idp_cert` set and conditions/destination/audience/time checks skipped | "Correctly signed responses still verify, pass full response validation" | low |
| functional/group.rb::the signed response exposes the expected NameID | `Response#name_id == 'someone@example.org'` | "expose the user's identity and attributes as today" | low |
| functional/group.rb::a normal compressed redirect-binding message decodes | Small deflated+base64 LogoutRequest via `SloLogoutrequest.new`; `name_id == 'user@example.com'` | "Normally sized messages, in every form the library accepts today (compressed ones included), are decoded and processed exactly as today." | low |
| functional/group.rb::a normal base64 message is processed | Small base64 (uncompressed) LogoutResponse via `Logoutresponse.new`; `in_response_to == '_abc'` | Same sentence ("every form the library accepts today") | low |

## Medium risk: the oversized-message timing test

The test demands the refusal be cheaper than 0.2x one regex pass over the input. The
instruction states this as "costs almost nothing: it happens before the library reads
through the message's contents". A size check of the received bytes before any scan,
decode or parse passes by a wide margin (reference 0.0005 s vs ~1.0 s pass). A fix that
first scans the message (e.g. to detect its encoding) and then refuses it fails, and the
instruction now rules that out in words ("before the library reads through"). It no longer
says "regardless of how it is encoded" for this case specifically; "whatever form the
message arrives in" carries that. I judge this the minimum wording that keeps the test fair
without naming the scan.

## Contracts kept (in neutral words)

- Refusal form: an error is raised when the message is handed to the library, no object
  returned (the bomb and oversized tests require a raise from the constructor).
- The limit is the library's existing configurable maximum at its current default (tests use
  default settings; 600 KB and 8.4 MB both exceed it).
- Over-limit content must not be parsed (parse spy in all three resource tests).
- Signature verdict must fail at the library's own signature checks, not only in a later
  validation step ("by any of the library's signature checks").
- Preservation: signed responses verify, full validation passes, identity readable; normal
  messages in every accepted form decode exactly as today.

## Details removed from the old instruction

- Class names `OneLogin::RubySaml::Response`, `OneLogin::RubySaml::SloLogoutrequest`,
  `OneLogin::RubySaml::Logoutresponse`, and "the document signature check they perform".
- The phrase "Please investigate and fix them" with three titled per-flaw sections
  ("Forged content accepted as signed", "Tiny message, huge expansion", "Oversized input
  processed before it is rejected"), which revealed the count of flaws.
- "if the response is made to contain more than one element bearing the identifier that
  the signature refers to — the genuinely signed element plus an additional element the
  attacker added" (mechanism stated as such; now one product-level example plus an
  invariant).
- "The signature verification step must refuse to treat such an ambiguous document as
  validly signed" (location: the verification step).
- "SAML messages may arrive compressed. A very small compressed, encoded message can be
  crafted so that it expands into an enormous document" and "The library decodes and keeps
  the whole expanded result" (mechanism of the decompression flaw).
- "Decoding must be bounded so that a message whose decoded size exceeds the configured
  limit is rejected rather than fully expanded" (fix location and approach: bound the
  decoder).
- "A greatly oversized message is scanned and parsed before any size limit is applied"
  (root cause: ordering of the scan versus the size guard).
- "regardless of how it is encoded" / "whatever their encoding" attached to the oversized
  case (hint that the size guard is skipped for one encoding).
- "Oversized messages must be refused up front, before that expensive work" (restated as a
  cost property without naming the scan).
- Nothing about the dropped parser-differential issue was in the old text; nothing added.

## Added (no new requirement)

- `/app` location and a standard constraints block (do not modify/add tests, do not look up
  the upstream fix, do not special-case the example, do not disable the feature). The
  "disable" clause mirrors the functional tests; no new test-checked requirement.
