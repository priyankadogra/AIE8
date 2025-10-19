import os
from pathlib import Path

# API Configuration - Use environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "your-cohere-key-here")

if OPENAI_API_KEY == "your-api-key-here":
    print("⚠️  Warning: Please set OPENAI_API_KEY environment variable")
else:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

if COHERE_API_KEY == "your-cohere-key-here":
    print("⚠️  Warning: Please set COHERE_API_KEY environment variable")
else:
    os.environ["COHERE_API_KEY"] = COHERE_API_KEY

# Data Configuration
PDF_DIR = "data/newsletters"
LOCAL_TZ = "America/Los_Angeles"

# RAG Configuration
COLLECTION_NAME = "scout_newsletters"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Agent Configuration
AGENT_MODEL = "gpt-4o-mini"
AGENT_TEMPERATURE = 0

# Evaluation Configuration
RAGAS_METRICS = ["faithfulness", "response_relevance", "context_precision", "context_recall"]