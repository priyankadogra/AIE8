#!/usr/bin/env python3
"""
Test script to verify the organized structure works
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test config
        import config
        print("✅ config imported successfully")
        
        # Test data processing
        from app.data_processing import ExtractedEvent, pdf_to_text
        print("✅ data_processing imported successfully")
        
        # Test RAG
        from app.rag import rag_search, build_rag_index_from_folder
        print("✅ rag imported successfully")
        
        # Test tools
        from app.tools import ensure_prepared, AGENT_STATE
        print("✅ tools imported successfully")
        
        # Test agent
        from app.agent import ask, agent_executor
        print("✅ agent imported successfully")
        
        print("\n🎉 All imports successful! Your organized structure is working.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_config():
    """Test configuration values"""
    try:
        import config
        print(f"\nTesting configuration...")
        print(f"PDF_DIR: {config.PDF_DIR}")
        print(f"COLLECTION_NAME: {config.COLLECTION_NAME}")
        print(f"AGENT_MODEL: {config.AGENT_MODEL}")
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing organized structure...\n")
    
    # Test imports
    imports_ok = test_imports()
    
    # Test config
    config_ok = test_config()
    
    if imports_ok and config_ok:
        print("\n🎉 All tests passed! Your project is properly organized.")
        print("\nNext steps:")
        print("1. Run: streamlit run app/streamlit_app.py")
        print("2. Set up RAGAS evaluation")
        print("3. Test the agent system")
    else:
        print("\n❌ Some tests failed. Check the errors above.")