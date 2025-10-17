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
    
    # Data Management Section
    st.sidebar.title("📁 Data Management")
    if st.sidebar.button("🔄 Prepare Data"):
        with st.spinner("Preparing data..."):
            ensure_prepared(PDF_DIR)
        st.success("✅ Data prepared successfully!")
    
    # Health Check
    if st.sidebar.button("🏥 Check Index Health"):
        health_status = index_health_check()
        st.sidebar.write(health_status)
    
    # Main Chat Interface
    st.title("🏫 School Events Assistant")
    st.write("Ask questions about school events and activities!")
    
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
                response = ask(prompt, PDF_DIR)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.sidebar.warning("⚠️ Please enter your OpenAI API key")
    st.info("Enter your API key in the sidebar to start using the assistant")