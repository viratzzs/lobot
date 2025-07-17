"""
Vector Database Manager for Regulatory Compliance System
Handles document storage, retrieval, and citation management.
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


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
        return ", ".join(parts)


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata"""
    content: str
    citation: Citation
    chunk_id: str
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = hashlib.md5(
                (self.content + self.citation.filename).encode()
            ).hexdigest()[:16]


class VectorDBManager:
    """Manages vector database operations for regulatory documents"""
    
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
        """Add document chunks to the specified collection"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk.content)
            metadatas.append({
                "filename": chunk.citation.filename,
                "page_number": chunk.citation.page_number,
                "title": chunk.citation.title,
                "line_number": chunk.citation.line_number,
                "section": chunk.citation.section,
                "regulation_type": chunk.citation.regulation_type,
                "chunk_id": chunk.chunk_id
            })
            ids.append(chunk.chunk_id)
        
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
                chunk_id=metadata["chunk_id"]
            )
            search_results.append((doc, citation, distance))
        
        return search_results
    
    def get_document_stats(self) -> Dict[str, int]:
        """Get statistics about stored documents"""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = collection.count()
        return stats


class DocumentProcessor:
    """Processes various document types for vector storage"""
    
    def __init__(self, vector_db: VectorDBManager):
        self.vector_db = vector_db
    
    def process_text_file(self, file_path: str, regulation_type: str = "general",
                         chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
        """Process a text file into chunks"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
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
                citation = Citation(
                    filename=os.path.basename(file_path),
                    regulation_type=regulation_type,
                    section=f"Chunk {chunk_num}",
                    line_number=content[:start].count('\n') + 1
                )
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    citation=citation,
                    chunk_id=f"{os.path.basename(file_path)}_chunk_{chunk_num}"
                )
                chunks.append(chunk)
                chunk_num += 1
            
            start = end - overlap if end < len(content) else end
        
        return chunks
    
    def process_pdf_file(self, file_path: str, regulation_type: str = "general") -> List[DocumentChunk]:
        """Process a PDF file using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("PyMuPDF not installed. Install with: pip install pymupdf")
            return []
        
        chunks = []
        
        try:
            pdf_document = fitz.open(file_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                
                if text.strip():
                    # Split page text into smaller chunks
                    page_chunks = self._split_text_into_chunks(text)
                    
                    for chunk_idx, chunk_text in enumerate(page_chunks):
                        citation = Citation(
                            filename=os.path.basename(file_path),
                            page_number=page_num + 1,
                            regulation_type=regulation_type,
                            section=f"Page {page_num + 1}, Chunk {chunk_idx + 1}"
                        )
                        
                        chunk = DocumentChunk(
                            content=chunk_text,
                            citation=citation,
                            chunk_id=f"{os.path.basename(file_path)}_p{page_num + 1}_c{chunk_idx + 1}"
                        )
                        chunks.append(chunk)
            
            pdf_document.close()
            
        except Exception as e:
            print(f"Error processing PDF {file_path}: {str(e)}")
            return []
        
        return chunks
    
    def process_docx_file(self, file_path: str, regulation_type: str = "general") -> List[DocumentChunk]:
        """Process a DOCX file using python-docx"""
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
            
            # Join paragraphs and split into chunks
            content = '\n'.join(full_text)
            text_chunks = self._split_text_into_chunks(content)
            
            for chunk_idx, chunk_text in enumerate(text_chunks):
                citation = Citation(
                    filename=os.path.basename(file_path),
                    regulation_type=regulation_type,
                    section=f"Document Chunk {chunk_idx + 1}"
                )
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    citation=citation,
                    chunk_id=f"{os.path.basename(file_path)}_chunk_{chunk_idx + 1}"
                )
                chunks.append(chunk)
                
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {str(e)}")
            return []
        
        return chunks
    
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


# Test function
def test_vector_db():
    """Test the vector database functionality"""
    db = VectorDBManager()
    processor = DocumentProcessor(db)
    
    # Test with sample data
    sample_chunks = [
        DocumentChunk(
            content="Foreign Direct Investment in India is governed by the Foreign Exchange Management Act (FEMA) 1999. All FDI transactions must be reported to RBI within 30 days.",
            citation=Citation(
                filename="fema_guidelines.pdf",
                page_number=15,
                title="FDI Reporting Requirements",
                regulation_type="FEMA",
                section="Chapter 3"
            ),
            chunk_id="fema_001"
        ),
        DocumentChunk(
            content="Companies Act 2013 requires all companies to maintain proper books of accounts. The accounts must be audited annually by a qualified chartered accountant.",
            citation=Citation(
                filename="companies_act_2013.pdf",
                page_number=87,
                title="Books of Accounts",
                regulation_type="Companies Act",
                section="Section 128"
            ),
            chunk_id="companies_001"
        )
    ]
    
    db.add_document_chunks(sample_chunks, "rbi_fema")
    
    # Test search
    results = db.search_documents("FDI reporting requirements", "rbi_fema")
    for content, citation, score in results:
        print(f"Score: {score}")
        print(f"Content: {content[:100]}...")
        print(f"Citation: {citation.to_citation_string()}")
        print("---")


if __name__ == "__main__":
    test_vector_db()
