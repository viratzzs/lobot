# 💰 LoBot - Your AI Financial Consultant

A multi-agent AI system that helps you navigate Indian financial regulations. Think of it as having specialized consultants for RBI/FEMA, Companies Act, SEBI, and Customs/Trade - all backed by actual regulatory documents.

## What it does

- **Answers regulatory questions** with proper citations (no BS, just facts)
- **Analyzes documents** for compliance issues
- **Routes queries** to the right specialist agents
- **Provides citations** for everything it tells you

## Tech Stack

- **CrewAI** for agent orchestration
- **FAISS** for document storage (until I decide to stop being lazy and shift entirely to azure db)
- **Azure OpenAI** for embeddings and completions (enterprise-grade deployment)
- **Python 3.11+**

## Azure Integration

We're using Azure OpenAI instead of direct OpenAI API for better:
- **Enterprise compliance** and data governance
- **Regional deployment** (keeps data in your preferred region)
- **Better rate limits** and SLA guarantees
- **Integration with Azure security** and monitoring

This means your financial data stays within Azure's enterprise environment rather than going directly to OpenAI (haha).

## Quick Start

1. **Clone and setup**:
```bash
git clone <repository-url>
cd lobot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

2. Configure Azure OpenAI credentials in the environment

3. **Run it**:
```bash
python main.py
```

## Usage

Just run the main script and pick what you want to do:
- Ask regulatory questions
- Analyze documents for compliance
- Add new documents to the knowledge base

**Sample questions:**
- "What are FDI reporting requirements under FEMA?"
- "Board meeting rules for private companies?"
- "SEBI disclosure requirements for listed companies?"

## What's inside

The system has specialized agents for different areas:
- **RBI/FEMA**: Banking and foreign exchange stuff
- **Companies Act**: Corporate governance and compliance
- **SEBI**: Securities and capital markets
- **Customs/Trade**: Import/export regulations

## Project Structure
```
src/
├── agents.py        # The specialist agents
├── rag_tools.py     # Citation and retrieval tools
├── tasks.py         # Task definitions
└── faiss_db.py      # Vector database stuff
```

## Important Notes

- Everything is backed by actual regulatory documents
- Citations are mandatory - no made-up answers
- Keep your documents updated for latest regulations
- This is guidance, not legal advice - check with lawyers for critical stuff
