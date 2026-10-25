# Exploratory analysis of 2026-10-22 (kept as a record)

The scripts that produced the first findings (feature AUCs, post-build features, leave-one-out
filter), copied out of the session scratchpad. They read the unpacked 10-21 VM snapshot at the
scratchpad path written inside them, so they will not run as-is. The maintained, self-contained version
of the label/score/LOO logic is `../screen.py`, which reads only `../../inputs/`.

- label.py: outcome per DeepSeek-lane candidate -> labels.json
- feat.py: pre-build pool features + AUCs -> rows.json
- post.py: post-build task features (manifest sites/traps, instruction words, test counts) -> rows2.json
- rule.py: the leave-one-out filter test (same model as screen.py)
