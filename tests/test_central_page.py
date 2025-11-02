import pytest
import atlas_mcp.central_page as central_page_mod
from atlas_mcp.central_page import (
    CentralPageAddress,
    get_allowed_scopes,
    run_on_wsl,
    get_samples_for_run,
    get_metadata,
    get_provenance,
)
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


# def test_get_hash_tags_toplevel(mocker, monkeypatch, tmp_path):
#     # Set a temporary cache location via env var and reload module so the module
#     # cache uses a per-test directory (avoids touching the user's persistent cache)
#     monkeypatch.setenv("ATLAS_MCP_CACHE_DIR", str(tmp_path / "cache"))
#     importlib.reload(central_page_mod)

#     # Mock the run_centralpage function to return a known output
#     mocker.patch(
#         "atlas_mcp.central_page.run_centralpage", return_value=["tag1", "tag2", "tag3"]
#     )

#     tags = central_page_mod.get_hash_tags(
#         central_page_mod.CentralPageAddress(scope="mc20_13TeV", hash_tags=[])
#     )
#     assert tags == ["tag1", "tag2", "tag3"]


# def test_run_centralpage(mocker):
#     # Mock subprocess.run to return a known output
#     mocker.patch(
#         "subprocess.run",
#         return_value=subprocess.CompletedProcess(
#             args=["centralpage", "list-tags", "--scope", "mc20_13TeV"],
#             returncode=0,
#             stdout="tag1\ntag2\ntag3\n",
#             stderr="",
#         ),
#     )

#     output = run_centralpage(["list-tags", "--scope", "mc20_13TeV"])
#     assert output == ["tag1", "tag2", "tag3"]


# def test_run_centralpage_for_real():
#     # This test actually runs the command on the WSL2 instance.
#     # It requires that the WSL2 instance 'atlas_al9' is set up correctly.
#     output = run_centralpage(["--help"])
#     assert len(output) > 5  # Help output should be several lines
#     assert output[0] == "Usage: centralpage [options] L1 L2 L3 L4"


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


# def test_get_address_for_keyword(mocker):
#     """Test get_address_for_keyword with mocked run_ami_helper output."""
#     # Mock run_ami_helper to return the provided test data
#     mock_output = """JetPhoton Dijet Systematic Sherpa2214
# JetPhoton Dijet Systematic PowhegPythia8
# JetPhoton Dijet Systematic Herwig72
# JetPhoton Dijet Baseline Pythia8
# JetPhoton Dijet Alternative Sherpa_2214_Lund
# JetPhoton Dijet Alternative Sherpa2214_Lund
# JetPhoton Dijet Alternative Sherpa2214_Dire
# JetPhoton Dijet Alternative PowhegHerwig72
# JetPhoton Dijet Alternative Herwig72_Dipole"""

#     mocker.patch(
#         "atlas_mcp.central_page.run_ami_helper",
#         return_value=mock_output.splitlines(),
#     )

#     # Test with a single keyword
#     addresses = central_page_mod.get_address_for_keyword("mc23_13p6TeV", "Dijet")

#     # All lines have 4 parts and should be parsed as addresses
#     assert len(addresses) == 9

#     # Verify structure of first address
#     assert addresses[0].scope == "mc23_13p6TeV"
#     assert addresses[0].hash_tags == (
#         "JetPhoton",
#         "Dijet",
#         "Systematic",
#         "Sherpa2214",
#     )

#     # Test with multiple keywords - should filter to only matching addresses
#     addresses_filtered = central_page_mod.get_address_for_keyword(
#         "mc23_13p6TeV", ["Dijet", "Baseline"]
#     )
#     assert len(addresses_filtered) == 1
#     assert addresses_filtered[0].hash_tags == [
#         "JetPhoton",
#         "Dijet",
#         "Baseline",
#         "Pythia8",
#     ]

#     # Test with multiple keywords that match multiple addresses
#     addresses_systematic = central_page_mod.get_address_for_keyword(
#         "mc23_13p6TeV", ["Dijet", "Systematic"]
#     )
#     assert len(addresses_systematic) == 3
#     assert all("Systematic" in addr.hash_tags for addr in addresses_systematic)

#     # Test with keyword list (alternative API)
#     addresses_list = central_page_mod.get_address_for_keyword(
#         "mc23_13p6TeV", ["Dijet", "Alternative"]
#     )
#     assert len(addresses_list) == 5
#     assert all("Alternative" in addr.hash_tags for addr in addresses_list)


def test_central_page_address_json_serialization():
    """Test that CentralPageAddress can be serialized and
    deserialized to/from JSON."""
    # Create a CentralPageAddress instance
    original = CentralPageAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad", "PwPy8", "2L2Nu")
    )

    # Serialize to JSON using Pydantic's model_dump_json()
    json_str = original.model_dump_json()

    # Deserialize from JSON using Pydantic's model_validate_json()
    reconstructed = CentralPageAddress.model_validate_json(json_str)

    # Verify the reconstructed object matches the original
    assert reconstructed.scope == original.scope
    assert reconstructed.hash_tags == original.hash_tags
    assert reconstructed == original


def test_central_page_address_hashable():
    """Test that CentralPageAddress is hashable (required for caching)."""
    # Create two identical instances
    addr1 = CentralPageAddress(scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad"))
    addr2 = CentralPageAddress(scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad"))

    # Test that they can be hashed
    hash1 = hash(addr1)
    hash2 = hash(addr2)

    # Identical instances should have the same hash
    assert hash1 == hash2

    # Test they can be used in a set (requires hashability)
    addr_set = {addr1, addr2}  # type: ignore[Unhashable]
    assert len(addr_set) == 1  # Should only have one element

    # Test they can be used as dict keys
    cache_dict = {addr1: "value1"}  # type: ignore[Unhashable]
    assert cache_dict[addr2] == "value1"


@pytest.mark.parametrize(
    "derivation, expected_flag",
    [
        ("PHYS", "DAOD_PHYS"),
        ("PHYSLITE", "DAOD_PHYSLITE"),
        ("DAOD_LLP1", "DAOD_LLP1"),
    ],
)
def test_get_samples_for_run_builds_correct_command(mocker, derivation, expected_flag):
    """Verify mapping and delegation for get_samples_for_run.

    Ensures derivation maps to the expected flag and the ami-helper
    command is constructed correctly.
    """
    # Ensure cache doesn't short-circuit this test
    central_page_mod.cache.clear()

    # Mock with valid JSON output
    mock_json_output = ['{"datasets": ["ds1", "ds2"]}']

    mocked = mocker.patch(
        "atlas_mcp.central_page.run_ami_helper", return_value=mock_json_output
    )

    scope = "mc23_13p6TeV"
    run_number = "00473423"

    result = get_samples_for_run(scope, run_number, derivation)

    # Returns parsed JSON
    assert result == {"datasets": ["ds1", "ds2"]}

    # Ensures we built the proper command
    mocked.assert_called_once_with(
        f"datasets with-datatype {scope} {run_number} {expected_flag} -o json"
    )


@pytest.mark.parametrize("bad_derivation", ["INVALID", "AOD"])
def test_get_samples_for_run_invalid_derivation_raises(bad_derivation):
    """Invalid derivations (incl. 'AOD') currently raise RuntimeError.

    Note: Docstring lists 'AOD' as an example, but current code
    does not accept it. This documents current behavior.
    """
    # Ensure cache doesn't short-circuit this test
    central_page_mod.cache.clear()

    with pytest.raises(RuntimeError) as excinfo:
        get_samples_for_run("mc23_13p6TeV", "00473423", bad_derivation)

    assert "Invalid `derivation`" in str(excinfo.value)


def test_get_metadata_builds_correct_command(mocker):
    """Verify get_metadata constructs the ami-helper command correctly
    and parses JSON output.
    """
    # Ensure cache doesn't short-circuit this test
    central_page_mod.cache.clear()

    # Mock the ami-helper output as JSON
    mock_json_output = [
        "{",
        '  "Physics Comment": "NULL",',
        '  "Physics Short Name": "Py8EG_A14NNPDF23LO_jj_JZ9incl",',
        '  "Generator Name": "Pythia8(v.308)+EvtGen(v.2.1.1)",',
        '  "Filter Efficiency": 0.01530918,',
        '  "Cross Section (nb)": 0.000027822',
        "}",
    ]

    mocked = mocker.patch(
        "atlas_mcp.central_page.run_ami_helper", return_value=mock_json_output
    )

    scope = "mc23_13p6TeV"
    dataset_name = (
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9."
        "deriv.DAOD_PHYS.e8514_s4162_r14622_p5855"
    )

    result = get_metadata(scope, dataset_name)

    # Verify the command was constructed correctly
    mocked.assert_called_once_with(f"datasets metadata {scope} {dataset_name} -o json")

    # Verify the returned dictionary contains the expected fields
    assert isinstance(result, dict)
    assert result["Physics Comment"] == "NULL"
    assert result["Physics Short Name"] == "Py8EG_A14NNPDF23LO_jj_JZ9incl"
    assert result["Generator Name"] == "Pythia8(v.308)+EvtGen(v.2.1.1)"
    assert result["Filter Efficiency"] == 0.01530918
    assert result["Cross Section (nb)"] == 0.000027822


def test_get_metadata_uses_top_of_provenance(mocker):
    """Verify get_metadata uses the top dataset from provenance when requested."""
    # Ensure cache doesn't short-circuit this test
    central_page_mod.cache.clear()

    # Mock provenance chain (DAOD -> AOD -> HITS -> EVNT)
    provenance_chain = [
        "mc23_13p6TeV.123456...DAOD_PHYS.e8514_s4162_r14622_p5855",
        "mc23_13p6TeV.123456...AOD.e8514_s4162_r14622",
        "mc23_13p6TeV.123456...HITS.e8514_s4162",
        "mc23_13p6TeV.123456...EVNT.e8514",
    ]

    mocker.patch("atlas_mcp.central_page.get_provenance", return_value=provenance_chain)

    # Return minimal JSON for metadata
    mocker.patch(
        "atlas_mcp.central_page.run_ami_helper",
        return_value=['{"Physics Short Name": "EVNT_TOP"}'],
    )

    scope = "mc23_13p6TeV"
    dataset_name = (
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9."
        "deriv.DAOD_PHYS.e8514_s4162_r14622_p5855"
    )

    result = get_metadata(scope, dataset_name, use_top_of_provenance=True)

    # Should parse JSON and return dict
    assert isinstance(result, dict)
    assert result["Physics Short Name"] == "EVNT_TOP"


def test_get_provenance_builds_correct_command(mocker):
    """Verify get_provenance constructs the ami-helper command correctly
    and returns a list of dataset names.
    """
    # Ensure cache doesn't short-circuit this test
    central_page_mod.cache.clear()

    # Mock the ami-helper output as simple lines
    mock_output = [
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.deriv.DAOD_PHYS.e8514_s4162_r14622_p5855",
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.recon.AOD.e8514_s4162_r14622",
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.simul.HITS.e8514_s4162",
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.evgen.EVNT.e8514",
    ]

    mocked = mocker.patch(
        "atlas_mcp.central_page.run_ami_helper", return_value=mock_output
    )

    scope = "mc23_13p6TeV"
    dataset_name = (
        "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9."
        "deriv.DAOD_PHYS.e8514_s4162_r14622_p5855"
    )

    result = get_provenance(scope, dataset_name)

    # Verify the command was constructed correctly
    mocked.assert_called_once_with(f"datasets provenance {scope} {dataset_name}")

    # Verify the returned list contains the expected datasets
    assert isinstance(result, list)
    assert len(result) == 4
    assert result[0].endswith("DAOD_PHYS.e8514_s4162_r14622_p5855")
    assert result[1].endswith("AOD.e8514_s4162_r14622")
    assert result[2].endswith("HITS.e8514_s4162")
    assert result[3].endswith("EVNT.e8514")
