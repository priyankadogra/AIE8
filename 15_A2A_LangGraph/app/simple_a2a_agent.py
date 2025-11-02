"""Simple LangGraph agent that uses A2A protocol to communicate with the agent server.

This is the simplest possible LangGraph that demonstrates how to use A2A protocol
to call another agent through the A2A client.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Annotated, TypedDict, List
from uuid import uuid4

import httpx

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, SendStreamingMessageRequest

load_dotenv()

logger = logging.getLogger(__name__)


class SimpleAgentState(TypedDict):
    """Simple state for the agent - just messages."""
    messages: Annotated[List, add_messages]


# Global A2A client (initialized once)
_a2a_client: A2AClient | None = None
_httpx_client: httpx.AsyncClient | None = None


async def get_a2a_client(base_url: str = "http://localhost:10000") -> A2AClient:
    """Get or create the A2A client."""
    global _a2a_client, _httpx_client
    
    if _a2a_client is None:
        # Create httpx client with longer timeout for LLM responses
        _httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        
        # Resolve agent card
        resolver = A2ACardResolver(
            httpx_client=_httpx_client,
            base_url=base_url,
        )
        
        agent_card = await resolver.get_agent_card()
        logger.info(f"Connected to agent: {agent_card.name}")
        
        # Create A2A client
        _a2a_client = A2AClient(
            httpx_client=_httpx_client,
            agent_card=agent_card
        )
    
    return _a2a_client


async def call_a2a_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Call the A2A agent server with the user's query."""
    # Get the last user message
    user_message = state["messages"][-1]
    if isinstance(user_message, HumanMessage):
        user_query = user_message.content
    else:
        # If it's not a HumanMessage, try to get content anyway
        user_query = getattr(user_message, "content", str(user_message))
    
    logger.info(f"Calling A2A agent with query: {user_query}")
    
    try:
        # Get A2A client
        client = await get_a2a_client()
        
        # Prepare message payload
        send_message_payload: Dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": user_query}],
                "message_id": uuid4().hex,
            },
        }
        
        # Use streaming for more reliable response handling
        streaming_request = SendStreamingMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        # Collect streaming response
        response_text = ""
        async for chunk in client.send_message_streaming(streaming_request):
            # Try to extract text from chunk
            chunk_dict = chunk.model_dump(mode='json', exclude_none=True)
            
            # Look for message content in various possible structures
            if 'result' in chunk_dict:
                result = chunk_dict['result']
                if 'message' in result and 'parts' in result['message']:
                    for part in result['message']['parts']:
                        if 'text' in part:
                            response_text += part['text'] + "\n"
                elif 'content' in result:
                    response_text += result['content'] + "\n"
            elif 'message' in chunk_dict:
                msg = chunk_dict['message']
                if 'parts' in msg:
                    for part in msg['parts']:
                        if 'text' in part:
                            response_text += part['text'] + "\n"
                elif 'content' in msg:
                    response_text += msg['content'] + "\n"
            elif 'text' in chunk_dict:
                response_text += chunk_dict['text'] + "\n"
        
        response_text = response_text.strip()
        
        if not response_text:
            # Fallback to non-streaming request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            response = await client.send_message(request)
            
            # Try to extract from response - check for error first
            if hasattr(response, 'root') and hasattr(response.root, 'error'):
                # Error response
                error_msg = f"Error: {response.root.error.message if hasattr(response.root.error, 'message') else str(response.root.error)}"
                logger.error(f"A2A agent error: {error_msg}")
                return {"messages": [AIMessage(content=error_msg)]}
            
            # Extract text directly from the response
            response_dict = response.model_dump(mode='json', exclude_none=True)
            
            # Try to extract text directly from the response structure
            # Check root.result.message.parts structure
            if 'root' in response_dict and 'result' in response_dict.get('root', {}):
                result = response_dict['root']['result']
                if 'message' in result and 'parts' in result.get('message', {}):
                    text_parts = []
                    for part in result['message']['parts']:
                        if isinstance(part, dict) and 'text' in part:
                            text_parts.append(part['text'])
                    if text_parts:
                        response_text = '\n'.join(text_parts)
                elif 'message' in result:
                    msg = result['message']
                    if isinstance(msg, dict) and 'content' in msg:
                        response_text = msg['content']
                    elif isinstance(msg, str):
                        response_text = msg
                
                # If still no text, check if result has text directly
                if not response_text and 'text' in result:
                    response_text = result['text']
                elif not response_text and 'content' in result:
                    response_text = result['content']
            
            # If we still don't have text, return the JSON structure as fallback
            if not response_text:
                response_text = json.dumps(response_dict, indent=2)
                logger.warning("Could not extract text from response, returning JSON structure")
        
        if not response_text:
            response_text = "No response received from A2A agent."
        
        logger.info(f"A2A agent responded (first 100 chars): {str(response_text)[:100]}...")
        
        # Return as AIMessage - text should already be extracted
        return {"messages": [AIMessage(content=response_text)]}
        
    except Exception as e:
        error_msg = f"Error calling A2A agent: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"messages": [AIMessage(content=error_msg)]}


def build_simple_a2a_graph(base_url: str = "http://localhost:10000"):
    """Build the simplest possible LangGraph that uses A2A protocol.
    
    Graph structure:
    - Entry: user query
    - Node: call_a2a_agent (calls the A2A agent server)
    - Exit: return response
    """
    graph = StateGraph(SimpleAgentState)
    
    # Add nodes
    graph.add_node("call_a2a", call_a2a_agent)
    
    # Set entry point
    graph.set_entry_point("call_a2a")
    
    # Flow: call_a2a -> END
    graph.add_edge("call_a2a", END)
    
    # Compile the graph
    return graph.compile()


async def run_example():
    """Run a simple example of the A2A agent."""
    print("🚀 Starting Simple A2A LangGraph Agent\n")
    
    # Build the graph
    graph = build_simple_a2a_graph()
    
    # Example query
    query = "What are the latest developments in AI?"
    
    print(f"📝 User query: {query}\n")
    
    # Run the graph
    config = {"configurable": {"thread_id": "simple-agent-1"}}
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        config
    )
    
    # Print the result
    print("✅ Response from A2A agent:")
    print("-" * 50)
    for message in result["messages"]:
        if isinstance(message, AIMessage):
            print(message.content)
    print("-" * 50)
    
    # Clean up
    if _httpx_client:
        await _httpx_client.aclose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_example())

