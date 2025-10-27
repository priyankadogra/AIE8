# pip install langgraph langchain-core mcp
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def main():
    # 1. Point to your MCP server file
    server = StdioServerParameters(
        command="python", args=["catfact_mcp_server.py"]
    )

    # 2. Connect over stdio
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 3. Call the tool
            print("🐾 Calling MCP tool: cat_fact ...")
            res = await session.call_tool("cat_fact", {})

            # 4. Parse the result
            for content in res.content:
                if getattr(content, "text", None):
                    print("\n😺 Cat Fact:")
                    print(content.text)
                elif getattr(content, "data", None):
                    print("\n😺 Cat Fact:")
                    print(content.data)

if __name__ == "__main__":
    asyncio.run(main())
