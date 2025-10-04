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


def test_run_on_wsl_with_path_files_mocked(mocker, tmp_path):
    """Test run_on_wsl with Path file objects using mocked subprocess calls."""
    # Create a temporary test file
    test_file = tmp_path / "test_input.txt"
    test_file.write_text("Test file content for Path object")

    # Mock subprocess.run to simulate successful file copying and command execution
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        # File copy result
        subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        # Main command result
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout="file processed\n", stderr=""
        ),
    ]

    result = run_on_wsl("ls /tmp", files={"data.txt": test_file})

    assert result == "file processed\n"
    assert mock_run.call_count == 2

    # Check that the first call was for copying the file with the specified name
    first_call = mock_run.call_args_list[0]
    assert "cp" in first_call[0][0]
    assert "/tmp/data.txt" in first_call[0][0]


def test_run_on_wsl_file_not_found():
    """Test that run_on_wsl raises FileNotFoundError for non-existent Path files."""
    non_existent_path = Path("/non/existent/file.txt")

    try:
        run_on_wsl("echo test", files={"missing.txt": non_existent_path})
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as e:
        assert str(non_existent_path) in str(e)


def test_run_on_wsl_mixed_files_mocked(mocker, tmp_path):
    """Test run_on_wsl with mixed string and Path files using dictionary format."""
    # Create a temporary test file
    test_file = tmp_path / "existing.txt"
    test_file.write_text("Existing file content")

    # Mock subprocess.run to simulate successful file copying and command execution
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        # First file copy (string content)
        subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        # Second file copy (Path object)
        subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        # Main command result
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout="files processed\n", stderr=""
        ),
    ]

    # Test with mixed content using dictionary format
    files_dict = {
        "script.sh": "#!/bin/bash\necho 'Hello from script'",
        "data.csv": test_file,
    }
    result = run_on_wsl("bash /tmp/script.sh && cat /tmp/data.csv", files=files_dict)

    assert result == "files processed\n"
    assert mock_run.call_count == 3

    # Check that files were copied with correct names
    calls = mock_run.call_args_list
    assert "base64 -d > /tmp/script.sh" in calls[0][0][0][-1]
    assert "/tmp/data.csv" in calls[1][0][0]
