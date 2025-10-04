from atlas_mcp.central_page import get_allowed_scopes, run_centralpage
from atlas_mcp import central_page as central_page_mod
import importlib
import subprocess


def test_get_allowed_scopes():
    scopes = get_allowed_scopes()
    assert len(scopes) >= 2
    assert all(
        hasattr(scope, "scope") and hasattr(scope, "description") for scope in scopes
    )
    assert any(scope.scope == "mc20_13TeV" for scope in scopes)
    assert any(scope.scope == "mc23_13p6TeV" for scope in scopes)


def test_get_hash_tags_toplevel(mocker, monkeypatch, tmp_path):
    # Set a temporary cache location via env var and reload module so the module
    # cache uses a per-test directory (avoids touching the user's persistent cache)
    monkeypatch.setenv("ATLAS_MCP_CACHE_DIR", str(tmp_path / "cache"))
    importlib.reload(central_page_mod)

    # Mock the run_centralpage function to return a known output
    mocker.patch(
        "atlas_mcp.central_page.run_centralpage", return_value="tag1\ntag2\ntag3"
    )

    tags = central_page_mod.get_hash_tags(
        central_page_mod.CentralPageAddress(scope="mc20_13TeV", hash_tags=[])
    )
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
