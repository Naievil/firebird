import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--workspace", action="store", required=True, help="Path to workspace directory"
    )
    parser.addoption(
        "--boot1", action="store", required=True, help="Path to boot1 file"
    )
    parser.addoption(
        "--flash", action="store", required=True, help="Path to flash file"
    )
    parser.addoption("--os", action="store", required=True, help="Path to OS file")
    parser.addoption(
        "--firebird-headless",
        action="store",
        default="./firebird-headless",
        help="Path to firebird-headless executable",
    )
    parser.addoption(
        "--system-id",
        action="store",
        choices=["CX", "CXII"],
        default="CXII",
        help="System ID for the emulator (e.g., CX, CXII)",
    )


@pytest.fixture
def boot1_path(request):
    return request.config.getoption("--boot1")


@pytest.fixture
def flash_path(request):
    return request.config.getoption("--flash")


@pytest.fixture
def os_path(request):
    return request.config.getoption("--os")


@pytest.fixture
def firebird_headless_path(request):
    return request.config.getoption("--firebird-headless")


@pytest.fixture
def system_id(request):
    return request.config.getoption("--system-id")


@pytest.fixture
def workspace_path(request):
    return request.config.getoption("--workspace")

# Hook function to print a new line right as each test starts
def pytest_runtest_logstart(nodeid, location):
    """Called when pytest starts running a test."""
    print()  # just prints a newline