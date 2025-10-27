# pip install langgraph langchain-core mcp
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

# ---- Define the shared state ----
class State(TypedDict):
    fact: str

# ---- LangGraph node that calls the MCP tool ----
async def get_cat_fact() -> str:
    server = StdioServerParameters(command="python", args=["catfact_mcp_server.py"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            res = await session.call_tool("cat_fact", {})
            for content in res.content:
                if getattr(content, "text", None):
                    return content.text
                if getattr(content, "data", None):
                    return content.data
    return "No fact returned."

def fetch_fact(state: State) -> State:
    fact = asyncio.run(get_cat_fact())
    return {"fact": fact}

def print_fact(state: State) -> State:
    print("🐈 Random Cat Fact:")
    print(state["fact"])
    return state

# ---- Build the graph ----
graph = StateGraph(State)
graph.add_node("fetch_fact", fetch_fact)
graph.add_node("print_fact", print_fact)
graph.add_edge(START, "fetch_fact")
graph.add_edge("fetch_fact", "print_fact")
graph.add_edge("print_fact", END)

app = graph.compile()

# ---- Run the LangGraph app ----
if __name__ == "__main__":
    app.invoke({"fact": ""})
