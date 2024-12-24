"""Shared pytest fixtures."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_path(request):
    """Override tmp_path to avoid Windows permission issues."""
    d = Path(tempfile.mkdtemp(prefix="sc_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def pytest_collection_modifyitems(config, items):
    """Enforce flat test layout — no subfolders except fixtures/."""
    seen = set()
    for item in items:
        path = Path(str(item.fspath))
        try:
            rel = path.relative_to(ROOT / "tests")
        except ValueError:
            continue
        if len(rel.parts) > 1:
            seen.add(rel.parts[0])
    bad = seen - {"fixtures"}
    assert not bad, "tests must live directly in tests/, not subfolders: %s" % bad
