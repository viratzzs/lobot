#!/usr/bin/env python3
"""
Simple test script for the regulatory compliance system
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test that all imports work"""
    try:
        print("Testing imports...")
        
        from src.vector_db import VectorDBManager, DocumentProcessor
        print("✅ Vector DB imported successfully")
        
        from src.rag_tools import create_rag_tool, create_document_analysis_tool, create_citation_validator_tool
        print("✅ RAG tools imported successfully")
        
        from src.agents import RegulatoryAgentFactory
        print("✅ Agents imported successfully")
        
        from src.tasks import RegulatoryTaskFactory, TaskOrchestrator
        print("✅ Tasks imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic system functionality"""
    try:
        print("\nTesting basic functionality...")
        
        # Load environment
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not found in environment")
            return False
        
        # Test vector database
        from src.vector_db import VectorDBManager
        vector_db = VectorDBManager()
        print("✅ Vector database initialized")
        
        # Test tool creation
        from src.rag_tools import create_rag_tool
        rag_tool = create_rag_tool(vector_db)
        print("✅ RAG tool created")
        
        # Test simple search (should return no results since DB is empty)
        result = rag_tool("test query", "general", 1)
        print("✅ RAG tool executed")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Regulatory Compliance System")
    print("=" * 50)
    
    if not test_basic_imports():
        return False
        
    if not test_basic_functionality():
        return False
        
    print("\n✅ All tests passed!")
    print("The system is ready to use. Run 'python main.py' to start.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
