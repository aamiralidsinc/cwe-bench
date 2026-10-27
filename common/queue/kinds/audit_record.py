"""audit_record: record finished audits and rebuild the ledger (postmortem.py record-ready; audit_results.py)."""
from kinds import Kind, check_from, command_from, register

register(Kind(name="audit_record", command=command_from("phase4"), check=check_from("c_audit_record"), light=True,
              priority=60, max_running=1, max_attempts=1, reads=("<trial>/postmortem-*/verdict.json",),
              writes=("build/audit/ledger.md", "build/audit/trials.tsv")))
