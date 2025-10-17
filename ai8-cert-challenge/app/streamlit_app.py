import streamlit as st
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import config
from config import PDF_DIR

# Import our agent
from app.agent import ask, ensure_prepared, agent_executor
from app.rag import index_health_check

# Set page config
st.set_page_config(
    page_title="School Events Assistant",
    page_icon="🏫",
    layout="wide"
)

# Title
st.title("🏫 School Events Assistant")
st.markdown("Ask questions about school events and activities!")

# Sidebar for data preparation
with st.sidebar:
    st.header("📁 Data Management")
    
    if st.button("🔄 Prepare Data"):
        with st.spinner("Preparing data..."):
            ensure_prepared(PDF_DIR)
            st.success("Data prepared successfully!")
    
    if st.button("🔍 Check Index Health"):
        with st.spinner("Checking index..."):
            index_health_check()
            st.success("Index health checked!")

# Main chat interface
st.header("💬 Chat with the Assistant")

# Initialize chat history
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

# Clear chat button
if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()