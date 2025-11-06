# InSightMail - Complete Project Overview

## 📋 Table of Contents
1. [What is InSightMail?](#what-is-insightmail)
2. [How It Works](#how-it-works)
3. [Architecture Overview](#architecture-overview)
4. [Key Components](#key-components)
5. [Data Flow](#data-flow)
6. [Requirements to Run](#requirements-to-run)
7. [Setup Instructions](#setup-instructions)
8. [Usage Guide](#usage-guide)

---

## 🎯 What is InSightMail?

**InSightMail** is an AI-powered job search email management system that runs **100% locally** on your machine. It helps job seekers organize, analyze, and gain insights from their job-related emails without compromising privacy or incurring cloud API costs.

### Key Features:
- 🤖 **100% Local AI**: Uses Ollama (Mistral/Phi-3) - no cloud APIs, no costs, complete privacy
- 📧 **Multi-Account Support**: Process emails from multiple Gmail accounts simultaneously
- 🎯 **Smart Classification**: Auto-categorizes emails into: Applications, Recruiter Outreach, Interviews, Offers, Rejections
- 🔍 **AI-Powered Search**: Natural language queries across your entire email history using RAG (Retrieval-Augmented Generation)
- 📊 **Visual Analytics**: Interactive dashboards showing pipeline conversion, response rates, and trends
- ⚡ **Real-time Processing**: Background processing with live updates as emails are analyzed
- 🔒 **Privacy First**: All processing happens locally - your emails never leave your machine

---

## 🏗️ How It Works

### High-Level Flow:

```
1. User uploads Gmail export files (JSON/EML/MBOX)
   ↓
2. Email Parser extracts email data (subject, sender, body, date)
   ↓
3. Emails stored in SQLite database
   ↓
4. LLM (Ollama) classifies each email into job categories
   ↓
5. Email content converted to embeddings (vector representations)
   ↓
6. Embeddings stored in ChromaDB vector database
   ↓
7. User queries emails using natural language
   ↓
8. RAG pipeline finds similar emails and generates answers
   ↓
9. Results displayed in Streamlit dashboard with analytics
```

### Processing Pipeline:

1. **Email Upload & Parsing**
   - User uploads Gmail export files via Streamlit UI
   - `EmailParser` extracts structured data from JSON/EML/MBOX formats
   - Emails are validated and deduplicated

2. **Database Storage**
   - Emails stored in SQLite database with metadata
   - Categories: Application Sent, Recruiter Response, Interview, Offer, Rejection, Other

3. **AI Classification**
   - `SummarizerChain` uses Ollama LLM to classify emails
   - Generates category, confidence score, and summary for each email
   - Processes emails in background tasks

4. **Vector Embedding**
   - `RAGPipeline` converts email content to embeddings using SentenceTransformers
   - Embeddings stored in ChromaDB for semantic search
   - Enables natural language queries

5. **Search & Retrieval**
   - User queries in natural language (e.g., "Show me interview emails")
   - RAG pipeline finds semantically similar emails
   - LLM generates contextual answers based on retrieved emails

6. **Analytics & Visualization**
   - Dashboard shows job pipeline statistics
   - Conversion rates, response rates, trends
   - Interactive charts and graphs

---

## 🏛️ Architecture Overview

### Technology Stack:

```
Frontend (Streamlit)
    ↓ HTTP Requests
Backend (FastAPI)
    ↓
    ├── SQLite Database (Structured Data)
    ├── ChromaDB (Vector Store)
    └── Ollama (Local LLM)
```

### Component Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  - Dashboard, Email Upload, Job Pipeline, Analytics         │
│  - Components: sidebar, email_upload, job_pipeline, etc.    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Email Parser │  │ LLM Adapter  │  │ RAG Pipeline │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼──────┐     │
│  │         Summarizer Chain (Orchestration)          │     │
│  └───────────────────────────────────────────────────┘     │
└──────┬──────────────────┬──────────────────┬───────────────┘
       │                  │                  │
┌──────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
│   SQLite    │  │   ChromaDB    │  │    Ollama    │
│  Database   │  │ Vector Store  │  │  Local LLM   │
└─────────────┘  └───────────────┘  └──────────────┘
```

---

## 🔧 Key Components

### Backend Components:

#### 1. **main.py** - FastAPI Application
- **Purpose**: REST API server that handles all HTTP requests
- **Key Endpoints**:
  - `POST /emails/upload` - Upload Gmail export files
  - `GET /emails` - Retrieve emails with filters
  - `POST /query` - Natural language search using RAG
  - `GET /stats` - Job pipeline statistics
  - `GET /summary` - AI-generated inbox summary
  - `GET /health` - System health check
- **Features**: Background task processing, CORS middleware, error handling

#### 2. **db.py** - Database Manager
- **Purpose**: SQLite database operations using SQLAlchemy ORM
- **Models**:
  - `Email`: Stores email data (subject, sender, body, category, etc.)
  - `JobApplication`: Tracks job applications (optional, for future use)
- **Operations**: CRUD operations, filtering, statistics, deduplication

#### 3. **email_parser.py** - Email Parser
- **Purpose**: Parse emails from various formats (JSON, EML, MBOX)
- **Features**:
  - Gmail API JSON format support
  - Google Takeout format support
  - EML file parsing
  - Base64 decoding for email bodies
  - Header decoding (subject, sender, date)
  - Multipart message handling
  - Content cleaning and normalization

#### 4. **llm_adapter.py** - LLM Interface
- **Purpose**: Interface to Ollama local LLM
- **Features**:
  - Async HTTP client for Ollama API
  - Model health checking
  - Text generation with configurable parameters
  - Structured JSON response generation
  - Batch processing support
  - Model fallback (primary → backup model)
- **Supported Models**: Mistral 7B, Phi-3 Mini, Llama 3.2 3B

#### 5. **rag_pipeline.py** - RAG Pipeline
- **Purpose**: Vector search and retrieval for semantic email search
- **Features**:
  - SentenceTransformer embeddings (all-MiniLM-L6-v2)
  - ChromaDB vector store integration
  - Semantic similarity search
  - Category-based filtering
  - Date range filtering
  - Similar email finding
  - Embedding export/import

#### 6. **summarizer_chain.py** - Email Classification Chain
- **Purpose**: Orchestrates email classification and summarization
- **Features**:
  - Email classification into job categories
  - Confidence scoring
  - Email summarization
  - Inbox summary generation
  - Job progress analysis
  - Follow-up suggestions
  - Contact information extraction

#### 7. **utils.py** - Utility Functions
- **Purpose**: Helper functions for email processing
- **Features**:
  - Email content cleaning
  - Sender information extraction
  - Company name extraction from email domains
  - Date parsing
  - Content validation
  - Email deduplication
  - Priority scoring

### Frontend Components:

#### 1. **app.py** - Main Streamlit Application
- **Purpose**: Main dashboard and navigation
- **Features**:
  - Page routing
  - API client for backend communication
  - Health check monitoring
  - Dashboard overview with metrics

#### 2. **components/sidebar.py** - Navigation Sidebar
- **Purpose**: Navigation menu and quick stats
- **Features**: Page selection, quick stats, settings, help

#### 3. **components/email_upload.py** - Email Upload Interface
- **Purpose**: File upload and processing interface
- **Features**:
  - Multi-file upload
  - File validation
  - Progress tracking
  - Upload history

#### 4. **components/job_pipeline.py** - Job Pipeline Visualization
- **Purpose**: Visualize job application pipeline
- **Features**: Funnel charts, category breakdown, timeline view

#### 5. **components/email_viewer.py** - Email Viewer
- **Purpose**: Display and browse individual emails
- **Features**: Email list, filtering, detailed view

#### 6. **components/rag_search.py** - Natural Language Search
- **Purpose**: "Ask My Inbox" search interface
- **Features**: Query input, results display, source citations

#### 7. **components/analytics.py** - Analytics Dashboard
- **Purpose**: Advanced analytics and insights
- **Features**: Charts, trends, conversion rates, company analysis

---

## 🔄 Data Flow

### Email Processing Flow:

```
1. User uploads file via Streamlit
   ↓
2. FastAPI receives file at /emails/upload
   ↓
3. EmailParser.parse_gmail_json() extracts email data
   ↓
4. Background task: process_emails_batch()
   ↓
5. For each email:
   a. SummarizerChain.classify_email() → LLM classification
   b. DatabaseManager.add_email() → Store in SQLite
   c. RAGPipeline.add_email() → Generate embedding & store in ChromaDB
   ↓
6. Email marked as processed
   ↓
7. User can query/search emails via dashboard
```

### Search Query Flow:

```
1. User enters query: "Show me interview emails"
   ↓
2. Streamlit sends POST /query with query text
   ↓
3. RAGPipeline.search_similar() finds similar emails
   ↓
4. LLMAdapter.generate_response() creates answer from context
   ↓
5. Results returned to frontend
   ↓
6. Streamlit displays answer + source emails
```

---

## 📦 Requirements to Run

### System Requirements:

1. **Python 3.9+**
   - Required for async/await support and modern features

2. **Ollama** (Local LLM Server)
   - Download from: https://ollama.ai
   - At least one model installed:
     - `mistral:7b` (recommended, 8GB+ RAM)
     - `phi3:mini` (faster, 4GB+ RAM)
     - `llama3.2:3b` (balanced, 6GB+ RAM)

3. **Memory Requirements**:
   - Minimum: 4GB RAM (for phi3:mini)
   - Recommended: 8GB+ RAM (for mistral:7b)
   - Storage: ~2GB for models + database

4. **Operating System**:
   - Windows 10/11
   - macOS 10.15+
   - Linux (Ubuntu 20.04+)

### Python Dependencies:

All dependencies are listed in `requirements.txt`:

**Core Framework:**
- `fastapi==0.104.1` - Backend API framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `streamlit==1.28.1` - Frontend framework

**Database:**
- `sqlalchemy==2.0.23` - ORM for SQLite
- `alembic==1.12.1` - Database migrations

**Vector Database & Embeddings:**
- `chromadb==0.4.15` - Vector database
- `sentence-transformers==2.2.2` - Embedding models
- `numpy==1.24.3` - Numerical operations

**LLM & AI:**
- `ollama==0.1.7` - Ollama Python client
- `httpx==0.24.1` - Async HTTP client

**Email Processing:**
- `email-validator==2.1.0` - Email validation
- `python-multipart==0.0.6` - File upload support

**Data Processing:**
- `pandas==2.1.3` - Data manipulation
- `pydantic==2.5.0` - Data validation

**Visualization:**
- `plotly==5.17.0` - Interactive charts
- `altair==5.1.2` - Statistical visualization

**Other:**
- `python-dotenv==1.0.0` - Environment variables
- `pytest==7.4.3` - Testing framework

---

## 🚀 Setup Instructions

### Step 1: Install Ollama

**Windows:**
```bash
# Download installer from https://ollama.ai/download
# Run installer and follow prompts
```

**macOS:**
```bash
brew install ollama
# OR download from https://ollama.ai/download
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Pull AI Model

```bash
# Start Ollama service
ollama serve

# In another terminal, pull a model
ollama pull mistral:7b      # Recommended (best accuracy)
# OR
ollama pull phi3:mini       # Faster alternative
```

### Step 3: Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd InSightMail

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env file with your settings:
# - OLLAMA_BASE_URL=http://localhost:11434
# - OLLAMA_MODEL=mistral:7b
# - DATABASE_URL=sqlite:///data/insightmail.db
```

### Step 5: Initialize Database

```bash
cd backend
python -c "from db import db_manager; db_manager.create_tables()"
```

### Step 6: Start Application

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py --server.port 8501
```

### Step 7: Access Application

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📖 Usage Guide

### 1. Upload Gmail Data

**Option A: Google Takeout (Recommended)**
1. Go to https://takeout.google.com
2. Select "Mail" → "All messages included"
3. Export as JSON or EML format
4. Download and extract files

**Option B: Gmail API**
- Use Gmail API to export emails programmatically
- Save as JSON format

**Upload in InSightMail:**
1. Navigate to "Email Upload" page
2. Enter your Gmail account email
3. Select exported files (JSON/EML/MBOX)
4. Click "Start Processing"
5. Wait for background processing to complete

### 2. View Job Pipeline

1. Navigate to "Job Pipeline" page
2. View emails categorized by:
   - Application Sent
   - Recruiter Response
   - Interview
   - Offer
   - Rejection
3. See conversion funnel and statistics

### 3. Search Emails

1. Navigate to "Ask My Inbox" page
2. Enter natural language query:
   - "Show me interview emails"
   - "Which companies sent me offers?"
   - "Find emails about remote positions"
3. View AI-generated answer with source emails

### 4. View Analytics

1. Navigate to "Analytics" page
2. View:
   - Response rates
   - Conversion rates
   - Timeline trends
   - Company analysis
   - Performance metrics

### 5. Browse Emails

1. Navigate to "Email Viewer" page
2. Filter by category, date, sender
3. View email details and summaries

---

## 🔍 Key Features Explained

### Email Classification

The system uses a local LLM (Ollama) to classify emails into job-related categories:

- **Application Sent**: Emails you sent applying for jobs
- **Recruiter Response**: Responses from recruiters/HR
- **Interview**: Interview invitations and scheduling
- **Offer**: Job offers and offer-related communications
- **Rejection**: Rejection letters
- **Other**: Non-job-related emails

Classification includes:
- Category assignment
- Confidence score (0.0-1.0)
- One-line summary
- Key information extraction

### RAG (Retrieval-Augmented Generation)

The RAG pipeline enables natural language search:

1. **Embedding Generation**: Email content converted to vector embeddings
2. **Vector Storage**: Embeddings stored in ChromaDB
3. **Query Processing**: User query converted to embedding
4. **Similarity Search**: Find similar emails using cosine similarity
5. **Context Generation**: Retrieve top-k similar emails
6. **Answer Generation**: LLM generates answer based on retrieved context

### Analytics & Insights

The system provides:

- **Pipeline Statistics**: Count of emails in each category
- **Conversion Rates**: Application → Response → Interview → Offer
- **Response Rates**: Percentage of applications that received responses
- **Timeline Analysis**: Email activity over time
- **Company Insights**: Most active companies and engagement
- **Follow-up Suggestions**: Emails that need attention

---

## 🐳 Docker Deployment (Optional)

### Using Docker Compose:

```bash
# Start all services (app + Ollama)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build:

```bash
# Build image
docker build -t insightmail .

# Run container
docker run -p 8501:8501 -p 8000:8000 insightmail
```

---

## 🧪 Testing

### Run Test Suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_parser.py
pytest tests/test_rag.py
pytest tests/test_llm.py
```

### Test with Sample Data:

```bash
# Use included sample data
cd backend
python -c "
from email_parser import EmailParser
parser = EmailParser()
emails = parser.batch_parse_files(['../data/samples/sample_gmail.json'], 'demo@gmail.com')
print(f'✅ Loaded {len(emails)} sample emails')
"
```

---

## 🐛 Troubleshooting

### Common Issues:

1. **Ollama not responding**
   - Check if Ollama is running: `ollama list`
   - Start Ollama: `ollama serve`
   - Verify model is installed: `ollama pull mistral:7b`

2. **No emails processed**
   - Check file format (JSON/EML supported)
   - Verify account email matches
   - Check backend logs for errors

3. **Classification failing**
   - Verify Ollama is running
   - Check model is available: `ollama list`
   - Try different model: `ollama pull phi3:mini`

4. **Search not working**
   - Wait for embeddings to generate
   - Check ChromaDB initialization
   - Verify vector database is created

5. **Slow performance**
   - Use smaller model (phi3:mini)
   - Reduce batch size
   - Close other applications

---

## 📊 Project Structure

```
InSightMail/
├── backend/                 # FastAPI backend
│   ├── main.py             # API routes & endpoints
│   ├── db.py               # Database models & operations
│   ├── email_parser.py     # Gmail export parsing
│   ├── llm_adapter.py      # Ollama LLM interface
│   ├── rag_pipeline.py     # Vector search pipeline
│   ├── summarizer_chain.py # Email classification
│   └── utils.py            # Utility functions
├── frontend/               # Streamlit frontend
│   ├── app.py              # Main application
│   └── components/         # UI components
│       ├── sidebar.py
│       ├── email_upload.py
│       ├── job_pipeline.py
│       ├── email_viewer.py
│       ├── rag_search.py
│       └── analytics.py
├── data/                   # Data storage
│   ├── samples/            # Sample email data
│   ├── embeddings/         # ChromaDB vector store
│   └── tokens/             # Auth tokens (if using Gmail API)
├── tests/                  # Test suite
│   ├── test_parser.py
│   ├── test_rag.py
│   └── test_llm.py
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # Docker image definition
├── env.example             # Environment variables template
└── README.md               # Project documentation
```

---

## 🔐 Privacy & Security

- **100% Local Processing**: All data stays on your machine
- **No Cloud APIs**: No data sent to external services
- **Local LLM**: Ollama runs entirely locally
- **Local Database**: SQLite database stored locally
- **Local Vector Store**: ChromaDB stored locally
- **No Tracking**: No analytics or tracking

---

## 🚀 Future Enhancements

Planned features:
- 📱 Mobile app (iOS/Android)
- 🔗 Platform integration (LinkedIn, Indeed)
- 🤝 Team features (share with career coaches)
- 📊 Advanced analytics (predictive modeling)
- 🔄 Real-time Gmail sync (without exports)
- 🌐 Multi-language support
- 📧 Email templates for follow-ups

---

## 📝 Summary

**InSightMail** is a complete, privacy-focused job search email management system that:

1. **Processes** Gmail exports locally
2. **Classifies** emails using local AI (Ollama)
3. **Stores** data in local databases (SQLite + ChromaDB)
4. **Searches** emails using semantic similarity (RAG)
5. **Visualizes** insights through interactive dashboards

All processing happens **100% locally** - your emails never leave your machine, ensuring complete privacy and no cloud costs.

---

## 📚 Additional Resources

- **Ollama Documentation**: https://ollama.ai/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Streamlit Documentation**: https://docs.streamlit.io
- **ChromaDB Documentation**: https://docs.trychroma.com
- **SentenceTransformers**: https://www.sbert.net

---

*Last Updated: 2024*

