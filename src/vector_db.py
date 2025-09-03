"""
Vector Database Manager for Regulatory Compliance System
Handles document storage, retrieval, and citation management.
Enhanced with hybrid search, temporal filtering, and advanced analytics.
"""

import os
import json
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import re
from collections import Counter, defaultdict


@dataclass
class Citation:
    """Structured citation information"""
    filename: str
    page_number: Optional[int] = None
    title: Optional[str] = None
    line_number: Optional[int] = None
    section: Optional[str] = None
    regulation_type: Optional[str] = None  # RBI, FEMA, Companies Act, etc.
    chunk_id: str = ""
    date_created: Optional[datetime] = None
    authority: Optional[str] = None  # Issuing authority
    hierarchy_level: Optional[str] = None  # Act, Rule, Circular, etc.
    
    def to_citation_string(self) -> str:
        """Convert citation to formatted string"""
        parts = [self.filename]
        if self.title:
            parts.append(f"'{self.title}'")
        if self.page_number:
            parts.append(f"Page {self.page_number}")
        if self.line_number:
            parts.append(f"Line {self.line_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        if self.authority:
            parts.append(f"Authority: {self.authority}")
        return ", ".join(parts)


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata"""
    content: str
    citation: Citation
    chunk_id: str
    embedding: Optional[List[float]] = None
    keywords: Optional[List[str]] = None
    importance_score: Optional[float] = None
    
    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = hashlib.md5(
                (self.content + self.citation.filename).encode()
            ).hexdigest()[:16]
        
        # Extract keywords if not provided
        if self.keywords is None:
            self.keywords = self._extract_keywords()
    
    def _extract_keywords(self) -> List[str]:
        """Extract important keywords from content"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b[A-Za-z]{3,}\b', self.content.lower())
        # Filter out common words
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        keywords = [word for word in words if word not in stopwords and len(word) > 3]
        # Return top 10 most frequent keywords
        return [word for word, count in Counter(keywords).most_common(10)]


class VectorDBManager:
    """Enhanced vector database manager with hybrid search and advanced features"""
    
    def __init__(self, db_path: str = "db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        
        # Create collections for different regulation types
        self.collections = {
            "rbi_fema": self._get_or_create_collection("rbi_fema"),
            "companies_act": self._get_or_create_collection("companies_act"),
            "sebi": self._get_or_create_collection("sebi"),
            "customs_trade": self._get_or_create_collection("customs_trade"),
            "general": self._get_or_create_collection("general")
        }
        
        # Initialize keyword indices for hybrid search
        self.keyword_indices = {name: defaultdict(list) for name in self.collections.keys()}
        self._build_keyword_indices()
        
        # Regulatory hierarchy for conflict resolution
        self.hierarchy_weights = {
            "act": 1.0,
            "rules": 0.9,
            "regulations": 0.8,
            "circulars": 0.7,
            "notifications": 0.6,
            "guidelines": 0.5
        }
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection with the specified name"""
        try:
            return self.client.get_collection(
                name=name,
                embedding_function=self.embedding_function
            )
        except:
            return self.client.create_collection(
                name=name,
                embedding_function=self.embedding_function
            )
    
    def add_document_chunks(self, chunks: List[DocumentChunk], collection_name: str = "general"):
        """Add document chunks to the specified collection with enhanced metadata"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk.content)
            metadata = {
                "filename": chunk.citation.filename,
                "page_number": chunk.citation.page_number,
                "title": chunk.citation.title,
                "line_number": chunk.citation.line_number,
                "section": chunk.citation.section,
                "regulation_type": chunk.citation.regulation_type,
                "chunk_id": chunk.chunk_id,
                "keywords": json.dumps(chunk.keywords or []),
                "importance_score": chunk.importance_score or 0.5,
                "date_created": chunk.citation.date_created.isoformat() if chunk.citation.date_created else None,
                "authority": chunk.citation.authority,
                "hierarchy_level": chunk.citation.hierarchy_level
            }
            metadatas.append(metadata)
            ids.append(chunk.chunk_id)
            
            # Update keyword index for hybrid search
            if chunk.keywords:
                for keyword in chunk.keywords:
                    self.keyword_indices[collection_name][keyword.lower()].append(chunk.chunk_id)
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Added {len(chunks)} chunks to {collection_name} collection")
    
    def search_documents(self, query: str, collection_name: str = "general", 
                        n_results: int = 5) -> List[Tuple[str, Citation, float]]:
        """Search for relevant documents and return with citations"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        search_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            citation = Citation(
                filename=metadata["filename"],
                page_number=metadata.get("page_number"),
                title=metadata.get("title"),
                line_number=metadata.get("line_number"),
                section=metadata.get("section"),
                regulation_type=metadata.get("regulation_type"),
                chunk_id=metadata["chunk_id"],
                date_created=datetime.fromisoformat(metadata["date_created"]) if metadata.get("date_created") else None,
                authority=metadata.get("authority"),
                hierarchy_level=metadata.get("hierarchy_level")
            )
            search_results.append((doc, citation, distance))
        
        return search_results
    
    def hybrid_search(self, query: str, collection_name: str = "general", 
                     n_results: int = 10, semantic_weight: float = 0.7) -> List[Dict[str, any]]:
        """Perform hybrid search combining semantic and keyword search"""
        
        # 1. Semantic search
        semantic_results = self.search_documents(query, collection_name, n_results * 2)
        
        # 2. Keyword search
        keyword_results = self._keyword_search(query, collection_name, n_results * 2)
        
        # 3. Combine results with weighted scoring
        combined_results = self._combine_search_results(
            semantic_results, keyword_results, semantic_weight
        )
        
        # 4. Apply hierarchy weighting
        hierarchy_weighted_results = self._apply_hierarchy_weighting(combined_results)
        
        # 5. Sort by combined score and return top results
        hierarchy_weighted_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return hierarchy_weighted_results[:n_results]
    
    def temporal_search(self, query: str, collection_name: str = "general",
                       days_back: int = 365, n_results: int = 5) -> List[Tuple[str, Citation, float]]:
        """Search with temporal filtering for recent documents"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get all results first
        all_results = self.search_documents(query, collection_name, n_results * 3)
        
        # Filter by date
        recent_results = []
        for content, citation, score in all_results:
            if citation.date_created and citation.date_created >= cutoff_date:
                recent_results.append((content, citation, score))
        
        # If not enough recent results, include some older ones
        if len(recent_results) < n_results:
            older_results = [r for r in all_results if r not in recent_results]
            recent_results.extend(older_results[:n_results - len(recent_results)])
        
        return recent_results[:n_results]
    
    def hierarchical_search(self, query: str, collection_name: str = "general",
                           hierarchy_preference: List[str] = None, 
                           n_results: int = 5) -> List[Tuple[str, Citation, float]]:
        """Search with regulatory hierarchy preference"""
        if hierarchy_preference is None:
            hierarchy_preference = ["act", "rules", "regulations", "circulars", "notifications"]
        
        all_results = self.search_documents(query, collection_name, n_results * 3)
        
        # Group by hierarchy level
        hierarchy_groups = defaultdict(list)
        for content, citation, score in all_results:
            level = citation.hierarchy_level or "unknown"
            hierarchy_groups[level.lower()].append((content, citation, score))
        
        # Return results in hierarchy order
        final_results = []
        for level in hierarchy_preference:
            if level in hierarchy_groups:
                # Sort within hierarchy level by relevance score
                hierarchy_groups[level].sort(key=lambda x: x[2])
                final_results.extend(hierarchy_groups[level])
                if len(final_results) >= n_results:
                    break
        
        # Add remaining results if needed
        for level, results in hierarchy_groups.items():
            if level not in hierarchy_preference:
                final_results.extend(results)
            if len(final_results) >= n_results:
                break
        
        return final_results[:n_results]
    
    def cross_regulatory_search(self, query: str, max_collections: int = 3,
                               n_results_per_collection: int = 3) -> Dict[str, List[Tuple[str, Citation, float]]]:
        """Search across multiple regulatory collections"""
        results = {}
        
        for collection_name in self.collections.keys():
            try:
                collection_results = self.search_documents(
                    query, collection_name, n_results_per_collection
                )
                if collection_results:
                    results[collection_name] = collection_results
            except Exception as e:
                print(f"Error searching in {collection_name}: {e}")
        
        return results
    
    def semantic_similarity_search(self, reference_chunk_id: str, collection_name: str = "general",
                                  n_results: int = 5) -> List[Tuple[str, Citation, float]]:
        """Find documents similar to a reference document chunk"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        try:
            # Get the reference document
            ref_result = collection.get(ids=[reference_chunk_id], include=["documents", "embeddings"])
            
            if not ref_result["documents"]:
                return []
            
            ref_document = ref_result["documents"][0]
            
            # Search for similar documents
            similar_results = collection.query(
                query_texts=[ref_document],
                n_results=n_results + 1  # +1 to exclude the reference document itself
            )
            
            search_results = []
            for doc, metadata, distance in zip(
                similar_results["documents"][0],
                similar_results["metadatas"][0], 
                similar_results["distances"][0]
            ):
                # Skip the reference document itself
                if metadata["chunk_id"] == reference_chunk_id:
                    continue
                    
                citation = Citation(
                    filename=metadata["filename"],
                    page_number=metadata.get("page_number"),
                    title=metadata.get("title"),
                    line_number=metadata.get("line_number"),
                    section=metadata.get("section"),
                    regulation_type=metadata.get("regulation_type"),
                    chunk_id=metadata["chunk_id"],
                    date_created=datetime.fromisoformat(metadata["date_created"]) if metadata.get("date_created") else None,
                    authority=metadata.get("authority"),
                    hierarchy_level=metadata.get("hierarchy_level")
                )
                search_results.append((doc, citation, distance))
            
            return search_results[:n_results]
            
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, any]:
        """Get enhanced statistics about stored documents"""
        stats = {}
        total_docs = 0
        
        for name, collection in self.collections.items():
            count = collection.count()
            stats[name] = {
                "document_count": count,
                "keywords_indexed": len(self.keyword_indices[name])
            }
            total_docs += count
        
        stats["total_documents"] = total_docs
        stats["total_collections"] = len(self.collections)
        
        return stats
    
    def get_collection_analytics(self, collection_name: str = "general") -> Dict[str, any]:
        """Get detailed analytics for a specific collection"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        try:
            # Get all documents in the collection
            all_docs = collection.get(include=["metadatas"])
            
            if not all_docs["metadatas"]:
                return {"error": "No documents found in collection"}
            
            analytics = {
                "total_documents": len(all_docs["metadatas"]),
                "regulation_types": Counter(),
                "authorities": Counter(),
                "hierarchy_levels": Counter(),
                "file_types": Counter(),
                "temporal_distribution": defaultdict(int)
            }
            
            for metadata in all_docs["metadatas"]:
                # Count regulation types
                reg_type = metadata.get("regulation_type", "Unknown")
                analytics["regulation_types"][reg_type] += 1
                
                # Count authorities
                authority = metadata.get("authority", "Unknown")
                analytics["authorities"][authority] += 1
                
                # Count hierarchy levels
                hierarchy = metadata.get("hierarchy_level", "Unknown")
                analytics["hierarchy_levels"][hierarchy] += 1
                
                # Count file types
                filename = metadata.get("filename", "")
                file_ext = os.path.splitext(filename)[1].lower() or "Unknown"
                analytics["file_types"][file_ext] += 1
                
                # Temporal distribution (by year)
                date_created = metadata.get("date_created")
                if date_created:
                    try:
                        year = datetime.fromisoformat(date_created).year
                        analytics["temporal_distribution"][year] += 1
                    except:
                        pass
            
            # Convert Counter objects to regular dicts for JSON serialization
            analytics["regulation_types"] = dict(analytics["regulation_types"])
            analytics["authorities"] = dict(analytics["authorities"])
            analytics["hierarchy_levels"] = dict(analytics["hierarchy_levels"])
            analytics["file_types"] = dict(analytics["file_types"])
            analytics["temporal_distribution"] = dict(analytics["temporal_distribution"])
            
            return analytics
            
        except Exception as e:
            return {"error": f"Error generating analytics: {str(e)}"}
    
    def _build_keyword_indices(self):
        """Build keyword indices for all collections"""
        for collection_name, collection in self.collections.items():
            try:
                all_docs = collection.get(include=["metadatas"])
                for metadata in all_docs["metadatas"]:
                    keywords_json = metadata.get("keywords", "[]")
                    try:
                        keywords = json.loads(keywords_json)
                        chunk_id = metadata.get("chunk_id", "")
                        for keyword in keywords:
                            self.keyword_indices[collection_name][keyword.lower()].append(chunk_id)
                    except:
                        pass
            except:
                pass
    
    def _keyword_search(self, query: str, collection_name: str, n_results: int) -> List[Dict[str, any]]:
        """Perform keyword-based search using BM25-like scoring"""
        query_terms = [term.lower() for term in re.findall(r'\b[A-Za-z]{3,}\b', query)]
        keyword_index = self.keyword_indices.get(collection_name, {})
        
        # Score documents based on keyword matches
        doc_scores = defaultdict(float)
        
        for term in query_terms:
            if term in keyword_index:
                # Simple TF-IDF like scoring
                tf = len(keyword_index[term])
                idf = np.log(len(self.collections[collection_name].get()["ids"]) / (tf + 1))
                
                for chunk_id in keyword_index[term]:
                    doc_scores[chunk_id] += idf
        
        # Get top scoring documents
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Retrieve document content and metadata
        results = []
        collection = self.collections[collection_name]
        
        for chunk_id, score in sorted_docs[:n_results]:
            try:
                doc_data = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
                if doc_data["documents"]:
                    results.append({
                        "content": doc_data["documents"][0],
                        "metadata": doc_data["metadatas"][0],
                        "score": score,
                        "search_type": "keyword"
                    })
            except:
                continue
        
        return results
    
    def _combine_search_results(self, semantic_results: List[Tuple[str, Citation, float]], 
                               keyword_results: List[Dict[str, any]], 
                               semantic_weight: float) -> List[Dict[str, any]]:
        """Combine semantic and keyword search results"""
        combined = {}
        
        # Process semantic results
        for content, citation, distance in semantic_results:
            chunk_id = citation.chunk_id
            relevance_score = 1 - distance  # Convert distance to similarity
            combined[chunk_id] = {
                "content": content,
                "citation": citation,
                "semantic_score": relevance_score,
                "keyword_score": 0.0,
                "combined_score": semantic_weight * relevance_score
            }
        
        # Add keyword results
        for result in keyword_results:
            chunk_id = result["metadata"]["chunk_id"]
            keyword_score = result["score"]
            
            if chunk_id in combined:
                combined[chunk_id]["keyword_score"] = keyword_score
                combined[chunk_id]["combined_score"] += (1 - semantic_weight) * keyword_score
            else:
                # Create citation from metadata
                metadata = result["metadata"]
                citation = Citation(
                    filename=metadata["filename"],
                    page_number=metadata.get("page_number"),
                    title=metadata.get("title"),
                    line_number=metadata.get("line_number"),
                    section=metadata.get("section"),
                    regulation_type=metadata.get("regulation_type"),
                    chunk_id=chunk_id,
                    date_created=datetime.fromisoformat(metadata["date_created"]) if metadata.get("date_created") else None,
                    authority=metadata.get("authority"),
                    hierarchy_level=metadata.get("hierarchy_level")
                )
                
                combined[chunk_id] = {
                    "content": result["content"],
                    "citation": citation,
                    "semantic_score": 0.0,
                    "keyword_score": keyword_score,
                    "combined_score": (1 - semantic_weight) * keyword_score
                }
        
        return list(combined.values())
    
    def _apply_hierarchy_weighting(self, results: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Apply regulatory hierarchy weighting to search results"""
        for result in results:
            hierarchy_level = result["citation"].hierarchy_level
            if hierarchy_level:
                weight = self.hierarchy_weights.get(hierarchy_level.lower(), 0.5)
                result["combined_score"] *= weight
        
        return results


class DocumentProcessor:
    """Enhanced document processor with metadata extraction and classification"""
    
    def __init__(self, vector_db: VectorDBManager):
        self.vector_db = vector_db
        
        # Regulatory authority patterns
        self.authority_patterns = {
            "RBI": ["reserve bank", "rbi", "central bank"],
            "SEBI": ["sebi", "securities and exchange board"],
            "MCA": ["ministry of corporate affairs", "mca", "registrar of companies"],
            "CBIC": ["central board of indirect taxes", "cbic", "customs"],
            "IRDAI": ["insurance regulatory", "irdai"]
        }
        
        # Hierarchy patterns
        self.hierarchy_patterns = {
            "act": ["act", "statute", "law"],
            "rules": ["rules", "rule"],
            "regulations": ["regulations", "regulation"],
            "circulars": ["circular", "letter"],
            "notifications": ["notification", "notice"],
            "guidelines": ["guidelines", "guidance"]
        }
    
    def process_text_file(self, file_path: str, regulation_type: str = "general",
                         chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
        """Process a text file into enhanced chunks with metadata extraction"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract document-level metadata
        authority = self._extract_authority(content)
        hierarchy_level = self._extract_hierarchy_level(file_path, content)
        
        chunks = []
        start = 0
        chunk_num = 1
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # Try to break at sentence boundaries
            if end < len(content):
                last_period = content.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                # Calculate importance score based on content
                importance_score = self._calculate_importance_score(chunk_content)
                
                citation = Citation(
                    filename=os.path.basename(file_path),
                    regulation_type=regulation_type,
                    section=f"Chunk {chunk_num}",
                    line_number=content[:start].count('\n') + 1,
                    date_created=datetime.now(),
                    authority=authority,
                    hierarchy_level=hierarchy_level
                )
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    citation=citation,
                    chunk_id=f"{os.path.basename(file_path)}_chunk_{chunk_num}",
                    importance_score=importance_score
                )
                chunks.append(chunk)
                chunk_num += 1
            
            start = end - overlap if end < len(content) else end
        
        return chunks
    
    def process_pdf_file(self, file_path: str, regulation_type: str = "general") -> List[DocumentChunk]:
        """Process a PDF file using PyMuPDF with enhanced metadata"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("PyMuPDF not installed. Install with: pip install pymupdf")
            return []
        
        chunks = []
        
        try:
            pdf_document = fitz.open(file_path)
            full_content = ""
            
            # Extract all text first for document-level analysis
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                full_content += page.get_text() + "\n"
            
            # Extract document-level metadata
            authority = self._extract_authority(full_content)
            hierarchy_level = self._extract_hierarchy_level(file_path, full_content)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                
                if text.strip():
                    # Split page text into smaller chunks
                    page_chunks = self._split_text_into_chunks(text)
                    
                    for chunk_idx, chunk_text in enumerate(page_chunks):
                        importance_score = self._calculate_importance_score(chunk_text)
                        
                        citation = Citation(
                            filename=os.path.basename(file_path),
                            page_number=page_num + 1,
                            regulation_type=regulation_type,
                            section=f"Page {page_num + 1}, Chunk {chunk_idx + 1}",
                            date_created=datetime.now(),
                            authority=authority,
                            hierarchy_level=hierarchy_level
                        )
                        
                        chunk = DocumentChunk(
                            content=chunk_text,
                            citation=citation,
                            chunk_id=f"{os.path.basename(file_path)}_p{page_num + 1}_c{chunk_idx + 1}",
                            importance_score=importance_score
                        )
                        chunks.append(chunk)
            
            pdf_document.close()
            
        except Exception as e:
            print(f"Error processing PDF {file_path}: {str(e)}")
            return []
        
        return chunks
    
    def process_docx_file(self, file_path: str, regulation_type: str = "general") -> List[DocumentChunk]:
        """Process a DOCX file using python-docx with enhanced metadata"""
        try:
            from docx import Document
        except ImportError:
            print("python-docx not installed. Install with: pip install python-docx")
            return []
        
        chunks = []
        
        try:
            doc = Document(file_path)
            
            # Extract text from all paragraphs
            full_text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text)
            
            # Join paragraphs and get full content
            content = '\n'.join(full_text)
            
            # Extract document-level metadata
            authority = self._extract_authority(content)
            hierarchy_level = self._extract_hierarchy_level(file_path, content)
            
            # Split into chunks
            text_chunks = self._split_text_into_chunks(content)
            
            for chunk_idx, chunk_text in enumerate(text_chunks):
                importance_score = self._calculate_importance_score(chunk_text)
                
                citation = Citation(
                    filename=os.path.basename(file_path),
                    regulation_type=regulation_type,
                    section=f"Document Chunk {chunk_idx + 1}",
                    date_created=datetime.now(),
                    authority=authority,
                    hierarchy_level=hierarchy_level
                )
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    citation=citation,
                    chunk_id=f"{os.path.basename(file_path)}_chunk_{chunk_idx + 1}",
                    importance_score=importance_score
                )
                chunks.append(chunk)
                
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {str(e)}")
            return []
        
        return chunks
    
    def _extract_authority(self, content: str) -> Optional[str]:
        """Extract issuing authority from document content"""
        content_lower = content.lower()
        
        for authority, patterns in self.authority_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return authority
        
        return None
    
    def _extract_hierarchy_level(self, file_path: str, content: str) -> Optional[str]:
        """Extract regulatory hierarchy level from filename and content"""
        filename = os.path.basename(file_path).lower()
        content_lower = content.lower()
        
        # Check filename first
        for level, patterns in self.hierarchy_patterns.items():
            for pattern in patterns:
                if pattern in filename or pattern in content_lower[:500]:  # Check first 500 chars
                    return level
        
        return None
    
    def _calculate_importance_score(self, content: str) -> float:
        """Calculate importance score based on content characteristics"""
        score = 0.5  # Base score
        
        content_lower = content.lower()
        
        # Boost score for certain keywords
        important_keywords = [
            "shall", "must", "required", "mandatory", "penalty", "fine",
            "compliance", "violation", "section", "rule", "regulation"
        ]
        
        for keyword in important_keywords:
            if keyword in content_lower:
                score += 0.05
        
        # Boost for regulatory references
        if re.search(r'section \d+|rule \d+|regulation \d+', content_lower):
            score += 0.1
        
        # Boost for dates and deadlines
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2} days|within \d+', content_lower):
            score += 0.05
        
        # Cap the score at 1.0
        return min(score, 1.0)
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append(chunk_text)
            
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def process_file(self, file_path: str, regulation_type: str = "general") -> List[DocumentChunk]:
        """Process a file based on its extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.txt':
            return self.process_text_file(file_path, regulation_type)
        elif file_extension == '.pdf':
            return self.process_pdf_file(file_path, regulation_type)
        elif file_extension in ['.docx', '.doc']:
            return self.process_docx_file(file_path, regulation_type)
        else:
            print(f"Unsupported file type: {file_extension}")
            return []


# Enhanced test function with new features
def test_enhanced_vector_db():
    """Test the enhanced vector database functionality"""
    print("Testing Enhanced Vector Database...")
    
    db = VectorDBManager()
    processor = DocumentProcessor(db)
    
    # Test with enhanced sample data
    sample_chunks = [
        DocumentChunk(
            content="Foreign Direct Investment in India is governed by the Foreign Exchange Management Act (FEMA) 1999. All FDI transactions must be reported to RBI within 30 days of receipt of funds. Non-compliance shall attract penalty under Section 13 of FEMA.",
            citation=Citation(
                filename="fema_guidelines.pdf",
                page_number=15,
                title="FDI Reporting Requirements",
                regulation_type="FEMA",
                section="Chapter 3",
                date_created=datetime(2024, 1, 15),
                authority="RBI",
                hierarchy_level="act"
            ),
            chunk_id="fema_001",
            importance_score=0.9
        ),
        DocumentChunk(
            content="Companies Act 2013 requires all companies to maintain proper books of accounts. The accounts must be audited annually by a qualified chartered accountant. Board resolution is mandatory for major decisions.",
            citation=Citation(
                filename="companies_act_2013.pdf",
                page_number=87,
                title="Books of Accounts",
                regulation_type="Companies Act",
                section="Section 128",
                date_created=datetime(2023, 6, 1),
                authority="MCA",
                hierarchy_level="act"
            ),
            chunk_id="companies_001",
            importance_score=0.8
        ),
        DocumentChunk(
            content="SEBI circular dated March 2024 clarifies that all listed companies must file quarterly results within 45 days of quarter end. Non-compliance will result in penalty and listing suspension.",
            citation=Citation(
                filename="sebi_circular_2024.pdf",
                page_number=2,
                title="Quarterly Filing Requirements",
                regulation_type="SEBI",
                section="Para 2.1",
                date_created=datetime(2024, 3, 10),
                authority="SEBI",
                hierarchy_level="circulars"
            ),
            chunk_id="sebi_001",
            importance_score=0.95
        )
    ]
    
    print("Adding enhanced document chunks...")
    db.add_document_chunks(sample_chunks, "rbi_fema")
    
    print("\n=== Testing Standard Search ===")
    results = db.search_documents("FDI reporting requirements", "rbi_fema")
    for content, citation, score in results:
        print(f"Score: {score:.3f}")
        print(f"Content: {content[:100]}...")
        print(f"Citation: {citation.to_citation_string()}")
        print(f"Authority: {citation.authority}")
        print(f"Hierarchy: {citation.hierarchy_level}")
        print("---")
    
    print("\n=== Testing Hybrid Search ===")
    hybrid_results = db.hybrid_search("penalty for FDI non-compliance", "rbi_fema", n_results=3)
    for result in hybrid_results:
        print(f"Combined Score: {result['combined_score']:.3f}")
        print(f"Semantic: {result['semantic_score']:.3f}, Keyword: {result['keyword_score']:.3f}")
        print(f"Content: {result['content'][:100]}...")
        print(f"Authority: {result['citation'].authority}")
        print("---")
    
    print("\n=== Testing Temporal Search ===")
    recent_results = db.temporal_search("compliance requirements", "rbi_fema", days_back=365)
    for content, citation, score in recent_results:
        print(f"Date: {citation.date_created}")
        print(f"Content: {content[:100]}...")
        print("---")
    
    print("\n=== Testing Hierarchical Search ===")
    hierarchy_results = db.hierarchical_search("reporting requirements", "rbi_fema")
    for content, citation, score in hierarchy_results:
        print(f"Hierarchy: {citation.hierarchy_level}")
        print(f"Content: {content[:100]}...")
        print("---")
    
    print("\n=== Testing Cross-Regulatory Search ===")
    cross_results = db.cross_regulatory_search("compliance penalty")
    for collection, results in cross_results.items():
        print(f"Collection: {collection}")
        for content, citation, score in results:
            print(f"  - {citation.regulation_type}: {content[:80]}...")
    
    print("\n=== Testing Analytics ===")
    stats = db.get_document_stats()
    print(f"Database Stats: {stats}")
    
    analytics = db.get_collection_analytics("rbi_fema")
    print(f"Collection Analytics: {analytics}")
    
    print("\nEnhanced Vector Database test completed!")


def test_vector_db():
    """Legacy test function for backward compatibility"""
    test_enhanced_vector_db()


if __name__ == "__main__":
    test_vector_db()
