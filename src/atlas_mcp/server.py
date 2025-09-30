from mcp.server.fastmcp import FastMCP
from atlas_mcp import tools as biz
from atlas_mcp import prompts as myprompts

mcp = FastMCP("myServer")


# Expose tools with structured output based on type hints/pydantic:
@mcp.tool()
def echo(msg: str) -> biz.Echo:
    return biz.echo(msg)


@mcp.tool()
def stats(data: list[float]) -> biz.Stat:
    return biz.compute_stats(data)


# Optional: register prompts so they appear as /mcp.myServer.greet
myprompts.register(mcp)


def main() -> None:
    # stdio is the default; this runs the server loop
    mcp.run()
