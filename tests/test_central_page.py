from atlas_mcp.central_page import get_allowed_scopes, run_centralpage, run_on_wsl
from atlas_mcp import central_page as central_page_mod
import importlib
import subprocess
from pathlib import Path


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


def test_run_on_wsl_with_files_mocked(mocker):
    """Test run_on_wsl with file copying functionality using mocked subprocess calls."""
    # Mock subprocess.run to simulate successful file copying and command execution
    mock_run = mocker.patch("subprocess.run")

    # First call for file copying, second call for main command
    mock_run.side_effect = [
        # File copy result
        subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        # Main command result
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout="test output\n", stderr=""
        ),
    ]

    # Test with string content using dictionary format
    test_content = "This is test file content\nLine 2"
    result = run_on_wsl("cat /tmp/input.txt", files={"input.txt": test_content})

    assert result == "test output\n"
    assert mock_run.call_count == 2

    # Check that the first call was for copying the file with the correct filename
    first_call = mock_run.call_args_list[0]
    assert "base64 -d > /tmp/input.txt" in first_call[0][0][-1]


def test_run_on_wsl_file_not_found():
    """Test that run_on_wsl raises FileNotFoundError for non-existent Path files."""
    non_existent_path = Path("/non/existent/file.txt")

    try:
        run_on_wsl("echo test", files={"missing.txt": non_existent_path})
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as e:
        assert str(non_existent_path) in str(e)


def test_get_samples_for_evtgen_parses_lines(mocker):
    """Ensure get_samples_for_evtgen parses lines after the start marker."""
    # Mock the environment runner to simulate the echoed start marker and two lines
    mocked_stdout = (
        "--start--\nmc23_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.evgen"
        ".EVNT.e8514 811.29 4.384567E-01 1.138433852\n   mc23a   FS DAOD_LLP1  "
        "mc23_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1."
        "e8514_s4162_r15540_p6942\n   mc23a   FS DAOD_LLP1  mc23_13p6TeV.601229."
        "PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1."
        "e8514_s4162_r15540_p6619\n   mc23a   FS DAOD_LLP1  mc23_13p6TeV.601229."
        "PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1."
        "e8514_s4162_r15540_p6463\n   mc23a   FS DAOD_LLP1  mc23_s4159_r15530_p6619\n   mc23d   "
        "FS DAOD_LLP1  mc23_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1"
        ".e8514_s4159_r15530_p6463\n   mc23d   FS DAOD_LLP1  mc23_13p6TeV.601229."
        "PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1.e8514_s4159_r15530_p6368\n   "
        "mc23e   FS DAOD_LLP1  mc23_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv."
        "DAOD_LLP1.e8514_s4369_r16083_p6942\n   mc23e   FS DAOD_LLP1  mc23_13p6TeV.601229."
        "PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1.e8514_s4369_r16083_p6619']"
    )

    mocker.patch(
        "atlas_mcp.central_page.run_in_centralpage_env", return_value=mocked_stdout
    )
    result = central_page_mod.get_samples_for_evtgen(
        "mc23_13p6TeV",
        "mc23_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.evgen.EVNT.e8514",
        "DAOD_LLP1",
    )

    assert len(result) == 8
    d1 = result[0]
    assert d1.x_sec == 811.29
    assert d1.generator_filter_eff == 0.4384567
    assert d1.k_factor == 1.138433852
    assert (
        d1.did
        == "mc23_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep.deriv.DAOD_LLP1."
        "e8514_s4162_r15540_p6942"
    )
    assert d1.d_type == "DAOD_LLP1"
    assert d1.s_type == "FS"
    assert d1.period == "mc23a"

    # Make sure all names are unique
    assert len(set(r.did for r in result)) == len(result)
