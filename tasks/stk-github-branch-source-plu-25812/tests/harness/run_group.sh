#!/bin/bash
# Run one hidden group with the project's native runner (Maven + surefire) and leave a single
# JUnit XML behind. A build or start-up failure is a failing group, never a missing result.
set -u
G=${1:?group}
OUT=${2:?junit xml path}

export JAVA_HOME=/opt/java/openjdk
export PATH="$JAVA_HOME/bin:/usr/local/bin:/usr/bin:/bin"
export HOME=/home/agent
cd /workspace || exit 0

case "$G" in
  security) PAT='Sec*' ;;
  functional) PAT='Func*' ;;
  *) exit 0 ;;
esac

SKIPS="-Dspotbugs.skip=true -Dcheckstyle.skip=true -Denforcer.skip=true \
-Dspotless.check.skip=true -Dspotless.apply.skip=true -Dmaven.javadoc.skip=true \
-Dlicense.skip=true -Dforbiddenapis.skip=true -Daccess-modifier-checker.skip=true"

rm -rf /workspace/target/surefire-reports
mvn -B -o -ntp -Dmaven.repo.local=/opt/m2 $SKIPS \
    -Dtest="$PAT" -DfailIfNoTests=false test > "/workspace/.htests/mvn-$G.log" 2>&1
rc=$?
python3 -I /workspace/.htests/harness/merge_results.py \
    /workspace/target/surefire-reports "$OUT" "$G" "$rc"
exit 0
