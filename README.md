# 🏛️ Indian Regulatory Compliance Advisory System

An advanced AI-powered multi-agent system designed to provide expert guidance on Indian regulatory and compliance matters. This system uses specialized AI agents to handle queries related to RBI/FEMA, Companies Act, SEBI, and Customs/Trade regulations.

## 🎯 Mission Objective

Provide accurate, well-cited regulatory guidance to enterprises operating in India's financial technology and corporate sectors. The system ensures:
- **No hallucination**: All responses are grounded in actual regulatory documents
- **Mandatory citations**: Every recommendation includes proper source references
- **Multi-domain expertise**: Specialized agents for different regulatory areas
- **Document compliance analysis**: Automated review of legal agreements

## 🏗️ System Architecture

### Multi-Agent Structure
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Query Router   │ -> │  Specialist     │ -> │  Synthesis      │
│  Agent          │    │  Agents         │    │  Agent          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Specialized Agents
- **🎯 Query Router**: Analyzes queries and routes to appropriate specialists
- **🏦 RBI/FEMA Specialist**: Banking regulations and foreign exchange matters
- **🏢 Companies Act Specialist**: Corporate governance and compliance
- **📊 SEBI Specialist**: Securities law and capital markets
- **🚢 Customs/Trade Specialist**: Import/export and trade regulations
- **📄 Document Analyzer**: Compliance analysis of legal documents
- **⚖️ Synthesis Agent**: Final report generation with citations

### Technology Stack
- **Framework**: CrewAI for multi-agent orchestration
- **Vector Database**: ChromaDB for document storage and retrieval
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT-4 Turbo
- **Languages**: Python 3.11+

## 🚀 Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd lobot
```

2. **Create virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -e .
```

4. **Set up environment variables**:
```bash
cp .env.template .env
# Edit .env file with your OpenAI API key
```

## 🔧 Configuration

### Environment Variables
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
CHROMA_DB_PATH=./db
EMBEDDING_MODEL=text-embedding-3-small
```

### Database Setup
The system uses ChromaDB for vector storage. Collections are automatically created for:
- `rbi_fema`: RBI and FEMA documents
- `companies_act`: Companies Act and corporate law
- `sebi`: SEBI regulations and securities law
- `customs_trade`: Customs and trade regulations
- `general`: General regulatory documents

## 📖 Usage

### Command Line Interface
```bash
python main.py
```

### Interactive Menu
```
Options:
1. Ask a regulatory question
2. Analyze a document
3. Add documents to database
4. System status
5. Exit
```

### Sample Queries
- "What are the reporting requirements for Foreign Direct Investment under FEMA?"
- "What are the board meeting requirements for private companies under Companies Act 2013?"
- "What are the disclosure requirements for listed companies under SEBI LODR?"

### Document Analysis
The system can analyze legal documents for compliance issues:
```python
result = system.analyze_document(document_content, "companies")
```

## 📚 Document Management

### Adding Documents
```python
# Add regulatory documents to the database
file_paths = ["rbi_circular.pdf", "companies_act.txt"]
regulation_types = ["rbi", "companies"]
result = system.add_documents_to_database(file_paths, regulation_types)
```

### Supported Formats
- **Text files** (`.txt`): Direct processing
- **PDF files** (`.pdf`): Extracted and chunked
- **Word documents** (`.docx`): Planned feature

### Citation Structure
Each document chunk includes:
- **Filename**: Source document name
- **Page number**: Specific page reference
- **Title**: Document/section title
- **Line number**: Specific line reference
- **Section**: Document section/chapter
- **Regulation type**: RBI, FEMA, Companies Act, etc.

## 🔍 System Features

### 1. Query Processing
- Intelligent routing to appropriate specialists
- Multi-domain query handling
- Contextual document retrieval
- Proper citation validation

### 2. Document Analysis
- Clause-by-clause compliance review
- Regulatory violation identification
- Amendment recommendations
- Risk prioritization

### 3. Citation Management
- Structured citation format
- Source validation
- Completeness scoring
- Automated formatting

### 4. Quality Assurance
- No hallucination policy
- Mandatory source citations
- Confidence scoring
- Limitation disclosure

## 🏛️ Regulatory Domains

### RBI/FEMA
- Foreign Direct Investment
- External Commercial Borrowings
- Foreign Exchange transactions
- Banking regulations
- Payment systems

### Companies Act 2013
- Corporate governance
- Board meetings and resolutions
- Annual filings
- Mergers and acquisitions
- Compliance requirements

### SEBI Regulations
- Listing obligations
- Disclosure requirements
- Insider trading
- Takeover regulations
- Investment advisory

### Customs & Trade
- Import/export procedures
- Customs valuation
- Trade policy
- GST on imports
- Export incentives

## 🔧 Development

### Project Structure
```
lobot/
├── src/
│   ├── __init__.py
│   ├── vector_db.py      # Vector database management
│   ├── rag_tools.py      # RAG tools and citation handling
│   ├── agents.py         # Specialized agent definitions
│   └── tasks.py          # Task orchestration
├── db/                   # ChromaDB storage
├── logs/                 # System logs
├── main.py              # Main application
├── pyproject.toml       # Project configuration
└── README.md           # Documentation
```

### Adding New Agents
1. Create agent in `src/agents.py`
2. Define specialized tools if needed
3. Update task factory for new workflows
4. Add to agent registry

### Extending Document Support
1. Add processor in `src/vector_db.py`
2. Update file type handling
3. Implement citation extraction
4. Test with sample documents

## 🚨 Important Notes

### Data Privacy
- All processing is done locally
- No data sent to external services except OpenAI API
- Implement proper access controls for sensitive documents

### Limitations
- Responses are based on available documents in the database
- System clearly indicates when information is not available
- Regular updates needed for regulatory changes

### Compliance Disclaimer
This system provides guidance based on available regulatory documents. Users should:
- Verify critical compliance matters with legal counsel
- Keep documents updated with latest regulations
- Understand system limitations and scope

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit pull request with detailed description

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the documentation
- Review system logs
- Contact the development team
- Submit issues on GitHub

---

**Built with ❤️ for regulatory compliance in India**
