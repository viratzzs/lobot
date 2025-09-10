import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_faiss_demo():
    print("🏛️  FAISS Demo - Processing 5 files from each folder")
    print("=" * 50)
    
    load_dotenv()
    
    # Check for Azure OpenAI environment variables
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing Azure OpenAI environment variables: {', '.join(missing_vars)}")
        print("Set these in your .env file:")
        print("AZURE_OPENAI_API_KEY=your_azure_openai_key")
        print("AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("AZURE_OPENAI_API_VERSION=2024-02-01 (optional)")
        print("AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small (optional)")
        return False
    
    try:
        from src.faiss_db import VectorDBManager, DocumentProcessor
        
        vector_db = VectorDBManager()
        processor = DocumentProcessor(vector_db)
        
        data_dirs = {
            "data/bare_acts": "companies_act",
            "data/rbi": "rbi_fema", 
            "data/sebi": "sebi",
            "data/cbic": "customs_trade",
            "data/sc": "general"
        }
        
        for data_dir, collection in data_dirs.items():
            if not os.path.exists(data_dir):
                continue
                
            pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')][:5]
            print(f"\n📂 {data_dir}: Processing {len(pdf_files)} files")
            
            for pdf_file in pdf_files:
                file_path = os.path.join(data_dir, pdf_file)
                try:
                    chunks = processor.process_pdf_file(file_path, collection)
                    if chunks:
                        vector_db.add_document_chunks(chunks, collection)
                        print(f"   ✅ {pdf_file}: {len(chunks)} chunks")
                except Exception as e:
                    print(f"   ❌ {pdf_file}: {e}")
        
        # Show stats
        print(f"\n📊 Database Stats:")
        stats = vector_db.get_database_stats()
        for collection, info in stats.items():
            if collection != "total_documents":
                print(f"   {collection}: {info['document_count']} docs")
        print(f"   TOTAL: {stats['total_documents']} documents")
        
        # Test search
        print(f"\n🔍 Testing searches:")
        queries = [
            ("FDI regulations", "rbi_fema"),
            ("disclosure requirements", "sebi"), 
            ("customs duties", "customs_trade"),
            ("company registration", "companies_act"),
            ("court procedures", "general")
        ]
        
        for query, collection in queries:
            results = vector_db.search_documents(query, collection, 2)
            print(f"\n   '{query}' in {collection}:")
            if results:
                for i, (content, citation, score) in enumerate(results):
                    print(f"      {i+1}. {citation.filename} (Score: {score:.3f})")
                    print(f"         {content[:80]}...")
            else:
                print(f"      No results")
        
        print(f"\n🎉 Demo completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    run_faiss_demo()
