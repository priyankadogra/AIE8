import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CatFacts-MCP")

@mcp.tool()
def cat_fact() -> str:
    """Return a random cat fact (no auth required)."""
    res = requests.get("https://catfact.ninja/fact", timeout=5)
    res.raise_for_status()
    return res.json()["fact"]

if __name__ == "__main__":
    mcp.run()  # automatically uses stdio
