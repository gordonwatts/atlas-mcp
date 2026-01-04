from atlas_mcp.central_page import (
    get_allowed_scopes,
    get_address_for_keyword,
)
from ami_helper.datamodel import CentralPageHashAddress


def test_get_allowed_scopes():
    scopes = get_allowed_scopes()
    assert len(scopes) >= 2
    assert all(
        hasattr(scope, "scope") and hasattr(scope, "description") for scope in scopes
    )
    assert any(scope.scope == "mc20_13TeV" for scope in scopes)
    assert any(scope.scope == "mc23_13p6TeV" for scope in scopes)


def test_central_page_address_hashable():
    """Test that CentralPageAddress is hashable (required for caching)."""
    # Create two identical instances
    addr1 = CentralPageHashAddress(scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad"))
    addr2 = CentralPageHashAddress(scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad"))

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


def test_get_address_for_keyword_single_keyword(mocker):
    """Test get_address_for_keyword with a single keyword string."""
    # Mock ami.find_hashtag to return partial addresses
    mock_partial_addr1 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", None, None, None)
    )
    mock_partial_addr2 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbarMET", None, None, None)
    )

    # Mock ami.find_hashtag_tuples to return complete addresses
    mock_complete_addr1 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad", "Baseline", "PowhegPythia")
    )
    mock_complete_addr2 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", "dilep", "Baseline", "PowhegPythia")
    )
    mock_complete_addr3 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbarMET", "allhad", "Baseline", "Sherpa")
    )

    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag",
        return_value=[mock_partial_addr1, mock_partial_addr2],
    )

    # Mock find_hashtag_tuples to return different complete addresses for each partial
    def mock_find_tuples(partial_addr):
        if partial_addr.hash_tags[0] == "ttbar":
            return [mock_complete_addr1, mock_complete_addr2]
        else:  # ttbarMET
            return [mock_complete_addr3]

    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag_tuples", side_effect=mock_find_tuples
    )

    result = get_address_for_keyword("mc23_13p6TeV", "ttbar")

    # Should return all three complete addresses since they all contain "ttbar"
    assert len(result) == 3
    assert mock_complete_addr1 in result
    assert mock_complete_addr2 in result
    assert mock_complete_addr3 in result


def test_get_address_for_keyword_multiple_keywords(mocker):
    """Test get_address_for_keyword with multiple keywords as a list."""
    mock_partial_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", None, None, None)
    )

    # Create addresses with different hashtags
    mock_complete_addr1 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad", "Baseline", "PowhegPythia")
    )
    mock_complete_addr2 = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", "dilep", "Baseline", "Sherpa")
    )
    mock_complete_addr3 = CentralPageHashAddress(
        scope="mc23_13p6TeV",
        hash_tags=("ttbar", "allhad", "Systematic", "PowhegHerwig"),
    )

    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag", return_value=[mock_partial_addr]
    )
    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag_tuples",
        return_value=[mock_complete_addr1, mock_complete_addr2, mock_complete_addr3],
    )

    # Search for ttbar AND allhad
    result = get_address_for_keyword("mc23_13p6TeV", ["ttbar", "allhad"])

    # Only addresses containing both "ttbar" and "allhad" should be returned
    assert len(result) == 2
    assert mock_complete_addr1 in result
    assert mock_complete_addr3 in result
    assert mock_complete_addr2 not in result  # doesn't contain "allhad"


def test_get_address_for_keyword_case_insensitive(mocker):
    """Test that keyword matching is case-insensitive."""
    mock_partial_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("TTbar", None, None, None)
    )

    mock_complete_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("TTbar", "AllHad", "Baseline", "PowhegPythia")
    )

    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag", return_value=[mock_partial_addr]
    )
    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag_tuples",
        return_value=[mock_complete_addr],
    )

    # Search with lowercase when tags are mixed case
    result = get_address_for_keyword("mc23_13p6TeV", "ttbar")

    assert len(result) == 1
    assert mock_complete_addr in result


def test_get_address_for_keyword_no_matches(mocker):
    """Test get_address_for_keyword when no addresses match the keywords."""
    mock_partial_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", None, None, None)
    )

    mock_complete_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", "allhad", "Baseline", "PowhegPythia")
    )

    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag", return_value=[mock_partial_addr]
    )
    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag_tuples",
        return_value=[mock_complete_addr],
    )

    # Search for keywords that won't match
    result = get_address_for_keyword("mc23_13p6TeV", ["ttbar", "nonexistent"])

    assert len(result) == 0


def test_get_address_for_keyword_empty_partial_list(mocker):
    """Test get_address_for_keyword when ami.find_hashtag returns no results."""
    mocker.patch("atlas_mcp.central_page.ami.find_hashtag", return_value=[])

    result = get_address_for_keyword("mc23_13p6TeV", "nonexistent")

    assert len(result) == 0


def test_get_address_for_keyword_filters_none_hashtags(mocker):
    """Test that filtering correctly handles None values in hashtags."""
    mock_partial_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", None, None, None)
    )

    # Create address with None in the middle
    mock_complete_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", None, "Baseline", "PowhegPythia")
    )

    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag", return_value=[mock_partial_addr]
    )
    mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag_tuples",
        return_value=[mock_complete_addr],
    )

    # Search should not crash on None values
    result = get_address_for_keyword("mc23_13p6TeV", "ttbar")

    assert len(result) == 1
    assert mock_complete_addr in result


def test_get_address_for_keyword_uses_first_keyword_for_ami_search(mocker):
    """Test that only the first keyword is used for the AMI search."""
    mock_partial_addr = CentralPageHashAddress(
        scope="mc23_13p6TeV", hash_tags=("ttbar", None, None, None)
    )

    mocker_find_hashtag = mocker.patch(
        "atlas_mcp.central_page.ami.find_hashtag", return_value=[mock_partial_addr]
    )
    mocker.patch("atlas_mcp.central_page.ami.find_hashtag_tuples", return_value=[])

    get_address_for_keyword("mc23_13p6TeV", ["ttbar", "allhad", "baseline"])

    # Verify find_hashtag was called only with the first keyword
    mocker_find_hashtag.assert_called_once_with("mc23_13p6TeV", "ttbar")


# @pytest.mark.parametrize(
#     "derivation, expected_flag",
#     [
#         ("PHYS", "DAOD_PHYS"),
#         ("PHYSLITE", "DAOD_PHYSLITE"),
#         ("DAOD_LLP1", "DAOD_LLP1"),
#     ],
# )
# def test_get_samples_for_run_builds_correct_command(mocker, derivation, expected_flag):
#     """Verify mapping and delegation for get_samples_for_run.

#     Ensures derivation maps to the expected flag and the ami-helper
#     command is constructed correctly.
#     """
#     # Use ignore_cache=True to avoid cache hits in tests.

#     # Mock with valid JSON output
#     mock_json_output = ['{"datasets": ["ds1", "ds2"]}']

#     mocked = mocker.patch(
#         "atlas_mcp.central_page.run_ami_helper", return_value=mock_json_output
#     )

#     scope = "mc23_13p6TeV"
#     run_number = "00473423"

#     result = get_samples_for_run(scope, run_number, derivation, ignore_cache=True)

#     # Returns parsed JSON
#     assert result == {"datasets": ["ds1", "ds2"]}

#     # Ensures we built the proper command
#     mocked.assert_called_once_with(
#         f"datasets with-datatype {scope} {run_number} {expected_flag} -o json"
#     )


# @pytest.mark.parametrize("bad_derivation", ["INVALID", "AOD"])
# def test_get_samples_for_run_invalid_derivation_raises(bad_derivation):
#     """Invalid derivations (incl. 'AOD') currently raise RuntimeError.

#     Note: Docstring lists 'AOD' as an example, but current code
#     does not accept it. This documents current behavior.
#     """
#     # Use ignore_cache=True to avoid cache hits in tests.

#     with pytest.raises(RuntimeError) as excinfo:
#         get_samples_for_run(
#             "mc23_13p6TeV", "00473423", bad_derivation, ignore_cache=True
#         )

#     assert "Invalid `derivation`" in str(excinfo.value)


# def test_get_metadata_builds_correct_command(mocker):
#     """Verify get_metadata constructs the ami-helper command correctly
#     and parses JSON output.
#     """
#     # Use ignore_cache=True to avoid cache hits in tests.

#     # Mock the ami-helper output as JSON
#     mock_json_output = [
#         "{",
#         '  "Physics Comment": "NULL",',
#         '  "Physics Short Name": "Py8EG_A14NNPDF23LO_jj_JZ9incl",',
#         '  "Generator Name": "Pythia8(v.308)+EvtGen(v.2.1.1)",',
#         '  "Filter Efficiency": 0.01530918,',
#         '  "Cross Section (nb)": 0.000027822',
#         "}",
#     ]

#     mocked = mocker.patch(
#         "atlas_mcp.central_page.run_ami_helper", return_value=mock_json_output
#     )

#     scope = "mc23_13p6TeV"
#     dataset_name = (
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9."
#         "deriv.DAOD_PHYS.e8514_s4162_r14622_p5855"
#     )

#     result = get_metadata(scope, dataset_name, ignore_cache=True)

#     # Verify the command was constructed correctly
#     mocked.assert_called_once_with(f"datasets metadata {scope} {dataset_name} -o json")

#     # Verify the returned dictionary contains the expected fields
#     assert isinstance(result, dict)
#     assert result["Physics Comment"] == "NULL"
#     assert result["Physics Short Name"] == "Py8EG_A14NNPDF23LO_jj_JZ9incl"
#     assert result["Generator Name"] == "Pythia8(v.308)+EvtGen(v.2.1.1)"
#     assert result["Filter Efficiency"] == 0.01530918
#     assert result["Cross Section (nb)"] == 0.000027822


# def test_get_metadata_uses_top_of_provenance(mocker):
#     """Verify get_metadata uses the top dataset from provenance when requested."""
#     # Use ignore_cache=True to avoid cache hits in tests.

#     # Mock provenance chain (DAOD -> AOD -> HITS -> EVNT)
#     provenance_chain = [
#         "mc23_13p6TeV.123456...DAOD_PHYS.e8514_s4162_r14622_p5855",
#         "mc23_13p6TeV.123456...AOD.e8514_s4162_r14622",
#         "mc23_13p6TeV.123456...HITS.e8514_s4162",
#         "mc23_13p6TeV.123456...EVNT.e8514",
#     ]

#     mocker.patch("atlas_mcp.central_page.get_provenance", return_value=provenance_chain)

#     # Return minimal JSON for metadata
#     mocker.patch(
#         "atlas_mcp.central_page.run_ami_helper",
#         return_value=['{"Physics Short Name": "EVNT_TOP"}'],
#     )

#     scope = "mc23_13p6TeV"
#     dataset_name = (
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9."
#         "deriv.DAOD_PHYS.e8514_s4162_r14622_p5855"
#     )

#     result = get_metadata(
#         scope, dataset_name, use_top_of_provenance=True, ignore_cache=True
#     )

#     # Should parse JSON and return dict
#     assert isinstance(result, dict)
#     assert result["Physics Short Name"] == "EVNT_TOP"


# def test_get_provenance_builds_correct_command(mocker):
#     """Verify get_provenance constructs the ami-helper command correctly
#     and returns a list of dataset names.
#     """
#     # Use ignore_cache=True to avoid cache hits in tests.

#     # Mock the ami-helper output as simple lines
#     mock_output = [
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.deriv.DAOD_PHYS.e8514_s4162_r14622_p5855",
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.recon.AOD.e8514_s4162_r14622",
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.simul.HITS.e8514_s4162",
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9.evgen.EVNT.e8514",
#     ]

#     mocked = mocker.patch(
#         "atlas_mcp.central_page.run_ami_helper", return_value=mock_output
#     )

#     scope = "mc23_13p6TeV"
#     dataset_name = (
#         "mc23_13p6TeV.123456.Pythia8_A14NNPDF23LO_jj_JZ9."
#         "deriv.DAOD_PHYS.e8514_s4162_r14622_p5855"
#     )

#     result = get_provenance(scope, dataset_name, ignore_cache=True)

#     # Verify the command was constructed correctly
#     mocked.assert_called_once_with(f"datasets provenance {scope} {dataset_name}")

#     # Verify the returned list contains the expected datasets
#     assert isinstance(result, list)
#     assert len(result) == 4
#     assert result[0].endswith("DAOD_PHYS.e8514_s4162_r14622_p5855")
#     assert result[1].endswith("AOD.e8514_s4162_r14622")
#     assert result[2].endswith("HITS.e8514_s4162")
#     assert result[3].endswith("EVNT.e8514")
