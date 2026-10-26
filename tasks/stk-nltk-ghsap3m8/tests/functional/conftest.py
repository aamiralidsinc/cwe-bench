import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "support"))


@pytest.fixture(autouse=True)
def _isolate_data_path():
    """Keep each case's data locations and resource cache to itself."""
    import nltk.data

    saved = list(nltk.data.path)
    nltk.data.clear_cache()
    try:
        yield
    finally:
        nltk.data.path[:] = saved
        nltk.data.clear_cache()
