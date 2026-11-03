from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_repo():
    return FIX / "repo-ok"


@pytest.fixture
def fix():
    return FIX
