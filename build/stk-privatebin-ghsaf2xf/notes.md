# stk-privatebin-ghsaf2xf — build notes

Start (UTC): 2026-10-26T12:16:07Z
End (UTC): (filled at the end of this session)

Repo: privatebin/privatebin. Pinned: 6c1f0dde0c4cccd8e132d27842a3cba556648d02 (first parent of the
earlier fix). Published fixes: 2a4d572c1e9e (A, GHSA-cqcc-mm6x-vmvw / CVE-2022-24833) and
e0dd4c025c19 (B, GHSA-f2xf-7x3g-4272; content commit 7f1f4085). Pattern H3b2, stack A+B.

## Levers (one line each)

- C1 / T1 (deepseek, advisory route): the attachment's declared media type is handed to the browser
  as the download link's blob type and as the preview type (js/privatebin.js:2772,2782,2785,2794,2801).
  Dismissal: the link has a download attribute, so a click saves it.
- C1 / T4 (deepseek, published-fix far site): the legacy version-1 display route reaches the same
  attachment setter through a separate decrypt path (js/privatebin.js:5051-5058). Dismissal: both
  format branches end in the same setter.
- C2 / T2 (both, shape): the download name is written only when the decrypted value is not
  `undefined`; a present-but-null `attachment_name` passes the key gate and jQuery's null value
  removes the attribute (js/privatebin.js:2797-2799, 5046). Dismissal: the v2 gate requires the key.
- C3 / T3 (mimo, uncovered upstream): the editor preview passes the download name where the media
  type belongs (js/privatebin.js:2368-2370), so a name matching `/pdf` builds an embedded document
  for active content (js/privatebin.js:3016-3058). Dismissal: the element's type attribute is
  advisory, so it looks cosmetic.

## Verified on the pinned tree

- Every security case fails on the pinned code for the intended reason and passes on the reference:
  11 security cases, 12 functional cases (local runs, and again inside the gate container).
- The real entry point works: a crafted version-2 (and version-1) ciphertext produced with Node's
  crypto/zlib is decrypted by `PasteDecrypter.run`; the attachment link, the Blob type recorded at
  `URL.createObjectURL`, and the preview element are observed. The editor route is reached through
  `Controller.clonePaste` plus the real preview-tab click.
- T3 is real: with an HTML payload and the name `application/pdf`, the pinned tree builds
  `<embed src="blob:..." type="application/pdf">`; the reference builds no element.
- T2 is real: `attachment_name: null` leaves the anchor without a `download` attribute on pinned;
  the reference writes an empty one.
- The project's own JavaScript suite passes at the pin in the built image (97 passing, mocha 10,
  Node 20, local wasm-fetch stub), including js/test/AttachmentViewer.js; that file also passes on
  the reference.
- Variant runs (local): alt_correct_fix 11/11 + 12/12; hardening 11/11 + 12/12;
  miss_media_type leaves the six C1 cases failing, functional all pass; miss_download_attr leaves
  only the two T2 cases failing; miss_preview_dispatch leaves only the two T3 cases failing;
  functional_overbroad passes security and fails seven functional cases; upstream_first_fix (A
  alone) leaves ten security cases failing, functional all pass; upstream_fix (A+B) leaves the two
  T2 and two T3 cases failing, functional all pass.
- Control task: pinned 0/6 security + 12/12 functional; control reference 6/6 + 12/12;
  control_miss_media_type security fail; control_overbroad functional fail.

## What could not be verified

- Browser behaviour itself: jsdom is not a browser. The cases assert the media type handed to the
  browser and the element the page builds, not rendering or script execution. The advisory's own
  precondition (a weakened or absent CSP) is stated in the report and is the scenario tested.
- The published B commit is a 2026 merge whose parent is far from the pin (8238a149); its diff
  cannot apply to this tree. `checks/upstream_fix.patch` is A applied verbatim plus B's two source
  edits (safe-media decision and its predicate) ported to the pinned setter, which is the same
  behaviour. `checks/upstream_first_fix.patch` is A's js change verbatim.
- Whether any browser ignores a `download` attribute for a same-origin blob is a browser claim and
  is not evidenced here; the task tests the download offer and the media type, both in the source.
- T3's embed is masked for script execution by C1's media-type fix (an octet-stream blob will not
  render). The T3 case therefore asserts the stated property — unsafe content must not be handed to
  a document container at all — rather than script execution. This is the build's main fairness
  concern and is stated in the final report.
- The advisory texts and diffs were read from the upstream git history; the reader record's own
  "unverified" notes about missing history do not apply to this build.
