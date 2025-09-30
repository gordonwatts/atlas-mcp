from atlas_mcp.central_page import (
    get_allowed_scopes,
    get_hash_tags,
    CentralPageAddress,
    run_centralpage,
)
import subprocess


def test_get_allowed_scopes():
    scopes = get_allowed_scopes()
    assert len(scopes) >= 2
    assert all(
        hasattr(scope, "scope") and hasattr(scope, "description") for scope in scopes
    )
    assert any(scope.scope == "mc20_13TeV" for scope in scopes)
    assert any(scope.scope == "mc23_13p6TeV" for scope in scopes)


def test_get_hash_tags_toplevel(mocker):
    # Mock the run_centralpage function to return a known output
    mocker.patch(
        "atlas_mcp.central_page.run_centralpage", return_value="tag1\ntag2\ntag3"
    )

    tags = get_hash_tags(CentralPageAddress(scope="mc20_13TeV", hash_tags=[]))
    assert tags == ["tag1", "tag2", "tag3"]


def test_run_centralpage(mocker):
    # Mock subprocess.run to return a known output
    mocker.patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["centralpage", "list-tags", "--scope", "mc20_13TeV"],
            returncode=0,
            stdout="tag1\ntag2\ntag3\n",
            stderr="",
        ),
    )

    output = run_centralpage(["list-tags", "--scope", "mc20_13TeV"])
    assert output == "tag1\ntag2\ntag3\n"


def test_run_centralpage_for_real():
    # This test actually runs the command on the WSL2 instance.
    # It requires that the WSL2 instance 'atlas_al9' is set up correctly.
    output = run_centralpage(["--help"])
    assert len(output) > 5  # Help output should be several lines
    assert output[0] == "Usage: centralpage [options] L1 L2 L3 L4"
