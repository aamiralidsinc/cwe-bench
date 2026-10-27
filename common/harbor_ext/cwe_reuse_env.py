"""cwe_reuse_env: build each task image ONCE per task version and reuse it in every Harbor run.

Harbor (0.23 dev) builds a fresh image for every run: its docker-compose-build.yaml has no `image:`,
so compose tags the build `<project>-main` with a per-run project name (`<task>__<7 chars>__env`,
`<task>__<7 chars>__verifier__trial`). It computes a content tag (`hb__<environment_id>`) but never
uses it. On the VM each such image is a full rebuild, up to ~19 GB per run for Java/Node tasks.

Run Harbor with   PYTHONPATH=<repo>/common/harbor_ext  harbor run ... -e cwe_reuse_env:ReuseDockerEnvironment
Harbor copies the environment import path into the separate verifier's environment, so both the agent
image (environment/) and the verifier image (tests/) go through this class. For each it:
  * computes cwe-reuse/<task>:<env|verifier>-<content hash>  (cwe_reuse_tag.py; regrades use the same tag);
  * builds that image once (cross-process lock: parallel gate/trial runs of one task build it once);
  * starts the run through Harbor's own prebuilt-image path (docker-compose-prebuilt.yaml), exactly as if
    task.toml had `docker_image` set; the delivered task files are not touched.
Harbor's `down --rmi local` never removes an image with a custom tag, so the shared image survives runs.
Every run's `main` container also gets the cwe.* labels (cwe_labels.py) through one more compose override.
Stock behaviour (per-run build) for --force-build, a task that names docker_image, a task with its own
environment/docker-compose.yaml, Windows containers, or CWE_IMAGE_REUSE=0.
"""
from __future__ import annotations

import asyncio
import fcntl
import os
import tempfile
import time
from pathlib import Path

from harbor.environments.docker.docker import DockerEnvironment

from cwe_labels import labels as cwe_labels, write_compose as write_labels_compose
from cwe_reuse_tag import build_cmd, lock_path, reuse_tag, touch_used


async def _run(*cmd: str) -> tuple[int, str]:
    p = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                             stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await p.communicate()
    except asyncio.CancelledError:            # Harbor's build timeout cancels us: do not leave a build behind
        p.kill()
        await p.wait()
        raise
    return p.returncode, out.decode(errors="replace")


async def _exists(tag: str) -> bool:
    return (await _run("docker", "image", "inspect", "--format", "{{.Id}}", tag))[0] == 0


async def ensure_image(ctx, tag: str, logger=None) -> None:
    """Build `tag` from `ctx` unless it exists; one builder per tag across all processes."""
    touch_used(tag)
    if await _exists(tag):
        if logger:
            logger.info(f"cwe-reuse: reusing {tag}")
        return
    with open(lock_path(tag), "w") as lf:
        while True:                           # non-blocking poll so a Harbor timeout can still cancel us
            try:
                fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                await asyncio.sleep(3)
        if await _exists(tag):                # another process built it while we waited
            if logger:
                logger.info(f"cwe-reuse: reusing {tag} (built by another run)")
            return
        if logger:
            logger.info(f"cwe-reuse: building {tag} from {ctx}")
        t0 = time.time()
        rc, out = await _run(*build_cmd(ctx, tag))
        if rc != 0:
            raise RuntimeError(f"cwe-reuse: docker build of {tag} failed (exit {rc}):\n{out[-4000:]}")
        if logger:
            logger.info(f"cwe-reuse: built {tag} in {time.time() - t0:.0f}s")


class ReuseDockerEnvironment(DockerEnvironment):
    @property
    def _docker_compose_paths(self) -> list[Path]:
        """Harbor's compose files plus one labels override for `main` (cwe_labels.py). Last in the list, so it only
        adds labels. CWE_LABELS=0 leaves Harbor's list as it is."""
        paths = list(super()._docker_compose_paths)
        if os.environ.get("CWE_LABELS", "1") == "0" or getattr(self, "_is_windows_container", False):
            return paths
        f = getattr(self, "_cwe_labels_path", None)
        if f is None:
            d = tempfile.mkdtemp(prefix="cwe-labels-")
            lab = cwe_labels(os.environ, getattr(self, "session_id", "") or "",
                             getattr(self, "environment_name", "") or "")
            f = write_labels_compose(Path(d) / "docker-compose-cwe-labels.json", lab)
            self._cwe_labels_path = f
        return paths + [f]

    def _reuse_applies(self, force_build: bool) -> bool:
        return (os.environ.get("CWE_IMAGE_REUSE", "1") != "0"
                and not force_build
                and not self.task_env_config.docker_image
                and not self._is_windows_container
                and self._dockerfile_path.exists()
                and not self._environment_docker_compose_path.exists())

    async def start(self, force_build: bool):
        if self._reuse_applies(force_build):
            ctx = self.environment_dir.resolve()
            _ = self.environment_id           # cache Harbor's content id from the unmodified config
            tag = reuse_tag(ctx)
            await ensure_image(ctx, tag, self.logger)
            # From here on Harbor treats the run exactly like a task with `docker_image = tag`.
            # model_copy: the Task's own config object (shared by other runs in this process) stays as is.
            self.task_env_config = self.task_env_config.model_copy(update={"docker_image": tag})
            self._env_vars.prebuilt_image_name = tag
        return await super().start(force_build)

    async def stop(self, delete: bool):
        try:
            return await super().stop(delete)
        finally:
            f = getattr(self, "_cwe_labels_path", None)
            if f is not None:                 # the override is only needed while compose runs
                try:
                    f.unlink()
                    f.parent.rmdir()
                except OSError:
                    pass
                self._cwe_labels_path = None
