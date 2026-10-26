# NEEDS_HUMAN_REVIEW: stk-mlflow-3745 v3 (NOT a clean breaker: instruction ambiguity), 2026-10-25T04:20Z

- DeepSeek 0/3 [0, 0, 0] audited fair (r1 medium, r2/r3 high; r2/r3 also missed region/location host values).
  MiMo: r2, r5 (3 h) audited fair (high / medium); r3 audited UNTRUSTED (instruction-ambiguity, medium).
- **One functional test decides nearly every run:** functional/test_legitimate_upstreams::
  test_shipped_local_default_is_still_called (Ollama built-in default localhost:11434 must still be called).
- **Ambiguity:** the instruction sentence "No value supplied by a user ... may cause [a call to a non-public
  destination]" can be read to cover choosing provider=ollama (which routes to loopback); "Everything that works
  today keeps working" says the shipped default must keep working. The text does not say which wins. Two earlier
  auditors flagged the same point at medium confidence; fairness review said READY.
- **Proposed repair (instruction only, not applied):** scope that sentence to address, host or other
  destination-forming values a user supplies or that are stored, so a provider choice with its shipped default
  is not covered; keep the trap unnamed. Then re-run the listing check and re-trial both models (new version).
