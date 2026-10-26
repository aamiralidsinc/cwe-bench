"""Fixture helpers shared by the hidden suites.

Repositories and payload programs are built with the git CLI and the standard library only, so a
hardened library under test cannot change what a fixture produces. Every payload program used by
the security suite is harmless: it writes an empty marker file and exits.
"""
import os
import subprocess


def _git(args, cwd, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["HOME"] = cwd
    proc = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc


def make_repo(path):
    """Create a two-commit repository with a rename and an edit, using only the git CLI."""
    os.makedirs(path, exist_ok=True)
    _git(["init", "-q", "-b", "main"], path)
    _git(["config", "user.name", "Fixture"], path)
    _git(["config", "user.email", "fixture@example.invalid"], path)
    with open(os.path.join(path, "file_a.txt"), "w") as handle:
        handle.write("".join(f"alpha line {i}\n" for i in range(30)))
    with open(os.path.join(path, "keep.txt"), "w") as handle:
        handle.write("keep\n")
    _git(["add", "file_a.txt", "keep.txt"], path)
    _git(["commit", "-qm", "first"], path)
    os.rename(os.path.join(path, "file_a.txt"), os.path.join(path, "file_b.txt"))
    with open(os.path.join(path, "file_b.txt"), "w") as handle:
        handle.write("".join(f"beta line {i}\n" if i < 5 else f"alpha line {i}\n" for i in range(30)))
    with open(os.path.join(path, "keep.txt"), "w") as handle:
        handle.write("keep changed\n")
    _git(["add", "-A"], path)
    _git(["commit", "-qm", "second"], path)
    return path


def make_program(directory):
    """Write a harmless executable program that only creates an empty marker file."""
    program = os.path.join(directory, "payload.sh")
    marker = os.path.join(directory, "marker.txt")
    with open(program, "w") as handle:
        handle.write(f"#!/bin/sh\n: > '{marker}'\nexit 0\n")
    os.chmod(program, 0o755)
    return program, marker
