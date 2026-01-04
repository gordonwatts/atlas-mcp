import json
import re

import pytest

from atlas_mcp import server

pytestmark = pytest.mark.integration

SCOPE = "mc23_13p6TeV"
KEYWORD = "ttbar"


@pytest.fixture(scope="module")
def central_page_address() -> dict:
    result = server.get_addresses_for_keyword.fn(
        SCOPE, KEYWORD, baseline_only=True, ignore_cache=True
    )
    parsed = json.loads(result)
    assert parsed
    return parsed[0]


@pytest.fixture(scope="module")
def evtgen_sample(central_page_address: dict) -> str:
    result = server.get_evtgen_for_address.fn(
        SCOPE, central_page_address["hash_tags"], ignore_cache=True
    )
    samples = json.loads(result)
    assert samples
    return samples[0]


def test_get_allowed_scopes_integration():
    result = server.get_allowed_scopes.fn(ignore_cache=True)
    parsed = json.loads(result)
    assert any(scope["scope"] == SCOPE for scope in parsed)


def test_get_addresses_for_keyword_integration(central_page_address: dict):
    assert central_page_address["scope"] == SCOPE
    assert len(central_page_address["hash_tags"]) == 4
    assert central_page_address["hash_tags"][2] == "Baseline"


def test_get_evtgen_for_address_integration(evtgen_sample: str):
    assert evtgen_sample.startswith(f"{SCOPE}.")
    assert ".EVNT" in evtgen_sample


def test_get_samples_for_run_integration(evtgen_sample: str):
    dsid = evtgen_sample.split(".")[1]
    assert re.fullmatch(r"\d+", dsid)
    result = server.get_samples_for_run.fn(
        SCOPE, dsid, data_tier="PHYSLITE", ignore_cache=True
    )
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_get_metadata_integration(evtgen_sample: str):
    result = server.get_metadata.fn(
        SCOPE,
        evtgen_sample,
        use_top_of_provenance=True,
        ignore_cache=True,
    )
    parsed = json.loads(result)
    assert isinstance(parsed, dict)
    assert parsed


def test_get_dataset_with_name_integration():
    result = server.get_dataset_with_name.fn(
        SCOPE, KEYWORD, is_central_page=True, ignore_cache=True
    )
    parsed = json.loads(result)
    assert parsed
    dataset_match = parsed[0]
    assert dataset_match["name"].startswith(f"{SCOPE}.")
    assert dataset_match["HashTag 1"]
    assert dataset_match["HashTag 2"]
    assert dataset_match["HashTag 3"]
    assert dataset_match["HashTag 4"]
