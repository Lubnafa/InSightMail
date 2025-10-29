# InSightMail 📧

**Your AI-powered job search email copilot that runs 100% locally**

InSightMail connects to multiple Gmail accounts, automatically classifies job-related emails using local LLMs, and provides intelligent insights into your hiring progress through an intuitive dashboard.

## ✨ Features

- 🤖 **Local AI Processing**: Uses Ollama (Mistral/Phi-3) for 100% local, zero-cost LLM inference
- 📧 **Multi-Account Gmail Integration**: Process emails from multiple Gmail accounts
- 🏷️ **Smart Email Classification**: Automatically categorizes emails as:
  - Application Sent
  - Recruiter Response  
  - Interview
  - Offer
  - Rejection
  - Other
- 🔍 **Ask My Inbox**: RAG-powered natural language search through your emails
- 📊 **Job Pipeline Dashboard**: Visual tracking of your application progress
- 📈 **Analytics & Insights**: Detailed analytics on response rates, timing, and trends
- 🚀 **Zero Cost**: No paid APIs required - runs entirely on your local machine

## 🏗️ Architecture

- **Backend**: FastAPI with async processing
- **Frontend**: Streamlit dashboard with interactive components
- **Database**: SQLite for email storage
- **Vector DB**: ChromaDB for semantic search
- **LLM**: Ollama (local inference)
- **Embeddings**: SentenceTransformers
- **Orchestration**: Custom pipeline (no LangChain dependency)

## 🚀 Quick Start

### Prerequisites

1. **Install Ollama** ([ollama.ai](https://ollama.ai))
   ```bash
   # Install Ollama, then pull a model
   ollama pull mistral:7b
   # or
   ollama pull phi3:mini
   ```

2. **Python 3.9+** with pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/InSightMail.git
   cd InSightMail
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment** (optional)
   ```bash
   cp env.example .env
   # Edit .env with your preferences
   ```

4. **Initialize the database**
   ```bash
   cd backend
   python -c "from db import db_manager; db_manager.create_tables()"
   ```

### Running the Application

1. **Start the backend API**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend dashboard** (in a new terminal)
   ```bash
   cd frontend
   streamlit run app.py --server.port 8501
   ```

3. **Open your browser**
   - Dashboard: http://localhost:8501
   - API Docs: http://localhost:8000/docs

## 📧 Getting Your Gmail Data

### Method 1: Google Takeout (Recommended)

1. Go to [Google Takeout](https://takeout.google.com)
2. Select "Mail"
3. Choose format: "All messages included" 
4. Export format: `.mbox` or individual `.eml` files
5. Download and extract

### Method 2: Gmail Search Export

1. In Gmail, search: `(recruiter OR interview OR application OR offer OR job OR hiring)`
2. Use a browser extension to export as JSON/EML
3. Save the exported files

### Method 3: Gmail API (Advanced)

1. Set up Gmail API credentials in Google Cloud Console
2. Configure `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in your environment
3. Use the built-in Gmail API integration

## 📱 Usage

### Upload & Process Emails

1. Navigate to **"Email Upload"** in the sidebar
2. Enter your Gmail account email
3. Upload your exported Gmail files (JSON, EML, MBOX)
4. Wait for AI processing to complete

### View Your Job Pipeline

1. Go to **"Job Pipeline"** to see your application progress
2. Track emails through each stage: Applied → Response → Interview → Offer
3. View conversion rates and identify follow-up opportunities

### Search Your Inbox

1. Use **"Ask My Inbox"** for natural language queries:
   - "How many interviews did I have this month?"
   - "Show me all rejection emails from tech companies"
   - "Which applications need follow-up?"

### Analytics & Insights

1. Visit **"Analytics"** for detailed insights:
   - Response rates and conversion metrics
   - Timeline analysis and activity patterns
   - Company-specific engagement scores
   - Predictive insights and recommendations

## 🔧 Configuration

### Environment Variables

Key settings in `env.example`:

```bash
# LLM Configuration
OLLAMA_MODEL=mistral:7b              # Primary model
OLLAMA_BACKUP_MODEL=phi3:mini        # Fallback model

# Database
DATABASE_URL=sqlite:///data/insightmail.db

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2     # Lightweight, fast
# EMBEDDING_MODEL=intfloat/e5-small  # Alternative option
```

### Model Options

**Recommended Models:**
- `mistral:7b` - Best balance of performance and speed
- `phi3:mini` - Fastest, good for lower-end hardware  
- `llama3.2:3b` - Good alternative

Pull models with: `ollama pull model-name`

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_parser.py
pytest tests/test_rag.py
pytest tests/test_llm.py
```

## 📊 Sample Data

The `data/samples/` directory contains example Gmail exports for testing:

```bash
# Load sample data
cd backend
python -c "
from email_parser import EmailParser
parser = EmailParser()
emails = parser.batch_parse_files(['../data/samples/sample_gmail.json'], 'demo@gmail.com')
print(f'Loaded {len(emails)} sample emails')
"
```

## 🐳 Docker Deployment

```bash
# Build the image
docker build -t insightmail .

# Run with Docker Compose
docker-compose up -d

# Access the application
# Dashboard: http://localhost:8501
# API: http://localhost:8000
```

## 🔍 API Reference

### Key Endpoints

- `GET /health` - System health check
- `POST /emails/upload` - Upload Gmail export files
- `GET /emails` - List processed emails with filtering
- `POST /query` - RAG-powered email search
- `GET /stats` - Pipeline statistics
- `GET /summary` - AI-generated inbox summary

Full API documentation: http://localhost:8000/docs

## 🛠️ Development

### Project Structure

```
insightmail/
├── backend/                 # FastAPI backend
│   ├── main.py             # API routes
│   ├── db.py               # Database models  
│   ├── email_parser.py     # Gmail export parsing
│   ├── llm_adapter.py      # Ollama interface
│   ├── rag_pipeline.py     # Vector search & retrieval
│   ├── summarizer_chain.py # LLM classification pipeline
│   └── utils.py            # Utility functions
├── frontend/               # Streamlit dashboard
│   ├── app.py              # Main dashboard
│   └── components/         # UI components
├── tests/                  # Test suite
├── data/                   # Data storage
│   ├── samples/            # Sample data
│   ├── embeddings/         # Vector database
│   └── tokens/             # API tokens
└── requirements.txt        # Dependencies
```

### Adding New Features

1. **Email Classification Categories**: Modify `EmailCategory` enum in `db.py`
2. **LLM Prompts**: Update prompts in `summarizer_chain.py`
3. **Dashboard Components**: Add new components in `frontend/components/`
4. **API Endpoints**: Add routes in `backend/main.py`

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest`
5. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**"Ollama not responding"**
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`
- Verify the API URL: `curl http://localhost:11434/api/tags`

**"No emails found"**
- Check file format (JSON, EML, MBOX supported)
- Verify Gmail account email is correct
- Ensure files contain job-related content

**"Classification not working"**
- Check Ollama model is loaded: `ollama ps`
- Try a different model: `ollama pull phi3:mini`
- Check API logs for errors

**"Slow performance"**
- Use smaller models (phi3:mini vs mistral:7b)
- Reduce batch sizes in configuration
- Close other resource-intensive applications

### Performance Optimization

1. **Model Selection**: Start with `phi3:mini` for speed
2. **Batch Processing**: Adjust `MAX_EMAILS_PER_BATCH` in config
3. **Hardware**: 8GB+ RAM recommended for larger models
4. **Storage**: SSD recommended for database operations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [SentenceTransformers](https://www.sbert.net/) - Embedding models
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Streamlit](https://streamlit.io/) - Dashboard framework

## 🤝 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/yourusername/InSightMail/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/InSightMail/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/yourusername/InSightMail/wiki)

---

**Built with ❤️ for job seekers who want to take control of their data and privacy.**
