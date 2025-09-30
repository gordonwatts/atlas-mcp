from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register(mcp: FastMCP) -> None:
    @mcp.prompt(title="Greet")
    def greet(name: str = "Gordon") -> list[base.Message]:
        return [
            # base.SystemMessage("You are a succinct assistant."),
            base.UserMessage(f"Say hi to {name} in one sentence."),
        ]
