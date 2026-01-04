import json
from typing import List

import typer
from ami_helper.utils import ensure_and_import
from fastmcp import FastMCP

import atlas_mcp.central_page as cp

# Make sure installation has completed
ensure_and_import("pyAMI_atlas")

# Create the fast mcp server
mcp = FastMCP("atlas_standard_MonteCarlo_catalog")


@mcp.tool()
def get_allowed_scopes(ignore_cache: bool = False) -> str:
    """Returns a list of allowed scopes/data-taking-periods
    for the CentralPage MC Sample catalog.

    Returns json.
    """
    return json.dumps([s.model_dump() for s in cp.get_allowed_scopes()])


@mcp.tool()
def get_addresses_for_keyword(
    scope: str, keyword: str, baseline_only: bool = True, ignore_cache: bool = False
) -> str:
    """Searches the PMG group's Standard Model Monte Carlo datasets for a hashtag that
    contains `keyword`. Only hashtags in `scope` are considered. Full 4-tuples hashtags
    are returned.

    These tuples can be passed to other methods to return datasets associated with them.
    The hashtags specify categories of datasets. They often have easily understandable english
    names and so make for a great place to start a Standard Model dataset search.

    The third returned tag indicates whether the dataset is 'Baseline', 'Systematic',
    or 'Alternative'. By default only hashtag combinations with `Baseline` are returned.
    If one needs samples that are alternative for for systematic comparisons, change the
    `baseline_only` parameter.

    Returns json
    """
    addresses = cp.get_address_for_keyword(scope, keyword, ignore_cache=ignore_cache)
    if baseline_only:
        addresses = [addr for addr in addresses if addr.hash_tags[2] == "Baseline"]
    return json.dumps([addr.to_dict() for addr in addresses])


@mcp.tool()
def get_evtgen_for_address(
    scope: str, hashtags: List[str], ignore_cache: bool = False
) -> str:
    """Returns a list of event generator (evtgen) sample names for a given CentralPageAddress.
    These will be rucio dataset names, for datasets that contains the output of
    the MC generation step. All samples for this address are returned. Parse the sample
    names to find the ones required. Sample names often contain decay channels, etc.

    Returns json
    """
    if len(hashtags) != 4:
        raise ValueError("hashtags must be a list of 4 strings")

    cpa = cp.CentralPageHashAddress(scope=scope, hash_tags=tuple(hashtags))
    samples = cp.get_evtgen_for_address(cpa, ignore_cache=ignore_cache)  # type: ignore
    return json.dumps(samples)


@mcp.tool()
def get_samples_for_run(
    scope: str, run_number: str, data_tier: str, ignore_cache: bool = False
) -> str:
    """Returns a list of rucio dataset names of a particular data_tier for a given EVTGEN sample
    and scope.

    evtgen_sample should be a valid rucio ID, with EVNT as the data tier.

    data_tier should be "PHYSLITE", "PHYS", "DAOD_LLP1", etc. Default to PHYSLITE unless
    otherwise requested.

    Returns the datasets and the ATLAS MC Campaigns. Those without a MC campaign should
    probably be ignored.

    Returns json
    """
    results = cp.get_samples_for_run(
        scope, int(run_number), data_tier, ignore_cache=ignore_cache  # type: ignore
    )
    return json.dumps(results)


@mcp.tool()
def get_metadata(
    scope: str,
    dataset_name: str,
    use_top_of_provenance: bool = False,
    ignore_cache: bool = False,
) -> str:
    """Returns metadata for a given dataset as JSON. This includes cross section,
    generator filter efficiency, physics short name, etc.

    If ``use_top_of_provenance`` is True, the server will first resolve the
    provenance chain and fetch metadata for the top (last) dataset, typically
    the EVNT.

    Returns json
    """
    md = cp.get_metadata(
        scope,
        dataset_name,
        use_top_of_provenance=use_top_of_provenance,
        ignore_cache=ignore_cache,  # type: ignore
    )
    return json.dumps(md)


@mcp.tool()
def get_dataset_with_name(
    scope: str,
    search_str: str,
    is_central_page: bool,
    ignore_cache: bool = False,
) -> str:
    """Searches AMI for all EVNT tier datasets whose name contains `search_str`.

    If you know you are looking for a standard model dataset, ``is_central_page``
    should be set to ``True``. If you are looking for something exotic, then
    ``is_central_page`` should be ``False``.

    If ``is_central_page`` is ``True``, only datasets with PMG / central-page
    hashtags are returned. If ``is_central_page`` is ``False``, all matching
    EVNT datasets whose name contains ``search_str`` are returned, regardless
    of PMG / central-page hashtags.
    Returns json string
    """
    ds = cp.get_dataset_with_name(
        scope, search_str, is_central_page, ignore_cache=ignore_cache  # type: ignore
    )
    return json.dumps(ds)


app = typer.Typer(help="ATLAS MCP Server")


@app.command()
def main(
    transport: str = typer.Option(
        "stdio",
        "--transport",
        help="Transport mode: stdio (default) or http",
    ),
    port: int = typer.Option(
        8080,
        "--port",
        help="Port for HTTP transport (default: 8080)",
    ),
) -> None:
    """Run the ATLAS MCP server with the specified transport."""
    if transport not in ["stdio", "http"]:
        typer.echo(f"Error: Invalid transport '{transport}'. Choose 'stdio' or 'http'.")
        raise typer.Exit(1)

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", port=port, host="localhost")


if __name__ == "__main__":
    app()
