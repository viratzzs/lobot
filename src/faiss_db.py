import os
import pickle
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import faiss
import re
from collections import Counter, defaultdict


@dataclass
class Citation:
    filename: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    regulation_type: Optional[str] = None
    chunk_id: str = ""
    authority: Optional[str] = None
    
    def to_citation_string(self) -> str:
        parts = [self.filename]
        if self.page_number:
            parts.append(f"Page {self.page_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        if self.authority:
            parts.append(f"Authority: {self.authority}")
        return ", ".join(parts)


@dataclass
class DocumentChunk:
    content: str
    citation: Citation
    chunk_id: str = ""
    
    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = hashlib.md5(
                (self.content + self.citation.filename).encode()
            ).hexdigest()[:16]


class VectorDBManager:
    def __init__(self, db_path: str = "db_faiss"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        self.embedding_dim = 1536
        self.indices = {}
        self.metadatas = {}
        
        self.collections = ["rbi_fema", "companies_act", "sebi", "customs_trade", "general"]
        
        for collection in self.collections:
            self.indices[collection] = faiss.IndexFlatIP(self.embedding_dim)
            self.metadatas[collection] = []
        
        self._load_indices()
    
    def _get_embedding(self, text: str) -> np.ndarray:
        try:
            import openai
            
            # Azure OpenAI configuration
            client = openai.AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            
            response = client.embeddings.create(
                model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding / np.linalg.norm(embedding)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            return embedding / np.linalg.norm(embedding)
    
    def add_document_chunks(self, chunks: List[DocumentChunk], collection_name: str = "general"):
        if collection_name not in self.indices:
            return
        
        embeddings = []
        metadatas = []
        
        for chunk in chunks:
            embedding = self._get_embedding(chunk.content)
            embeddings.append(embedding)
            
            metadata = {
                "content": chunk.content,
                "filename": chunk.citation.filename,
                "page_number": chunk.citation.page_number,
                "section": chunk.citation.section,
                "regulation_type": chunk.citation.regulation_type,
                "chunk_id": chunk.chunk_id,
                "authority": chunk.citation.authority
            }
            metadatas.append(metadata)
        
        if embeddings:
            embeddings_array = np.vstack(embeddings)
            self.indices[collection_name].add(embeddings_array)
            self.metadatas[collection_name].extend(metadatas)
            print(f"Added {len(chunks)} chunks to {collection_name}")
            self._save_indices()
    
    def search_documents(self, query: str, collection_name: str = "general", 
                        n_results: int = 5) -> List[Tuple[str, Citation, float]]:
        if collection_name not in self.indices or self.indices[collection_name].ntotal == 0:
            return []
        
        query_embedding = self._get_embedding(query).reshape(1, -1)
        scores, indices = self.indices[collection_name].search(
            query_embedding, min(n_results, self.indices[collection_name].ntotal)
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                metadata = self.metadatas[collection_name][idx]
                citation = Citation(
                    filename=metadata["filename"],
                    page_number=metadata.get("page_number"),
                    section=metadata.get("section"),
                    regulation_type=metadata.get("regulation_type"),
                    chunk_id=metadata["chunk_id"],
                    authority=metadata.get("authority")
                )
                results.append((metadata["content"], citation, float(score)))
        
        return results
    
    def get_database_stats(self) -> Dict:
        stats = {}
        total = 0
        for collection in self.collections:
            count = self.indices[collection].ntotal
            stats[collection] = {"document_count": count}
            total += count
        stats["total_documents"] = total
        return stats
    
    def _save_indices(self):
        for collection in self.collections:
            if self.indices[collection].ntotal > 0:
                faiss.write_index(self.indices[collection], 
                                os.path.join(self.db_path, f"{collection}.faiss"))
                with open(os.path.join(self.db_path, f"{collection}_meta.pkl"), 'wb') as f:
                    pickle.dump(self.metadatas[collection], f)
    
    def _load_indices(self):
        for collection in self.collections:
            index_path = os.path.join(self.db_path, f"{collection}.faiss")
            meta_path = os.path.join(self.db_path, f"{collection}_meta.pkl")
            
            if os.path.exists(index_path):
                try:
                    self.indices[collection] = faiss.read_index(index_path)
                except:
                    self.indices[collection] = faiss.IndexFlatIP(self.embedding_dim)
            
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'rb') as f:
                        self.metadatas[collection] = pickle.load(f)
                except:
                    self.metadatas[collection] = []


class DocumentProcessor:
    def __init__(self, vector_db: VectorDBManager):
        self.vector_db = vector_db
    
    def process_pdf_file(self, file_path: str, authority: str = "general") -> List[DocumentChunk]:
        try:
            import fitz
        except ImportError:
            print("Install PyMuPDF: pip install pymupdf")
            return []
        
        chunks = []
        try:
            doc = fitz.open(file_path)
            filename = os.path.basename(file_path)
            
            for page_num in range(len(doc)):
                text = doc[page_num].get_text()
                if text.strip():
                    text_chunks = self._split_text(text)  # chunk it
                    for i, chunk_text in enumerate(text_chunks):
                        citation = Citation(
                            filename=filename,
                            page_number=page_num + 1,
                            section=f"Page {page_num + 1}, Chunk {i + 1}",
                            regulation_type=authority,
                            authority=authority
                        )
                        chunk = DocumentChunk(content=chunk_text, citation=citation)
                        chunks.append(chunk)
            doc.close()
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        
        return chunks
    
    def _split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Try to break at sentence
                last_period = text.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end
        return chunks
