#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
printf '%s\n' stk-jenkins-ghsa7fpg stk-elfinder-ghsa44p8 stk-fabio-ghsafq95 stk-siyuan-ghsa4mx9 stk-mlflow-3745 stk-openremote-29156 stk-nuclei-ghsajpvm stk-pyload-ghsa7gvf stk-lemur-5644 \
 | xargs -P5 -I{} bash -c 'sleep $((5 + RANDOM % 25)); bash stacking/out/reword_chain_20261024.sh "$1"' _ {}
echo "$(date -u +%FT%TZ) reword batch done" >> stacking/out/ride_along.log
