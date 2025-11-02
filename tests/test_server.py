import json
from atlas_mcp.central_page import CentralPageAddress, CentralPageScope
from atlas_mcp import server


def test_get_allowed_scopes(mocker):
    """Test get_allowed_scopes returns a valid JSON list of scopes."""
    # Create mock data
    mock_scopes = [
        CentralPageScope(scope="mc23_13p6TeV", description="Run 3 MC"),
        CentralPageScope(scope="mc21_13TeV", description="Run 2 MC"),
        CentralPageScope(scope="mc20_13TeV", description="Run 2 MC (older)"),
    ]

    # Mock the central_page.get_allowed_scopes function
    mocker.patch("atlas_mcp.central_page.get_allowed_scopes", return_value=mock_scopes)

    # Call the server function
    result = server.get_allowed_scopes()

    # Verify the result is valid JSON
    parsed = json.loads(result)

    # Verify it's a list
    assert isinstance(parsed, list)

    # Verify the correct number of scopes
    assert len(parsed) == 3

    # Verify the content - should be just the scope strings
    assert parsed[0]["scope"] == "mc23_13p6TeV"
    assert parsed[0]["description"] == "Run 3 MC"


def test_get_addresses_for_keyword_baseline_only(mocker):
    """Test get_addresses_for_keyword with baseline_only=True (default)."""
    # Create mock data with mix of Baseline, Systematic, and Alternative
    mock_addresses = [
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Baseline", "Pythia8"),
        ),
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Systematic", "Sherpa2214"),
        ),
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Alternative", "Herwig72"),
        ),
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Baseline", "Sherpa"),
        ),
    ]

    # Mock the central_page.get_address_for_keyword function
    mocker.patch(
        "atlas_mcp.central_page.get_address_for_keyword",
        return_value=mock_addresses,
    )

    # Call the server function with baseline_only=True (default)
    result = server.get_addresses_for_keyword("mc23_13p6TeV", "Dijet")

    # Verify the result is valid JSON
    parsed = json.loads(result)

    # Should only return Baseline addresses (2 out of 4)
    assert len(parsed) == 2

    # Verify each result can be deserialized back to CentralPageAddress
    for item in parsed:
        addr = CentralPageAddress(**item)
        assert addr.scope == "mc23_13p6TeV"
        assert addr.hash_tags[2] == "Baseline"
        assert "Dijet" in addr.hash_tags


def test_get_addresses_for_keyword_all_types(mocker):
    """Test get_addresses_for_keyword with baseline_only=False."""
    # Create mock data with mix of Baseline, Systematic, and Alternative
    mock_addresses = [
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Baseline", "Pythia8"),
        ),
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Systematic", "Sherpa2214"),
        ),
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Alternative", "Herwig72"),
        ),
        CentralPageAddress(
            scope="mc23_13p6TeV",
            hash_tags=("JetPhoton", "Dijet", "Baseline", "Sherpa"),
        ),
    ]

    # Mock the central_page.get_address_for_keyword function
    mocker.patch(
        "atlas_mcp.central_page.get_address_for_keyword",
        return_value=mock_addresses,
    )

    # Call the server function with baseline_only=False
    result = server.get_addresses_for_keyword(
        "mc23_13p6TeV", "Dijet", baseline_only=False
    )

    # Verify the result is valid JSON
    parsed = json.loads(result)

    # Should return all addresses (4 out of 4)
    assert len(parsed) == 4

    # Verify each result can be deserialized back to CentralPageAddress
    types_found = set()
    for item in parsed:
        addr = CentralPageAddress(**item)
        assert addr.scope == "mc23_13p6TeV"
        assert "Dijet" in addr.hash_tags
        types_found.add(addr.hash_tags[2])

    # Verify we got all three types
    assert types_found == {"Baseline", "Systematic", "Alternative"}


def test_get_metadata_tool(mocker):
    """Server get_metadata tool returns JSON and passes through flag."""
    mocked = mocker.patch(
        "atlas_mcp.central_page.get_metadata",
        return_value={
            "Physics Comment": "NULL",
            "Physics Short Name": "Py8EG_A14NNPDF23LO_jj_JZ9incl",
        },
    )

    scope = "mc23_13p6TeV"
    dataset = "mc23_13p6TeV.123456.Pythia8...DAOD_PHYS.e8514_s4162_r14622_p5855"
    result = server.get_metadata(scope, dataset, use_top_of_provenance=True)

    parsed = json.loads(result)
    assert parsed["Physics Comment"] == "NULL"
    assert parsed["Physics Short Name"] == "Py8EG_A14NNPDF23LO_jj_JZ9incl"

    mocked.assert_called_once_with(
        scope, dataset, use_top_of_provenance=True
    )
