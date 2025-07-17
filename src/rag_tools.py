"""
Custom RAG Tool for Regulatory Compliance
Interfaces with vector database and ensures proper citations
"""

from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import json

from .vector_db import VectorDBManager, Citation


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


# Legacy dictionary functions for backward compatibility
def create_rag_tool_dict(vector_db: VectorDBManager) -> Dict[str, Any]:
    """Create a RAG tool dictionary for CrewAI agents"""
    
    def regulatory_rag_search(query: str, regulation_type: str = "general", max_results: int = 5) -> str:
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
            search_results = vector_db.search_documents(
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
    
    return {
        "name": "regulatory_rag_search",
        "description": "Search regulatory documents for relevant context with mandatory citations",
        "func": regulatory_rag_search
    }


def create_document_analysis_tool_dict(vector_db: VectorDBManager) -> Dict[str, Any]:
    """Create a document analysis tool dictionary for CrewAI agents"""
    
    def document_compliance_analyzer(document_content: str, regulation_type: str = "general") -> str:
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
                    search_results = vector_db.search_documents(
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
    
    return {
        "name": "document_compliance_analyzer",
        "description": "Analyze a document for regulatory compliance issues",
        "func": document_compliance_analyzer
    }


def create_citation_validator_tool_dict() -> Dict[str, Any]:
    """Create a citation validator tool dictionary for CrewAI agents"""
    
    def citation_validator(citation_text: str) -> str:
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
    
    return {
        "name": "citation_validator",
        "description": "Validate and format citations for regulatory documents",
        "func": citation_validator
    }
