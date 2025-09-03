"""
Main Regulatory Compliance System
Orchestrates the multi-agent workflow for regulatory queries
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from crewai import Crew, Process
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.vector_db import VectorDBManager, DocumentProcessor
from src.rag_tools import (
    RegulatoryRAGTool, DocumentAnalysisTool, CitationValidatorTool,
    create_rag_tool_dict, create_document_analysis_tool_dict, create_citation_validator_tool_dict
)
from src.agents import RegulatoryAgentFactory
from src.tasks import RegulatoryTaskFactory, TaskOrchestrator


class RegulatoryComplianceSystem:
    """Main system orchestrating regulatory compliance queries"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        
        # Initialize vector database
        self.vector_db = VectorDBManager()
        
        # Initialize agent factory with vector database
        self.agent_factory = RegulatoryAgentFactory(self.vector_db)
        
        # Initialize agents
        self.agents = self.agent_factory.get_all_agents()
        
        # Initialize task management
        self.task_factory = RegulatoryTaskFactory(self.agents)
        self.task_orchestrator = TaskOrchestrator(self.task_factory)
        
        # System statistics
        self.query_count = 0
        self.session_start = datetime.now()
        
        print("✅ Regulatory Compliance System initialized successfully")
        print(f"📊 Database stats: {self.vector_db.get_document_stats()}")
    
    def process_query(self, user_query: str, query_type: str = "auto") -> Dict[str, Any]:
        """Process a regulatory query through the multi-agent system"""
        
        self.query_count += 1
        query_start_time = datetime.now()
        
        print(f"\n🔍 Processing Query #{self.query_count}: {user_query[:100]}...")
        
        try:
            # Determine query type if auto
            if query_type == "auto":
                query_type = self.task_orchestrator.determine_query_type(user_query)
            
            print(f"📋 Query type: {query_type}")
            
            # Create workflow
            tasks = self.task_orchestrator.create_workflow(user_query)
            tasks = self.task_orchestrator.add_task_dependencies(tasks)
            
            # Create crew
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                process=Process.sequential,
                verbose=1,
                memory=True,
                planning=True
            )
            
            # Execute the crew
            print("🚀 Executing multi-agent workflow...")
            result = crew.kickoff(inputs={'query': user_query})
            
            # Process results
            processing_time = (datetime.now() - query_start_time).total_seconds()
            
            response = {
                "query": user_query,
                "query_type": query_type,
                "query_number": self.query_count,
                "processing_time": processing_time,
                "result": str(result),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            print(f"✅ Query processed successfully in {processing_time:.2f} seconds")
            return response
            
        except Exception as e:
            error_response = {
                "query": user_query,
                "query_number": self.query_count,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
            print(f"❌ Error processing query: {str(e)}")
            return error_response
    
    def analyze_document(self, document_content: str, 
                        regulation_type: str = "general") -> Dict[str, Any]:
        """Analyze a document for regulatory compliance"""
        
        print(f"\n📄 Analyzing document for {regulation_type} compliance...")
        
        try:
            # Create document analysis task
            analysis_task = self.task_factory.create_document_analysis_task(
                document_content, regulation_type
            )
            
            synthesis_task = self.task_factory.create_synthesis_task([])
            synthesis_task.context = [analysis_task]
            
            # Create crew for document analysis
            crew = Crew(
                agents=[self.agents['document_analyzer'], self.agents['synthesis']],
                tasks=[analysis_task, synthesis_task],
                process=Process.sequential,
                verbose=1
            )
            
            # Execute analysis
            result = crew.kickoff(inputs={'document_content': document_content})
            
            response = {
                "document_length": len(document_content),
                "regulation_type": regulation_type,
                "analysis_result": str(result),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            print("✅ Document analysis completed successfully")
            return response
            
        except Exception as e:
            error_response = {
                "document_length": len(document_content),
                "regulation_type": regulation_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
            print(f"❌ Error analyzing document: {str(e)}")
            return error_response
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics"""
        return {
            "session_start": self.session_start.isoformat(),
            "queries_processed": self.query_count,
            "database_stats": self.vector_db.get_document_stats(),
            "available_agents": list(self.agents.keys()),
            "system_status": "operational"
        }
    
    def add_documents_to_database(self, file_paths: List[str], 
                                 regulation_types: List[str] = None) -> Dict[str, Any]:
        """Add documents to the vector database"""
        
        if regulation_types is None:
            regulation_types = ["general"] * len(file_paths)
        
        if len(file_paths) != len(regulation_types):
            raise ValueError("Number of file paths must match number of regulation types")
        
        processor = DocumentProcessor(self.vector_db)
        results = []
        
        for file_path, reg_type in zip(file_paths, regulation_types):
            try:
                if file_path.endswith('.txt'):
                    chunks = processor.process_text_file(file_path, reg_type)
                elif file_path.endswith('.pdf'):
                    chunks = processor.process_pdf_file(file_path, reg_type)
                else:
                    print(f"⚠️ Unsupported file type: {file_path}")
                    continue
                
                # Add to database
                collection_map = {
                    "rbi": "rbi_fema",
                    "fema": "rbi_fema",
                    "companies": "companies_act",
                    "sebi": "sebi",
                    "customs": "customs_trade",
                    "trade": "customs_trade"
                }
                
                collection = collection_map.get(reg_type.lower(), "general")
                self.vector_db.add_document_chunks(chunks, collection)
                
                results.append({
                    "file_path": file_path,
                    "regulation_type": reg_type,
                    "chunks_added": len(chunks),
                    "collection": collection,
                    "status": "success"
                })
                
                print(f"✅ Added {len(chunks)} chunks from {file_path} to {collection}")
                
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "regulation_type": reg_type,
                    "error": str(e),
                    "status": "error"
                })
                print(f"❌ Error processing {file_path}: {str(e)}")
        
        return {
            "results": results,
            "total_files_processed": len([r for r in results if r["status"] == "success"]),
            "total_chunks_added": sum(r.get("chunks_added", 0) for r in results),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main function for command-line interface"""
    
    print("🏛️  Indian Regulatory Compliance Advisory System")
    print("=" * 60)
    print("Specialized AI agents for regulatory compliance queries")
    print("Available domains: RBI/FEMA, Companies Act, SEBI, Customs/Trade")
    print("=" * 60)
    
    try:
        # Initialize system
        system = RegulatoryComplianceSystem()
        
        # Interactive mode
        while True:
            print("\nOptions:")
            print("1. Ask a regulatory question")
            print("2. Analyze a document")
            print("3. Add documents to database")
            print("4. System status")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                query = input("\nEnter your regulatory query: ").strip()
                if query:
                    result = system.process_query(query)
                    print("\n" + "=" * 60)
                    print("📋 REGULATORY ADVISORY RESPONSE")
                    print("=" * 60)
                    if result["status"] == "success":
                        print(result["result"])
                    else:
                        print(f"Error: {result['error']}")
                    print("=" * 60)
                
            elif choice == "2":
                doc_content = input("\nEnter document content (or 'file:path' to read from file): ").strip()
                if doc_content.startswith("file:"):
                    file_path = doc_content[5:]
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            doc_content = f.read()
                    except Exception as e:
                        print(f"Error reading file: {e}")
                        continue
                
                reg_type = input("Enter regulation type (rbi/fema/companies/sebi/customs/general): ").strip()
                if not reg_type:
                    reg_type = "general"
                
                result = system.analyze_document(doc_content, reg_type)
                print("\n" + "=" * 60)
                print("📄 DOCUMENT COMPLIANCE ANALYSIS")
                print("=" * 60)
                if result["status"] == "success":
                    print(result["analysis_result"])
                else:
                    print(f"Error: {result['error']}")
                print("=" * 60)
                
            elif choice == "3":
                file_paths = input("Enter file paths (comma-separated): ").strip().split(',')
                file_paths = [fp.strip() for fp in file_paths if fp.strip()]
                
                reg_types = input("Enter regulation types (comma-separated, or press Enter for 'general'): ").strip()
                if reg_types:
                    reg_types = [rt.strip() for rt in reg_types.split(',')]
                else:
                    reg_types = ["general"] * len(file_paths)
                
                result = system.add_documents_to_database(file_paths, reg_types)
                print(f"\nProcessed {result['total_files_processed']} files")
                print(f"Added {result['total_chunks_added']} chunks to database")
                
            elif choice == "4":
                status = system.get_system_status()
                print(f"\nSystem Status: {status['system_status']}")
                print(f"Session started: {status['session_start']}")
                print(f"Queries processed: {status['queries_processed']}")
                print(f"Database stats: {status['database_stats']}")
                print(f"Available agents: {', '.join(status['available_agents'])}")
                
            elif choice == "5":
                print("\nThank you for using the Regulatory Compliance System!")
                break
                
            else:
                print("Invalid choice. Please try again.")
                
    except KeyboardInterrupt:
        print("\n\nSystem interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\nSystem error: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()


def test_legal_reasoning_integration():
    """Test function to verify legal reasoning integration"""
    print("Testing Legal Reasoning Integration...")
    
    try:
        # Test the legal reasoning tool directly
        from src.rag_tools import LegalReasoningTool
        reasoning_tool = LegalReasoningTool()
        
        # Test scenario
        test_scenario = {
            "description": "A foreign company wants to invest in an Indian IT company",
            "details": "Investment amount is $50 million for 49% stake"
        }
        
        result = reasoning_tool._run(json.dumps(test_scenario), "basic")
        print("Legal Reasoning Tool Test Result:")
        print(result)
        
        # Test agent with reasoning capability
        system = RegulatoryComplianceSystem()
        router_agent = system.agents['router']
        
        print(f"\nRouter agent tools: {[tool.__class__.__name__ for tool in router_agent.tools]}")
        print("✅ Legal reasoning integration successful!")
        
    except Exception as e:
        print(f"❌ Legal reasoning integration failed: {str(e)}")
        import traceback
        traceback.print_exc()