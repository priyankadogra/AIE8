#!/usr/bin/env python3
"""
Test script for Cohere RAG functionality
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_cohere_rag():
    """Test Cohere RAG functionality"""
    
    print("🧪 Testing Cohere RAG Implementation")
    print("=" * 50)
    
    # Prompt for API keys
    print("Please enter your API keys (they won't be saved):")
    openai_key = input("OpenAI API Key: ").strip()
    cohere_key = input("Cohere API Key: ").strip()
    
    if not openai_key:
        print("❌ OpenAI API key is required")
        return False
    
    if not cohere_key:
        print("❌ Cohere API key is required")
        return False
    
    # Set the keys for this session only
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["COHERE_API_KEY"] = cohere_key
    
    print("✅ API keys set for this session")
    
    try:
        # Import and test Cohere RAG
        from app.cohere_rag import CohereRAG
        from config import PDF_DIR
        
        print(f"📁 PDF Directory: {PDF_DIR}")
        
        # Create Cohere RAG instance
        cohere_rag = CohereRAG()
        print("✅ Cohere RAG instance created")
        
        # Test basic functionality
        test_text = "This is a test document with lots of information about school events. Unity Day is coming up on October 22nd, and students should wear orange. The Halloween parade will be on the blacktop at 9:00 AM on October 31st."
        
        print("\n🔧 Testing basic functionality...")
        print(f"Test text length: {len(test_text)} chars")
        
        # Test embedding
        print("\n🔧 Testing embeddings...")
        embeddings = cohere_rag.embed_texts([test_text])
        print(f"Embedding shape: {embeddings.shape}")
        print(f"Embedding dimension: {embeddings.shape[1]}")
        
        # Test indexing (if PDFs exist)
        if Path(PDF_DIR).exists() and list(Path(PDF_DIR).glob("*.pdf")):
            print(f"\n🔧 Testing indexing...")
            result = cohere_rag.index_folder(PDF_DIR)
            print(f"Indexing result: {result}")
            
            # Test search
            print("\n🔧 Testing search...")
            search_results = cohere_rag.search("Unity Day", k=3)
            print(f"Found {len(search_results)} results")
            for i, (chunk, score) in enumerate(search_results, 1):
                print(f"  {i}. Score: {score:.3f}, Source: {chunk['source_pdf']}")
                print(f"     Text: {chunk['text'][:100]}...")
        
        print("\n✅ All Cohere RAG tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cohere_rag()
    if success:
        print("\n🎉 Cohere RAG is ready to use!")
        print("\nNext steps:")
        print("1. Run: uv run streamlit run app/streamlit_app.py")
        print("2. Click 'Build Cohere Index' in the sidebar")
        print("3. Ask questions to test the reranking functionality!")
    else:
        print("\n❌ Please fix the issues above and try again")
        sys.exit(1)

