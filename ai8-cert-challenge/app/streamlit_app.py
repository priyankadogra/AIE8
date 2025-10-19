import streamlit as st
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# API Key Input (set this first)
st.sidebar.title("🔑 API Configuration")
api_key = st.sidebar.text_input(
    "OpenAI API Key", 
    type="password",
    help="Enter your OpenAI API key to use the assistant"
)

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
    st.sidebar.success("✅ API Key set!")
    
    # Now import other modules (only after API key is set)
           from config import PDF_DIR
           from app.agent import ask, ensure_prepared, agent_executor
           from app.rag import index_health_check
           from app.cohere_rag import cohere_health_check
           from app.tools import build_cohere_index_tool, answer_query_cohere_tool
    
    # Data Management Section
    st.sidebar.title("📁 Data Management")
    if st.sidebar.button("🔄 Prepare Data"):
        with st.spinner("Preparing data..."):
            ensure_prepared(PDF_DIR)
        st.success("✅ Data prepared successfully!")
    
    # Cohere Index
    if st.sidebar.button("🧠 Build Cohere Index"):
        with st.spinner("Building Cohere compressed index..."):
            result = build_cohere_index_tool(PDF_DIR)
        st.success(f"✅ Cohere index built! {result}")
    
    # Health Check
    st.sidebar.title("🏥 Health Checks")
    if st.sidebar.button("📊 Check Regular Index"):
        health_status = index_health_check()
        st.sidebar.write(health_status)
    
    if st.sidebar.button("🧠 Check Cohere Index"):
        health_status = cohere_health_check()
        st.sidebar.write(health_status)
    
    # Main Chat Interface
    st.title("🏫 School Events Assistant")
    st.write("Ask questions about school events and activities!")
    
    # Retrieval Method Selection
    st.sidebar.title("🔧 Retrieval Settings")
    use_cohere = st.sidebar.checkbox("Use Cohere Compression", help="Enable Cohere-compressed retrieval for better context quality")
    
    if use_cohere:
        st.info("🧠 Using Cohere-compressed retrieval for enhanced context quality")
    else:
        st.info("📊 Using standard retrieval")
    
    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about school events..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if use_cohere:
                    # Use Cohere-compressed retrieval
                    result = answer_query_cohere_tool(prompt)
                    response = result["answer"]
                    # Add retrieval method info
                    if result.get("retrieval_method"):
                        response += f"\n\n*Retrieved using: {result['retrieval_method']}*"
                else:
                    # Use standard retrieval
                    response = ask(prompt, PDF_DIR)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.sidebar.warning("⚠️ Please enter your OpenAI API key")
    st.info("Enter your API key in the sidebar to start using the assistant")