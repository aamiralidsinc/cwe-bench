#!/bin/bash
# Run one hidden group through the JUnit Platform console launcher and leave one JUnit XML file at
# the path the verifier's run_group() supplies. The launcher writes one report per engine/class, so
# the reports are merged under a single <testsuites> root for the scorer.
set -u
group=${1:?usage: run_tests.sh security|functional OUT}
out=${2:?usage: run_tests.sh security|functional OUT}
CP="/workspace/.htests/classes/support:/workspace/.htests/classes/app:$(ls /opt/payara-deps/*.jar | paste -sd:)"
rep=$(mktemp -d)
case "$group" in
  security)   cls=security.SecurityTests ;;
  functional) cls=functional.FunctionalTests ;;
  *) echo "unknown group $group" >&2; exit 2 ;;
esac
java -jar /opt/junit-console.jar execute -cp "$CP" --select-class="$cls" \
    --reports-dir="$rep" --disable-banner --details=tree
rc=$?
python3 -I - "$rep" "$out" <<'PY'
import glob, os, sys, xml.etree.ElementTree as ET
rep, out = sys.argv[1], sys.argv[2]
root = ET.Element("testsuites")
found = 0
for path in sorted(glob.glob(os.path.join(rep, "TEST-*.xml"))):
    try:
        suite = ET.parse(path).getroot()
    except Exception:
        continue
    root.append(suite)
    found += len(list(suite.iter("testcase")))
if found:
    ET.ElementTree(root).write(out, encoding="UTF-8", xml_declaration=True)
sys.exit(0 if found else 3)
PY
mrc=$?
rm -rf "$rep"
[ "$mrc" -eq 0 ] || exit "$mrc"
exit "$rc"
