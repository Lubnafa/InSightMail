# InSightMail

**Your local AI copilot for managing your job search inbox**

Job hunting usually means drowning in emails — applications, rejections, interviews, follow-ups — all scattered across accounts. InSightMail helps you turn that chaos into clarity.

It runs entirely on your own machine, so your data stays private while you get analytics and insights that actually help you.

## Why InSightMail

### The Problem

If you've been applying for jobs online, you know how messy it gets. Dozens of emails from recruiters, interviews, and updates pile up fast. Keeping track of who replied, who didn't, and when to follow up becomes impossible.

### The Solution

InSightMail automatically organizes your Gmail exports using local AI models (no cloud calls, no cost). It classifies messages, builds dashboards, and lets you query your inbox in plain English — all locally.

## Key Features

| Feature | Description |
|---------|-------------|
| **100% Local AI** | Uses Ollama (Mistral or Phi-3). No servers, no API costs, no data leaks. |
| **Multi-Account Support** | Process exports from multiple Gmail accounts together. |
| **Smart Categorization** | Detects Applications, Recruiter Outreach, Interviews, Offers, and Rejections. |
| **Ask My Inbox** | Search with plain English queries such as "Show me all interview invites from last month." |
| **Visual Analytics** | Interactive charts showing conversion rates, follow-up needs, and company trends. |
| **Real-Time Updates** | Emails are parsed and classified as soon as they're uploaded. |
| **Privacy-First** | Everything stays local — nothing ever leaves your system. |

## Architecture Overview

```
Streamlit (UI)  →  FastAPI (Backend)  →  Ollama (Local LLM)
                              ↓
                          SQLite DB
                              ↓
                         ChromaDB (Vector Store)
```

**Tech stack:**
- FastAPI (backend API)
- Streamlit (frontend dashboard)
- SQLite (database)
- ChromaDB (vector search)
- Ollama + SentenceTransformers (AI and embeddings)

## Getting Started

### 1. Requirements

- **Python 3.9 or newer**
- **Ollama** installed locally

Install a model for the app to use:

```bash
ollama pull mistral:7b   # High quality
# or
ollama pull phi3:mini    # Faster on low-end hardware
```

### 2. Installation

```bash
git clone https://github.com/yourusername/InSightMail.git
cd InSightMail
pip install -r requirements.txt
```

Initialize the database:

```bash
cd backend
python -c "from db import db_manager; db_manager.create_tables()"
```

### 3. Run the Application

```bash
# Start the backend
cd backend
python -m uvicorn main:app --reload --port 8000

# In another terminal, start the UI
cd frontend
streamlit run app.py --server.port 8501
```

Now open:
- **Dashboard** → http://localhost:8501
- **API Docs** → http://localhost:8000/docs

## Importing Gmail Data

### Option 1: Google Takeout

1. Go to [takeout.google.com](https://takeout.google.com)
2. Select **Mail**
3. Export in JSON or EML format
4. Download and upload those files in the InSightMail dashboard

### Option 2: Gmail Search Export

Use a Gmail search like `(recruiter OR interview OR offer)` and export via browser extensions.

### Option 3: Gmail API (Advanced Users)

Connect Gmail API credentials for real-time sync.

## Using InSightMail

1. Go to **Email Upload** in the sidebar
2. Upload your exported Gmail files
3. Let the app parse and classify them
4. Explore the dashboard: timelines, conversion charts, and follow-up suggestions
5. Use the **"Ask My Inbox"** feature for natural-language queries such as:
   - "How many rejections in October?"
   - "Show me interview invites from tech companies."
   - "Which applications haven't received responses yet?"

## Configuration

Create a `.env` file from `env.example`:

```bash
OLLAMA_MODEL=mistral:7b
DATABASE_URL=sqlite:///data/insightmail.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Switch models anytime:

```bash
ollama pull phi3:mini
```

## Testing

Run tests to make sure everything's working:

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Docker Deployment

```bash
docker-compose up -d

# or

docker build -t insightmail .
docker run -p 8501:8501 -p 8000:8000 insightmail
```

Then visit:
- **Dashboard** → http://localhost:8501
- **API** → http://localhost:8000

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama not running | Run `ollama serve` |
| No emails detected | Check file format and Gmail address |
| Slow performance | Use the `phi3:mini` model |
| Search not working | Wait for embeddings to finish generating |

## Roadmap

- Live Gmail API sync
- LinkedIn and Indeed integrations
- Predictive analytics (e.g., response likelihood)
- Shared dashboards for career coaches
- Mobile companion app

## License

MIT License.

Built with FastAPI, Streamlit, ChromaDB, and Ollama.

## Community

- **Report issues** → [GitHub Issues](https://github.com/yourusername/InSightMail/issues)
- **Join discussions** → [GitHub Discussions](https://github.com/yourusername/InSightMail/discussions)
- **Documentation** → [Project Wiki](https://github.com/yourusername/InSightMail/wiki)

---

**Built for job seekers who want clarity without giving up privacy.**

*Your emails. Your data. Your insights.*
