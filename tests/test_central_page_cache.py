from atlas_mcp import central_page as central_page_mod
import importlib


def test_get_hash_tags_caching(mocker, monkeypatch, tmp_path):
    # Set a temporary cache location via env var and reload module so the module
    # cache uses a per-test directory (avoids touching persistent cache)
    monkeypatch.setenv("ATLAS_MCP_CACHE_DIR", str(tmp_path / "cache"))
    importlib.reload(central_page_mod)

    # Mock run_centralpage to return string output
    mock = mocker.patch(
        "atlas_mcp.central_page.run_centralpage", return_value="a\nb\nc\n"
    )

    # Construct CentralPageAddress from the reloaded module to match the cached type
    cpa = central_page_mod.CentralPageAddress(scope="mc20_13TeV", hash_tags=[])

    first = central_page_mod.get_hash_tags(cpa)
    second = central_page_mod.get_hash_tags(cpa)

    # Under caching, the underlying run_centralpage should have been called once
    assert mock.call_count == 1
    assert first == ["a", "b", "c"]
    assert second == first
