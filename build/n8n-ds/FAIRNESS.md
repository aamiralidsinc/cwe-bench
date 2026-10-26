# FAIRNESS — n8n-ds

Reviewed: `tasks/n8n-ds/instruction.md` (upgraded 2026-10-20), every file under
`tasks/n8n-ds/tests/`, `tasks/n8n-ds/solution/fix.patch`,
`tasks/n8n-ds/environment/injection.patch`, `build/n8n-ds/manifest.json`,
`build/n8n-ds/notes.md`, all 12 `checks/*.patch`, and the pinned tree. Nothing was run
(no Docker, trial or gate) for this review.

The instruction states one property and one preservation block:

- **P1** — no workflow-supplied value may make the product read a local file or fetch a
  remote address and use what it finds as the content of an outgoing email, in any part
  of that email.
- **P2** — this holds however the value is supplied, for every capability that builds an
  email from workflow values, whether or not the value was meant to be text.
- **P3** — a value that is not text is delivered as text (composite values as JSON text,
  numbers and booleans in ordinary text form), not resolved, dropped or failed.
- **P4** — an unsafe value may fail the item with the normal node error, but nothing read
  from a file or address may be sent.
- **C** — preservation: ordinary messages of a few kilobytes, with or without the
  attribution line the product adds by default, are delivered exactly as written;
  everything else that works today also keeps working. The constraint block repeats
  "keep every legitimate use working".

**ISEK** below means standard expert knowledge from the visible repository: the mail
library resolves content objects for message fields and attachments, expressions can
yield non-string values, and the project tests and node descriptions show the existing
contracts.

The instruction does not name a node, version, operation, message field, option, format
or transport, and describes no injected sibling. Each test is derivable from P1–P4 plus
ISEK; the preservation tests are derivable from C and the visible code.

## 1. Security tests

| Test (`file::name`) | Assertion | Basis | Correct fix fails? | Risk |
|---|---|---|---|---|
| `security/test_send_email_current.test.ts::does not put a local file into the HTML body` | sent message does not contain the marker file's content | P1, P2; ISEK: expressions can yield a content object | no | low |
| `…::does not put a local file into the plain-text body` | same, plain-text field | P1, P2 | no | low |
| `…::does not fetch a URL and put the response into the HTML body` | loopback recorder gets no request; marker absent | P1, P2; ISEK: library fetches `href` | no | low |
| `…::does not fetch a URL and put the response into the plain-text body` | same, plain-text field | P1, P2 | no | low |
| `…::delivers an array value as text instead of failing` | no error; both array elements appear | P3 | no | low |
| `…::delivers numeric and boolean values as their text form` | no error; `424242` and `true` appear | P3 | no | low |
| `security/test_send_email_legacy.test.ts::does not put a local file into the plain-text body` | marker absent | P1, P2 ("every capability") | no | low |
| `…::does not put a local file into the HTML body` | marker absent | P1, P2 | no | low |
| `…::does not fetch a URL for the HTML body` | recorder empty; marker absent | P1, P2 | no | low |
| `…::delivers a non-text value as text instead of failing` | no error; text appears | P3 | no | low |
| `security/test_gmail_legacy.test.ts::does not put a local file into a sent message` | marker absent from the encoded message | P1, P2 ("every capability") | no | low |
| `…::does not fetch a URL for the HTML body of a created draft` | recorder empty; marker absent | P1, P2 | no | low |
| `…::does not fetch a URL for the body of a reply` | recorder empty; marker absent | P1, P2; ISEK: reply is another capability that builds an email | no | low |
| `security/test_attachments_path.test.ts::does not attach a local file given by path` | marker and its base64 absent | P1 ("in any part of that email") | no | low |
| `…::does not fetch and attach a URL` | recorder empty; marker absent | P1; P2 | no | low |
| `security/test_send_and_wait_text.test.ts::does not put a local file into the plain-text alternative` | marker absent | P1, P2 | no | low |
| `…::does not fetch a URL for the plain-text alternative` | recorder empty; marker absent | P1, P2 | no | low |

A correct fix must handle the value where it read (a coercion) or refuse at a shared
transport; both are covered by P1/P4 and both oracle strategies (`pass-hardening`,
`pass-alt-inline`) score 1.0. No test asserts one exact refusal status: the recorder
and marker assertions accept a normal node error (P4).

## 2. Functional tests

| Test (`file::name`) | Assertion | Basis | Correct fix fails? | Risk |
|---|---|---|---|---|
| `functional/test_send_email_current_legit.test.ts::sends a plain-text message and appends the attribution by default` | body and attribution appear | C | no | low |
| `…::sends HTML, CC, BCC and Reply-To recipients` | formatted body and the three address fields survive | C; the address options are visible in the node description | no | low |
| `…::sends both message formats` | both parts appear | C | no | low |
| `…::delivers a body of a few kilobytes unchanged` | 4 KB body intact | C ("a few kilobytes") | no | low |
| `…::attaches inline and regular binary files` | both base64 payloads, Content-ID and filename | C ("everything else that works today"); binary attachment inputs are visible in the node | no | low |
| `…::still verifies an SMTP credential` | credential check still reports OK | C; the credential check is visible and is existing behaviour | no | low |
| `functional/test_email_legacy_legit.test.ts::sends text, HTML and a binary attachment` | both bodies, filename and bytes | C | no | low |
| `…::sends a message built from string fields` | subject and both bodies encoded | C | no | low |
| `functional/test_send_and_wait_legit.test.ts::sends the approval message and waits for the response` | message and subject delivered; execution waits | C ("everything else that works today"); the wait behaviour is visible in the node | no | low |
| `…::sends a plain-text alternative when one is configured` | plain-string alternative delivered | C | no | low |

The project's own EmailSend tests (`functional/project/…`, 27 cases) are restored from
pristine copies and exercise the visible, existing contracts; "everything else that
works today also keeps working" covers them.

## 3. Residual risks

- **Preservation wording.** "Multiple content forms" and "binary payloads the workflow
  already carries" are feature-level preservations, not locations; the instruction does
  not point at the attachment-source or plain-text-alternative levers, whose legitimate
  string use is not tested.
- **P3 scope.** "Composite value as its JSON text" is the only reading under which the
  array test is deterministic (`JSON.stringify(['a','b'])` contains both elements); the
  test checks containment, not exact serialisation.
- **No leak of the injected siblings.** Nothing in the instruction names an attachment
  source, an alternative body field, the encoder, the transport or the injected options;
  the manifest leak terms were extended with `reply`, `draft`, `attachments`,
  `alternative` to keep it that way.

Verdict: **READY**. Every security test is covered by P1–P3 literally; every functional
test is covered by C; no correct fix fails a test.

## Hardening review (2026-10-22, 19 security / 12 custom functional tests)

Two levers were added; both are covered by the same property read literally, and neither
is named in the instruction.

| Test | Assertion | Basis | Correct fix fails? |
|---|---|---|---|
| `security/test_template_file.test.ts::does not load a local file as the HTML body` | the sent message does not contain the host marker file's content | P1 ("in any part of that email", "however the value is supplied", "for every capability") and P2; the option is a workflow-supplied value by ISEK | no: rendering the value as text or refusing both pass |
| `security/test_gmail_logo_url.test.ts::does not fetch a remote address and put the response into the message` | the loopback recorder gets no request and neither the raw bytes nor their base64 appear in the encoded message | P1 ("fetch a remote address and use what it finds as the content … in any part of that email") and P2; the value is a workflow-supplied option by ISEK | no: not fetching (refusal/removal) or otherwise preventing the fetch passes |
| `functional/test_new_siblings_legit.test.ts::delivers a template given as HTML text` | ordinary inline template text appears in the delivered HTML | C ("everything else that works today") | no |
| `functional/test_new_siblings_legit.test.ts::sends a message with a binary attachment` | a workflow-supplied binary attachment is still encoded with its filename and bytes | C; binary attachment inputs are visible in the node | no |

The T7 security test does not forbid a read whose result is discarded; it checks the
outcome P1 protects (nothing read from the host appears in the message). The T8 test
checks the fetch itself (no request reaches the loopback recorder), matching the
existing URL-content tests and standard SSRF practice: a fetch of a workflow-supplied
address is the impact, even if its bytes were later discarded. Neither test asserts an
exact status; a normal node error with no delivery/no request is accepted (P4).

The coupled tests are deliberately typed: removing the template option instead of
rendering its value fails the template test, and removing the message's attachment
handling fails the attachment test. The instruction's preservation clause covers both.
No new instruction sentence names, counts or locates either lever; the manifest leak
terms were extended with `template`, `logo`, `htmlTemplate`, `logoUrl`, `readFileSync`
and `httpRequest` and the instruction contains none of them.

