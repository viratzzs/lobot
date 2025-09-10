"""
Custom RAG Tool for Regulatory Compliance
Interfaces with vector database and ensures proper citations
Enhanced with legal reasoning capabilities
"""

from typing import List, Dict, Any, Optional
from crewai.tools import BaseTool
import json

from .faiss_db import VectorDBManager, Citation


class RegulatoryRAGTool(BaseTool):
    """
    Custom RAG tool that searches regulatory documents with mandatory citations
    """
    name: str = "regulatory_rag_search"
    description: str = (
        "Search regulatory documents for relevant context with mandatory citations. "
        "Args: query (str), regulation_type (str, optional), max_results (int, optional)"
    )
    
    def __init__(self, vector_db: VectorDBManager, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'vector_db', vector_db)
        # Set the name and description as instance attributes for CrewAI compatibility
        self.name = "regulatory_rag_search"
        self.description = (
            "Search regulatory documents for relevant context with mandatory citations. "
            "Args: query (str), regulation_type (str, optional), max_results (int, optional)"
        )
    
    def _run(self, query: str, regulation_type: str = "general", max_results: int = 5) -> str:
        """
        Search regulatory documents for relevant context with mandatory citations
        """
        try:
            # Determine collection to search
            collection_map = {
                "rbi": "rbi_fema",
                "fema": "rbi_fema",
                "companies": "companies_act",
                "sebi": "sebi",
                "customs": "customs_trade",
                "trade": "customs_trade",
                "general": "general"
            }
            
            collection_name = collection_map.get(regulation_type.lower(), "general")
            
            # Search the vector database
            search_results = self.vector_db.search_documents(
                query=query,
                collection_name=collection_name,
                n_results=max_results
            )
            
            if not search_results:
                return json.dumps({
                    "status": "no_results",
                    "message": "No relevant documents found for the query",
                    "query": query,
                    "regulation_type": regulation_type
                })
            
            # Format results with citations
            formatted_results = []
            citations = []
            
            for content, citation, score in search_results:
                formatted_results.append({
                    "content": content,
                    "citation": citation.to_citation_string(),
                    "relevance_score": round(1 - score, 3),  # Convert distance to relevance
                    "source_type": citation.regulation_type or "Unknown"
                })
                
                citations.append(citation.to_citation_string())
            
            # Create summary
            sources = set()
            for result in formatted_results:
                sources.add(result.get("source_type", "Unknown"))
            
            context_summary = f"Found {len(formatted_results)} relevant documents for '{query}' from sources: {', '.join(sources)}. "
            context_summary += f"Highest relevance score: {max(r['relevance_score'] for r in formatted_results):.3f}"
            
            response = {
                "status": "success",
                "query": query,
                "regulation_type": regulation_type,
                "context_summary": context_summary,
                "results": formatted_results,
                "citations": citations,
                "total_results": len(formatted_results)
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Error searching documents: {str(e)}",
                "query": query,
                "regulation_type": regulation_type
            }
            return json.dumps(error_response)


class DocumentAnalysisTool(BaseTool):
    """
    Tool for analyzing document compliance against regulations
    """
    name: str = "document_compliance_analyzer"
    description: str = (
        "Analyze a document for regulatory compliance issues. "
        "Args: document_content (str), regulation_type (str, optional)"
    )
    
    def __init__(self, vector_db: VectorDBManager, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'vector_db', vector_db)
        # Set the name and description as instance attributes for CrewAI compatibility
        self.name = "document_compliance_analyzer"
        self.description = (
            "Analyze a document for regulatory compliance issues. "
            "Args: document_content (str), regulation_type (str, optional)"
        )
    
    def _run(self, document_content: str, regulation_type: str = "general") -> str:
        """
        Analyze a document for regulatory compliance issues
        """
        try:
            # This would implement document analysis logic
            # For now, return a placeholder response
            analysis_sections = document_content.split('\n\n')
            
            findings = []
            for i, section in enumerate(analysis_sections[:3]):  # Analyze first 3 sections
                if len(section.strip()) > 50:  # Only analyze substantial sections
                    # Search for relevant regulations
                    search_results = self.vector_db.search_documents(
                        query=section[:200],  # First 200 chars as query
                        collection_name=regulation_type,
                        n_results=2
                    )
                    
                    if search_results:
                        findings.append({
                            "section_number": i + 1,
                            "section_preview": section[:100] + "...",
                            "relevant_regulations": [
                                {
                                    "regulation": citation.to_citation_string(),
                                    "relevance": round(1 - score, 3)
                                }
                                for content, citation, score in search_results
                            ]
                        })
            
            response = {
                "status": "success",
                "document_length": len(document_content),
                "sections_analyzed": len(analysis_sections),
                "compliance_findings": findings,
                "regulation_type": regulation_type
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Error analyzing document: {str(e)}",
                "regulation_type": regulation_type
            }
            return json.dumps(error_response)


class CitationValidatorTool(BaseTool):
    """
    Tool for validating and formatting citations
    """
    name: str = "citation_validator"
    description: str = (
        "Validate and format citations for regulatory documents. "
        "Args: citation_text (str)"
    )
    
    def __init__(self):
        super().__init__()
        # Set the name and description as instance attributes for CrewAI compatibility
        self.name = "citation_validator"
        self.description = (
            "Validate and format citations for regulatory documents. "
            "Args: citation_text (str)"
        )
    
    def _run(self, citation_text: str) -> str:
        """
        Validate and format citations for regulatory documents
        """
        try:
            # Basic citation validation logic
            required_elements = ["filename", "page", "section", "title"]
            found_elements = []
            
            citation_lower = citation_text.lower()
            
            if any(ext in citation_lower for ext in [".pdf", ".doc", ".txt"]):
                found_elements.append("filename")
            
            if "page" in citation_lower:
                found_elements.append("page")
            
            if "section" in citation_lower or "chapter" in citation_lower:
                found_elements.append("section")
            
            if "'" in citation_text and "'" in citation_text:
                found_elements.append("title")
            
            completeness_score = len(found_elements) / len(required_elements)
            
            response = {
                "status": "success",
                "citation": citation_text,
                "found_elements": found_elements,
                "missing_elements": [elem for elem in required_elements if elem not in found_elements],
                "completeness_score": round(completeness_score, 2),
                "is_valid": completeness_score >= 0.5
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Error validating citation: {str(e)}",
                "citation": citation_text
            }
            return json.dumps(error_response)


class LegalReasoningTool(BaseTool):
    """
    Tool for applying formal legal reasoning to regulatory scenarios
    """
    name: str = "legal_reasoning_analyzer"
    description: str = (
        "Apply formal legal reasoning to analyze regulatory scenarios. "
        "Args: scenario (str), analysis_type (str, optional)"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Import here to avoid circular imports
        from .legal_reasoning import LegalReasoningEngine, ComplianceWorkflowEngine
        object.__setattr__(self, 'reasoning_engine', LegalReasoningEngine())
        object.__setattr__(self, 'workflow_engine', ComplianceWorkflowEngine())
        
        # Set the name and description as instance attributes for CrewAI compatibility
        self.name = "legal_reasoning_analyzer"
        self.description = (
            "Apply formal legal reasoning to analyze regulatory scenarios. "
            "Args: scenario (str), analysis_type (str, optional)"
        )
    
    def _run(self, scenario: str, analysis_type: str = "basic") -> str:
        """
        Apply legal reasoning to analyze a regulatory scenario
        """
        try:
            # Parse scenario if it's a JSON string
            if isinstance(scenario, str):
                try:
                    scenario_dict = json.loads(scenario)
                except json.JSONDecodeError:
                    # If not JSON, treat as text description
                    scenario_dict = {"description": scenario}
            else:
                scenario_dict = scenario
            
            if analysis_type == "comprehensive":
                # Use comprehensive workflow engine
                analysis_result = self.workflow_engine.comprehensive_compliance_check(scenario_dict)
            else:
                # Use basic reasoning engine
                analysis_result = self.reasoning_engine.analyze_compliance(scenario_dict)
            
            # Format the response
            response = {
                "status": "success",
                "analysis_type": analysis_type,
                "scenario": scenario_dict.get("description", str(scenario_dict)[:100]),
                "legal_analysis": analysis_result,
                "summary": self._create_analysis_summary(analysis_result)
            }
            
            return json.dumps(response, indent=2, default=str)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Error in legal reasoning: {str(e)}",
                "scenario": str(scenario)[:100],
                "analysis_type": analysis_type
            }
            return json.dumps(error_response)
    
    def _create_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the legal analysis"""
        summary = {}
        
        # Basic reasoning engine results
        if "facts" in analysis_result:
            summary["identified_facts"] = len(analysis_result.get("facts", []))
            summary["applicable_rules"] = len(analysis_result.get("applicable_rules", []))
            summary["conflicts_found"] = len(analysis_result.get("conflicts", []))
            summary["conclusions"] = len(analysis_result.get("conclusions", []))
            summary["confidence_score"] = analysis_result.get("confidence_score", 0.0)
        
        # Comprehensive workflow results
        if "compliance_score" in analysis_result:
            summary["overall_compliance_score"] = analysis_result.get("compliance_score", 0.0)
            
            # Risk analysis summary
            if "risk_assessment" in analysis_result:
                risks = analysis_result["risk_assessment"].get("risks", [])
                summary["total_risks"] = len(risks)
                summary["high_risks"] = len([r for r in risks if r.get("severity") == "high"])
        
        return summary
