from typing import List

from mcp.server.fastmcp import FastMCP

import atlas_mcp.central_page as cp
from atlas_mcp import prompts as myprompts

mcp = FastMCP("atlas_standard_MonteCarlo_catalog")


@mcp.tool()
def get_allowed_scopes() -> List[cp.CentralPageScope]:
    """Returns a list of allowed scopes/data-taking-periods
    for the CentralPage MC Sample catalog."""
    return cp.get_allowed_scopes()


@mcp.tool()
def get_addresses_for_keyword(scope: str, keyword: str) -> List[cp.CentralPageAddress]:
    """Returns a list of CentralPageAddress for the given scope. This is a good set of keywords
    for a category search for standard ATLAS background datasets. Only addresses that contain the
    keyword are returned.
    """
    addresses = cp.get_address_for_keyword(scope, keyword)
    return addresses


@mcp.tool()
def get_evtgen_for_address(cpa: cp.CentralPageAddress) -> List[str]:
    """Returns a list of event generator (evtgen) sample names for a given CentralPageAddress.
    These will be rucio dataset names, for datasets that contains the output of
    the MC generation step. All samples for this address are returned. Parse the sample
    names to find the ones required.
    """
    samples = cp.get_evtgen_for_address(cpa)
    return samples


@mcp.tool()
def get_samples_for_evtgen(
    scope: str, evtgen_sample: str, data_tier: str
) -> List[cp.DIDInfo]:
    """Returns a list of rucio dataset names of a particular data_tier for a given EVTGEN sample
    and scope.

    evtgen_sample should be a valid rucio ID, with EVNT as the data tier.

    data_tier should be "PHYSLITE", "PHYS", "DAOD_LLP1", etc. Default to PHYSLITE unless
    otherwise requested.
    """
    results = cp.get_samples_for_evtgen(scope, evtgen_sample, data_tier)
    return results


# Optional: register prompts so they appear as /mcp.myServer.greet
myprompts.register(mcp)


def main() -> None:
    # stdio is the default; this runs the server loop
    mcp.run()


if __name__ == "__main__":
    main()
