# asyncssh-inv: fairness audit of the rewritten instruction

Instruction: `tasks/asyncssh-inv/instruction.md` (system + invariant style), written 2026-10-16.
Tests: `tasks/asyncssh-inv/tests/` are identical to `tasks/asyncssh/tests/` after the 2026-10-16 repair
(12 security + 5 functional). Neither the tests nor `solution/` changed.

Quotes in the third column come from the new instruction. "Example" means the one trigger example in the Report.

## Per-test table

| test (file::name) | what it asserts | what makes it fair | risk |
|---|---|---|---|
| security/test_message_injection.py::test_server_rejects_early_userauth | A raw client sends its version line and then a plaintext USERAUTH_REQUEST before KEXINIT. The server must close the socket or send DISCONNECT within 3 s. | It is the example, almost word for word. Invariant: "Until the initial key exchange has completed, an endpoint, server or client alike, must not act on anything ... only valid once the secure channel exists (user authentication, ...). On receiving such a message it must drop the connection promptly." | low |
| security/test_message_injection.py::test_server_rejects_early_ext_info | Same, but the injected packet is EXT_INFO sent toward the server. The server must drop the connection. | Same invariant: "server or client alike", "protocol-extension negotiation". Expert knowledge also covers it: RFC 8308 allows EXT_INFO only after NEWKEYS, and the Terrapin work made pre-NEWKEYS injection a well-known class. | low-medium (the extension category is named only in a parenthesis) |
| security/test_message_injection.py::test_client_rejects_early_ext_info | A raw server sends EXT_INFO (server-sig-algs) before KEXINIT. The asyncssh client must drop the connection within 3 s. | Same invariant: "server or client alike", "protocol-extension negotiation", "drop the connection promptly". | low-medium |
| security/test_message_injection.py::test_client_rejects_early_userauth_success | A raw server sends USERAUTH_SUCCESS before KEXINIT. The client must drop the connection. | Same invariant: "server or client alike", "user authentication". | low |
| security/test_authkeys_traversal.py::test_authorized_keys_username_traversal | The server config has `AuthorizedKeysFile <base>/keys/%u/authorized_keys`. The user `legit` logs in with its own key (must succeed). The user `../OUTSIDE` uses a key planted in `<base>/OUTSIDE` (connect must raise). | Report: "authorized keys are found through a per-user path template, one key directory per account name". Invariant: "No user name a client presents may steer the authorized-keys lookup outside that location; such a login must be refused." Preservation: "public-key logins of ordinary account names through the per-user template". | low |
| security/test_authkeys_traversal.py::test_authorized_keys_username_embedded_traversal | Same setup, with user name `legit/../../OUTSIDE`. The legitimate login must still succeed and the attack must fail. | "No user name" covers every spelling, embedded traversal included. | low |
| security/test_scp_traversal.py::test_scp_download_path_traversal | A malicious SCP source sends a C-record named `../escaped_evil`. Nothing may be written at `<base>/escaped_evil`. An exception from scp() is allowed. | Invariant: "No file name or other data sent by the remote side may make the client create or write a file anywhere outside that destination." | low |
| security/test_scp_traversal.py::test_scp_download_absolute_path | Same, with an absolute name `<base>/abs_escaped`. The file must not exist afterwards. | "No file name ... anywhere outside that destination" covers absolute names. | low |
| security/test_scp_traversal.py::test_scp_download_embedded_traversal | Same, with `sub/../../embedded_escaped`, where `dst/sub` already exists. The file must not escape. | Same sentence ("No file name"). | low |
| security/test_pktsize_dos.py::test_channel_zero_pktsize_dos | The client opens a session advertising max_pktsize 0 and the server has output to send. Within 30 s, connect must succeed and `conn.run` must raise `asyncssh.Error`. Completing normally counts as a failure. | Invariant: "a size too small to carry any data (such as zero) must never make the receiving endpoint hang. The channel must instead be refused promptly with a protocol error, which the application sees as the library's ordinary error. It must not be adjusted and served." | low |
| security/test_pktsize_dos.py::test_channel_zero_pktsize_dos_dropbear_compression | Same, but the client's version string is `dropbear_2022.83` and compression is negotiated by default. The library turns the advertised 0 into -1 internally. | The peer still advertises exactly 0, which the invariant already covers. "A size too small to carry any data" also covers the internal -1, so a guard on the raw advertised value passes, and so does a `<= 0` guard. Expert knowledge: the peer's version string is attacker-controlled, so special handling keyed on it is part of the attack surface. Dropbear is deliberately not named, because naming it would point at the code path. | medium (an agent that guards with `== 0` after the version-based adjustment fails, and the instruction does not point at that adjustment; the wording does cover the case) |
| security/test_pktsize_dos.py::test_channel_zero_pktsize_in_open_confirmation | The server has max_pktsize 0, so its open confirmation advertises 0, and the client sends stdin. The client must refuse, so `conn.run` raises `asyncssh.Error` within 30 s. | "Whichever side states it, whether opening a channel or accepting one ...". The refusal form is the same sentence as above. | low |
| functional/test_auth.py::test_password_login | A password login works and `conn.run` returns the handler's stdout `hello`. | "password logins", "command runs with small output" | low |
| functional/test_auth.py::test_per_user_pubkey_login | `alice` authenticates with a key under `keys/alice/` through the `%u` template. | "public-key logins of ordinary account names through the per-user template" | low |
| functional/test_scp.py::test_legit_scp_download | `scp((conn, "/report.txt"), dst)` from a real SFTP/SCP server writes `dst/report.txt` with the right contents. | "SCP downloads of ordinary file names, including names that contain dots" | low |
| functional/test_session.py::test_command_roundtrip | `conn.run` returns exit status 0 and the exact stdout. | "command runs with small output" | low |
| functional/test_session.py::test_large_output_multiple_packets | About 256 KiB of output arrives intact with exit status 0. | "output of hundreds of kilobytes that spans many packets at the default packet sizes" | low |

## Contracts kept, and why

- **Refusal form, handshake:** "drop the connection promptly". The tests accept an EOF or an SSH
  DISCONNECT within 3 s. Simply ignoring the message would fail, so the drop is stated.
- **Refusal form, packet size:** "refused promptly with a protocol error, which the application sees as
  the library's ordinary error. It must not be adjusted and served." The scenario counts a completed run
  as `unexpected-complete`, which fails. So silently raising a zero size to a usable value must be ruled
  out explicitly, because an engineer could reasonably choose to do that. This is a contract, not a hint.
- **Both directions** for the handshake ("server or client alike") and for packet size ("whether opening
  a channel or accepting one"). Without these, the repair tests for the client direction and the open
  confirmation would rest on an assumption.
- **The per-user template configuration** is described at product level ("OpenSSH-style configuration
  ... per-user path template, one key directory per account name"). The tests depend on this setup,
  and an operator would describe it this way.
- **Preservation, with the legitimate magnitudes:** small and large (hundreds of KiB) command output,
  dotted SCP file names, password and per-user public-key logins.
- **Installs and imports from `/app`:** kept from the original.
- The 2026-10-16 repairs (client-direction and second-type injection, embedded and absolute SCP names,
  embedded user-name traversal, the dropbear and compression zero, the open confirmation) are all
  covered by the wording of the invariants. None of them is listed as a variant.

## Removed from the old instruction

- The four per-flaw sections and their bold titles, which gave away the count (four) and the grouping.
- "Several behaviours look like security problems" (kept only as "several ways", with no count) and
  "find the root cause of each".
- The handshake detail: "connection- or authentication-layer packet", the two reproduced directions
  ("a raw client that sends an early authentication request to the server, and a raw server that sends
  an early extension-information packet to the client"), and "before any encryption is negotiated".
  This is now one example plus a direction-neutral invariant.
- User name: "path-traversal segments", "a directory *outside* the key area", "it will authenticate a
  key planted there", "a name that walks outside its own key directory".
- SCP: "a malicious or compromised server can name a transferred file with a leading traversal
  segment", which named the mechanism and the leading-segment variant, and "a name that points outside
  the destination must be rejected", which gave the fix approach (reject the name).
- Packet size: "the endpoint hangs as soon as it has channel data to send back — it spins on the CPU
  and never returns", which described the mechanism (a busy loop in the send path), and "If a peer
  advertises a maximum packet size of zero" as the single trigger. That is now "a size too small to
  carry any data (such as zero)".
- "Each of the abuses above is rejected through the same public entry points" was replaced by the
  per-invariant refusal forms.
- The original had no constraints block. The standard one was added (no test edits, no upstream fix
  lookup, no special-casing the example).

## Minimum hint wording kept

- The handshake invariant names two example categories in a parenthesis ("user authentication,
  protocol-extension negotiation and the like"). Without "protocol-extension negotiation", the two
  EXT_INFO tests would rest on knowledge of RFC 8308 alone. That is standard for SSH experts, but it
  makes them medium-risk, so the category is kept as the minimum needed for fairness. It names a
  category of message, not a code location or a fix.
- "Such as zero" for the packet size, which is the attacker's actual input.
- 2026-10-16 (lead): removed the sentence 'It must not be adjusted and served.' from the instruction: it pointed at the adjustment the dropbear test probes. The refusal contract ('refused promptly with a protocol error') still states what the test requires.
