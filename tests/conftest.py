import pytest

@pytest.fixture(autouse=True)
def ensure_pyami_installed() -> None:
    from ami_helper.utils import ensure_setup
    ensure_setup()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that exercise real AMI/Central Page calls.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: mark tests that require AMI/Central Page access",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--integration"):
        return
    skip_integration = pytest.mark.skip(reason="need --integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
