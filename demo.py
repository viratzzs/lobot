#!/usr/bin/env python3
"""
Minimal demo of the regulatory compliance system
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_demo():
    """Run a simple demo of the system"""
    print("🏛️  Indian Regulatory Compliance Advisory System - Demo")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY in your .env file")
        print("Copy .env.template to .env and add your OpenAI API key")
        return False
    
    try:
        # Import system components
        from src.vector_db import VectorDBManager
        from src.rag_tools import (
            RegulatoryRAGTool,
            DocumentAnalysisTool,
            CitationValidatorTool
        )
        from src.agents import RegulatoryAgentFactory
        
        print("✅ System components imported successfully")
        
        # Initialize vector database
        vector_db = VectorDBManager()
        print("✅ Vector database initialized")
        
        # Create tool instances
        rag_tool = RegulatoryRAGTool(vector_db)
        document_analyzer = DocumentAnalysisTool(vector_db)
        citation_validator = CitationValidatorTool()
        print("✅ Tools created successfully")
        
        # Create agent factory
        agent_factory = RegulatoryAgentFactory(vector_db)
        print("✅ Agent factory created")
        
        # Create agents
        agents = agent_factory.get_all_agents()
        print(f"✅ Created {len(agents)} specialized agents:")
        for name, agent in agents.items():
            print(f"   - {name}: {agent.role}")
        
        # Test RAG tool
        print("\n🔍 Testing RAG tool with sample query...")
        test_result = rag_tool._run("What are FDI regulations?", "fema", 2)
        print("✅ RAG tool executed (no documents in DB yet, so no results expected)")
        
        # Test document analyzer
        print("\n📄 Testing document analyzer...")
        doc_result = document_analyzer._run("Sample contract content for testing", "general")
        print("✅ Document analyzer executed")
        
        # Test citation validator
        print("\n📋 Testing citation validator...")
        citation_result = citation_validator._run("RBI Circular No. 123, Page 45, Section 3.2")
        print("✅ Citation validator executed")
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Add regulatory documents to the database using option 3 in main.py")
        print("2. Run 'python main.py' to start the interactive system")
        print("3. Try asking regulatory questions")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
