import streamlit as st
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules at the top level
from config import PDF_DIR
from app.agent import ask, agent_executor
from app.tools import ensure_prepared
from app.rag import index_health_check, build_rag_index_from_folder

# API Key Input (set this first)
st.sidebar.title("🔑 API Configuration")
openai_key = st.sidebar.text_input(
    "OpenAI API Key", 
    type="password",
    help="Enter your OpenAI API key to use the assistant"
)

cohere_key = st.sidebar.text_input(
    "Cohere API Key", 
    type="password",
    help="Enter your Cohere API key for enhanced retrieval with reranking"
)

if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
    st.sidebar.success("✅ OpenAI API Key set!")
    
if cohere_key:
    os.environ["COHERE_API_KEY"] = cohere_key
    st.sidebar.success("✅ Cohere API Key set!")

if openai_key:
    # Data Management Section
    st.sidebar.title("📁 Data Management")
    if st.sidebar.button("🔄 Prepare Data"):
        with st.spinner("Preparing data..."):
            ensure_prepared(PDF_DIR)
        st.success("✅ Data prepared successfully!")
    
    # Build Index (unified)
    if st.sidebar.button("🧠 Build RAG Index"):
        with st.spinner("Building RAG index..."):
            result = build_rag_index_from_folder(PDF_DIR)
        st.success(f"✅ RAG index built! {result}")
    
    # Health Check
    st.sidebar.title("🏥 Health Checks")
    if st.sidebar.button("📊 Check RAG Index"):
        health_status = index_health_check()
        st.sidebar.write(health_status)
    
    # Main Chat Interface
    st.title("🏫 Scout - School Events Assistant")
    st.write("Ask questions about school events and activities!")
        
    # Retrieval Method Selection
    st.sidebar.title("🔧 Retrieval Settings")
    use_reranking = st.sidebar.checkbox("Use Cohere Reranking", help="Enable Cohere reranking for better retrieval quality")
    
    if use_reranking:
        if not cohere_key:
            st.warning("⚠️ Cohere API key required for reranking")
            use_reranking = False
        else:
            st.info("🧠 Using Cohere reranking for enhanced retrieval quality")
    else:
        st.info("📊 Using standard vector similarity retrieval")
    
    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask Scout about school events..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Use unified RAG with optional reranking
                response = ask(prompt, PDF_DIR, use_reranking=use_reranking)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.sidebar.warning("⚠️ Please enter your OpenAI API key")
    st.info("Enter your API keys in the sidebar to start using Scout")