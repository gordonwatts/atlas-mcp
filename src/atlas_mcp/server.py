from typing import List

from mcp.server.fastmcp import FastMCP

import atlas_mcp.central_page as cp
from atlas_mcp import prompts as myprompts
from atlas_mcp import tools as biz

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


# Optional: register prompts so they appear as /mcp.myServer.greet
myprompts.register(mcp)


def main() -> None:
    # stdio is the default; this runs the server loop
    print("hi")
    mcp.run()


if __name__ == "__main__":
    main()
