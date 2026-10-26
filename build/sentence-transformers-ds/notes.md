# Build notes: sentence-transformers-ds

- Start (UTC): 2026-10-24T04:12:41Z (pipeline start)
- Plan written (UTC): 2026-10-24T04:20:00Z (before any task file)
- End (UTC): see end_utc.txt

## Advisory / commits
GHSA-JHR6-GM9C-RQJV / CVE-2026-68770 / PYSEC-2026-4164 — huggingface/sentence-transformers,
CWE-94 code injection via a class reference carried by a model's stored configuration
(the trust gate around class imports).
Pinned (vulnerable) 429cf5d424869c7aba629ded61e93b2788921677. Published fixes
626eb602b088878a8173bcab69225f68411b99e1 (v6: hard refusal) and
ae1acc3fb2aa2004577b297eb4a915ce7a03316a (first deprecation warning). Verified: the
security change itself is commit a2258de9 (#3860) inside the v6 branch; ae1acc3 and the
pinned commit are independent of it (the pin is not a2258de9's ancestor and vice versa).
Track INJECTED. Pattern A+B.

## Mechanism (one line)
A model's stored configuration can name a dotted class; the loader resolves it, and at
the pinned commit an untrusted reference is still imported through the plain-import
fallback (and through a second config field with no gate at all), so loading a model
can execute code the caller never opted into.

## Design: levers

| id | kind | site | shape | reason to dismiss |
|----|------|------|-------|-------------------|
| T1 | main, how-type (B-style route) | `sentence_transformers/util/misc.py:121-141` | the plain-import fallback: local dir, Hub id, existing file path, absent trust decision, CrossEncoder entry | the `os.path.exists` local-trust condition is the visible gate; dropping it (or switching it to `isdir`) looks like the whole fix, but the fallback still imports |
| T2 | far site A, how-type | `sentence_transformers/sentence_transformer/modules/word_embeddings.py:127` | a saved WordEmbeddings model whose tokenizer class is a non-library ref | a legacy GloVe-style tokenizer setting, not a module class; different package |
| T3 | far site A, where-type | `sentence_transformers/base/modules/router.py:650` | a Router module whose nested route type is a non-library ref | nested route configuration; a fix placed at the top-level resolver misses the module's own resolver |
| T4 | coupled must-keep-working, how-type | `sentence_transformers/base/trainer.py:1041-1044` | a training run restoring its own checkpoint of a programmatically built model with a custom module class | only appears at the end of training; the reload is in the trainer package and the model never carries an opt-in |
| S1 | injected sibling | `sentence_transformers/sentence_transformer/modules/cnn.py:95-101` | a saved CNN whose activation setting is a non-library ref | Dense/CrossEncoder already gate activations, so activation settings look handled; CNN is a rarely used legacy module |
| S2 | injected sibling | `sentence_transformers/base/modules/transformer.py:1852-1858` | a Transformer config naming a processor class | backbone loading delegates trust to transformers; the config loader already strips trust settings, so it looks hardened |

Distinct reasons-to-skip: hidden fallback / legacy tokenizer setting / nested resolver /
end-of-training reload / "activations are already gated" / "backbone trust is delegated".

## Property (stated once, general)
A class reference carried by a model's stored configuration must never cause code
outside sentence-transformers to be imported or executed unless that load explicitly
allows untrusted code, whether the model is a Hub id or a path on this machine, wherever
the stored configuration is consulted.

## Coupled must-keep-working (functional)
- built-in `sentence_transformers.*` refs load with no opt-in;
- the public class-lookup helper with no model location keeps importing installed classes;
- a local custom modeling file loads with the explicit opt-in;
- a training run restores its own checkpoint (in-memory classes; no new opt-in);
- ordinary saved models (static-embedding chain, tiny Transformer backbone, CNN with a
  built-in torch activation) reload and reproduce their embeddings.

## Injected siblings: full candidate list and why these two
Candidates found by searching every config-driven class/import site at the pin:
1. `base/modules/dense.py` activation_function — already gated (trust or `torch.` prefix,
   else default); not a route, recorded and dismissed.
2. `cross_encoder/model.py` `_resolve_activation_fn` — already gated the same way; dismissed.
3. `util/deprecated_import.py` legacy path mapping — fixed table, no config-selected import.
4. `base/modules/transformer.py` `_ENCODER_ONLY_MODELS` — fixed registry, not attacker input.
5. `word_embeddings.py` tokenizer_class — real far site (T2), used as a real lever.
6. `base/modules/router.py` nested types — real far site (T3), used as a real lever.
7. `sentence_transformer/modules/cnn.py` activation setting — no such setting upstream;
   injected as S1 because a maintainer copying Dense's activation feature into a legacy
   module is plausible, and the code is reachable through `modules.json`.
8. `base/modules/transformer.py` processor override — no such setting upstream; injected as
   S2 because the backbone loader already sanitises trust settings and a custom processor
   override would plausibly forget the gate; reachable through `sentence_bert_config.json`.
9. `sentence_transformer/modules/static_embedding.py` tokenizer — rejected: a second route
   of the tokenizer-class concept already covered by T2.
10. `multi_vector_encoder/model.py` `_get_module_init_defaults` raw import — exists only in
    the v6 tree (after the pin), so it cannot be a real route here; too large to backport.
Picked S1 and S2: distinct configuration surfaces, both how-type (the value has to be
produced into a config and understood), reachable through the real saved-model entry point,
and absent from the published security fix.

## Sites / routes the tests cover
- T1: local directory, Hub id, existing file path, `trust_remote_code=None`, CrossEncoder.
- T2: WordEmbeddings saved model through `SentenceTransformer`.
- T3: Router saved model through `SentenceTransformer`.
- S1: CNN saved model through `SentenceTransformer`.
- S2: Transformer saved model through `SentenceTransformer`.
- T4: trainer `resume_from_checkpoint` path (public `train()`).

## Verified
- Pinned+injected: 9/9 security tests fail (each writes its probe marker), 7/7 hidden
  functional pass; 14/14 selected project tests pass offline.
- Oracle: 9/9 security + 7/7 hidden functional + 14/14 project pass; score 30/30, reward 1.0.
- Every check patch re-run with the full task suite (hidden + project):
  sf-miss-fallback 3 security fails; sf-miss-word-embeddings / router / cnn / transformer
  1 security fail each; ff-refuse-all 2 hidden functional fails; ff-overbroad 1 hidden
  functional fail; pass-hardening and pass-alt 30/30 (reward 1.0).
- The trainer reload is genuinely exercised: transformers 5.20.2 `Trainer.train(resume_from_checkpoint=...)`
  calls the overridden `_load_from_checkpoint` (trainer.py:1547).
- Offline: both images cache the tiny model and the BERT tokenizer under /opt/hf-cache;
  tests run with `HF_HUB_OFFLINE=1` and no network.

## Could not verify / guesses
- `present_in_latest` for the register is from a read-only look at `origin/main` of the
  scratch clone (import_module_class raises; word_embeddings and router use the gate).
- The v6 fix commit is a large release merge; the oracle reduces it to the seven
  security-relevant hunks plus the two injected siblings.
- Snapshots: transformers 5.20.2 / huggingface-hub 2.3.0 / torch 2.14.1+cpu resolved by
  unpinned constraints; the pinned tree's own tests pass with them.

## Outside scope (noted, not built)
- The Transformer backbone's own `trust_remote_code` is passed through to transformers'
  gate; that is a different mechanism and was left alone.
- Dense/CrossEncoder activation gates are real but already safe at the pin.

## Gate results
- static: PASSED (only the downstream blind patch and FAIRNESS.md are absent, as designed).
- nop: PASSED — 9 security tests fail on the pinned+injected tree, 21 functional tests pass.
- oracle: PASSED — 3 runs, each reward 1.0 with identical 9/9 security and 21/21 functional results.
- patches: (see below)
- patches: PASSED — sf-miss-fallback (3 security fails, 0.6667), sf-miss-word-embeddings /
  sf-miss-router / sf-miss-cnn / sf-miss-transformer (1 security fail each, 0.8889);
  ff-refuse-all and ff-overbroad (functional fails, reward 0); pass-hardening and pass-alt
  (reward 1.0). All checks ran the full task suite, including the pristine project tests.

## End
- End (UTC): see end_utc.txt.
