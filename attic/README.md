# attic/

The round 1/2 driver from before the sibling pipeline (`build/run.py` and friends), 2026-10-13..17.

**Nothing here is runnable as it is.** These files use the paths from before the 2026-10-25 reorganisation (`builder/`, `pipeline/`, `harness/`, `stacking/`, `sibling2/`, `build/trial.py`, ...). They are kept so that no earlier work is lost and every past run can be traced to the code that ran it. To revive one, port it to `common/paths.py` / `common/paths.sh` first.

## round1-2-driver/

Legacy driver: `run.py`, `status.py`, `slot.py`, `trial_fleet.py`, `queue_offline.py`.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `round1-2-driver/queue.json` | `build/queue.json` | 2026-10-22 11:17 | `b2356dcea9cf` |
| `round1-2-driver/queue_offline.py` | `build/queue_offline.py` | 2026-10-20 19:17 | `ccb096d731c5` |
| `round1-2-driver/rebuilt_tasks_chain.sh` | `build/rebuilt_tasks_chain.sh` | 2026-10-15 15:16 | `8ea35a1e2a1a` |
| `round1-2-driver/resmon.sh` | `build/resmon.sh` | 2026-10-16 11:22 | `0d9689ecb5fa` |
| `round1-2-driver/run.py` | `build/run.py` | 2026-10-14 14:00 | `718d64c81031` |
| `round1-2-driver/slot.py` | `build/slot.py` | 2026-10-16 07:05 | `9ea24d2dd23c` |
| `round1-2-driver/status.py` | `build/status.py` | 2026-10-13 23:31 | `5865141d2e06` |
| `round1-2-driver/trial_fleet.py` | `build/trial_fleet.py` | 2026-10-15 01:21 | `e53e6402ec55` |
