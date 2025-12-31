import pytest

from ami_helper.utils import ensure_and_import


@pytest.fixture(autouse=True)
def ensure_pyami_installed() -> None:
    ensure_and_import("pyAMI_atlas")
