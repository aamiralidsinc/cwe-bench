"""Hidden-test bootstrap.

The product tree lives in /app (overridable for local validation).  pytest is
invoked with cwd=/app, but the tests themselves live under /tests, so make the
product root importable explicitly and put this directory on the path for the
shared helpers module.
"""
import os
import sys
from pathlib import Path

APP_DIR = os.environ.get("HERMES_APP_DIR", "/app")
sys.path.insert(0, APP_DIR)
sys.path.insert(0, str(Path(__file__).resolve().parent))
