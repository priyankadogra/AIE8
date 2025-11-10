# Scout Architecture

## System Overview

Scout is a school events assistant with a React frontend and FastAPI backend that uses RAG (Retrieval Augmented Generation) and LangChain agents.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  React Frontend                          │
│                   (Next.js)                              │
│                                                           │
│  - Chat Interface                                        │
│  - Settings Panel (API Keys)                            │
│  - Message History                                       │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
                         │ (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│                   (app/api.py)                           │
│                                                           │
│  Endpoints:                                              │
│  - POST /api/chat                                        │
│  - POST /api/prepare                                     │
│  - GET  /api/health                                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              LangChain Agent Layer                       │
│                  (app/agent.py)                          │
│                                                           │
│  - Question Understanding                                │
│  - Tool Selection                                        │
│  - Response Generation                                   │
└─────────┬──────────────────────────┬────────────────────┘
          │                          │
          ▼                          ▼
┌──────────────────┐      ┌──────────────────────┐
│  Search Events   │      │  Search Documents    │
│   Tool           │      │    Tool (RAG)        │
│ (Structured)     │      │  (Vector Search)     │
└─────────┬────────┘      └──────────┬───────────┘
          │                          │
          │                          ▼
          │               ┌──────────────────────┐
          │               │   Qdrant Vector DB   │
          │               │   (Embeddings)       │
          │               └──────────┬───────────┘
          │                          │
          │                          ▼
          │               ┌──────────────────────┐
          │               │  Cohere Reranking    │
          │               │    (Optional)        │
          │               └──────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│              Data Processing Layer                       │
│          (app/data_processing.py, app/rag.py)           │
│                                                           │
│  - PDF Extraction                                        │
│  - Event Parsing                                         │
│  - Deduplication                                         │
│  - Text Chunking                                         │
│  - Embedding Generation                                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Storage                            │
│                                                           │
│  - Newsletter PDFs (data/newsletters/)                   │
│  - Vector Index (Qdrant)                                │
│  - Extracted Events (in-memory)                         │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (React/Next.js)

**Location:** `frontend/`

**Responsibilities:**
- User interface and interaction
- API key management (browser-only)
- Chat history display
- Settings configuration
- HTTP requests to backend

**Technology:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Hooks

### Backend API (FastAPI)

**Location:** `app/api.py`

**Responsibilities:**
- HTTP endpoint routing
- Request/response handling
- CORS management
- API key validation
- Thin wrapper around existing logic

**Endpoints:**
- `POST /api/chat` - Process user messages
- `POST /api/prepare` - Initialize data (extract events, build index)
- `POST /api/build-index` - Build/rebuild RAG index
- `GET /api/health` - Check system status

### Agent Layer (LangChain)

**Location:** `app/agent.py`

**Responsibilities:**
- Intent understanding
- Tool selection and orchestration
- Response generation
- Context management

**Tools:**
1. **SearchEventsTool** - Query structured events by date/keywords
2. **SearchDocumentsTool** - RAG search through newsletter content

**Flow:**
```
User Question
    ↓
Parse Intent (what, when, where)
    ↓
Select Tools (events vs documents)
    ↓
Execute Tools (parallel if possible)
    ↓
Generate Response (with context)
    ↓
Return to User
```

### RAG System

**Location:** `app/rag.py`, `app/cohere_rag.py`

**Pipeline:**
```
1. PDF → Text Extraction (pypdf)
2. Text → Chunks (400 chars, 100 overlap)
3. Chunks → Embeddings (OpenAI text-embedding-3-small)
4. Embeddings → Vector DB (Qdrant)
5. Query → Search (cosine similarity)
6. Results → Rerank (Cohere, optional)
7. Top-K → Context for LLM
```

**Vector Database:**
- **Engine:** Qdrant (in-memory mode)
- **Collection:** `scout_newsletters`
- **Dimension:** 1536 (OpenAI embeddings)
- **Metric:** Cosine similarity

### Data Processing

**Location:** `app/data_processing.py`, `app/tools.py`

**Event Extraction:**
```
PDF Newsletter
    ↓
Text Extraction
    ↓
LLM Parsing (GPT-4o-mini)
    ↓
Structured Events (Pydantic models)
    ↓
Deduplication
    ↓
In-Memory Storage
```

**Event Schema:**
- Title, Start/End Date, Location
- Grades, Audience
- Actions (what to bring/do)
- Deadlines (RSVP, payment)
- Source PDF reference
- Confidence score

## Data Flow

### Chat Message Flow

```
1. User types message in frontend
2. Frontend sends POST to /api/chat with:
   - message
   - openai_api_key
   - cohere_api_key (optional)
   - use_reranking (boolean)

3. Backend sets API keys in environment

4. Backend calls agent.ask(message, pdf_folder)

5. Agent analyzes message:
   - Date query? → Search events by date
   - Event query? → Search events by keyword
   - Instructions? → RAG search documents

6. Agent executes tools:
   - SearchEventsTool: Filter structured events
   - SearchDocumentsTool: Vector search + optional reranking

7. Agent generates response using:
   - Matched events
   - Retrieved document snippets
   - LLM synthesis

8. Backend returns response to frontend

9. Frontend displays in chat
```

### Data Preparation Flow

```
1. User clicks "🔄 Prepare Data"

2. Frontend sends POST to /api/prepare

3. Backend calls ensure_prepared():
   a. Read PDFs from data/newsletters/
   b. Extract events from each PDF (LLM)
   c. Deduplicate events
   d. Build RAG index:
      - Chunk text
      - Generate embeddings
      - Index in Qdrant

4. Backend returns success

5. System ready for queries
```

## Technology Stack

### Frontend
- **Framework:** Next.js 14
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** React Hooks (useState)
- **HTTP:** Fetch API

### Backend
- **Framework:** FastAPI
- **Server:** Uvicorn (ASGI)
- **Language:** Python 3.9+
- **Agent:** LangChain
- **Vector DB:** Qdrant
- **PDF Processing:** pypdf
- **Date Parsing:** dateparser, python-dateutil

### AI/ML
- **LLM:** OpenAI GPT-4o-mini
- **Embeddings:** OpenAI text-embedding-3-small
- **Reranking:** Cohere (optional)
- **Agent Framework:** LangChain

## Security Considerations

### Current Implementation
- ✅ API keys passed per-request (not stored server-side)
- ✅ API keys stored in browser session only
- ✅ CORS enabled (configure for production)
- ✅ No sensitive data in repository

### Production Recommendations
- 🔒 Use environment variables for API keys
- 🔒 Implement rate limiting
- 🔒 Add authentication (OAuth, JWT)
- 🔒 Restrict CORS to specific origins
- 🔒 Use HTTPS only
- 🔒 Monitor API usage and costs

## Scalability

### Current Limitations
- In-memory vector DB (Qdrant)
- In-memory event storage
- Single-instance deployment

### Scaling Options
1. **Qdrant Cloud** - Persistent, distributed vector DB
2. **Redis** - Distributed caching layer
3. **PostgreSQL** - Persistent event storage
4. **Load Balancer** - Multiple backend instances
5. **CDN** - Frontend asset distribution

## Deployment Targets

### Supported Platforms
- ✅ Vercel (frontend + backend)
- ✅ Railway (backend alternative)
- ✅ Local development
- 🔄 AWS/GCP/Azure (with modifications)

### Deployment Strategy
```
Development:
  Frontend: localhost:3000
  Backend: localhost:8000

Production:
  Frontend: Vercel (https://scout-frontend.vercel.app)
  Backend: Vercel/Railway (https://scout-api.vercel.app)
```

## Monitoring & Observability

### Recommended Metrics
- API response times
- LLM token usage
- Vector search latency
- Error rates
- User sessions
- Query types

### Tools
- Vercel Analytics
- OpenAI Usage Dashboard
- Cohere Dashboard
- Custom logging (FastAPI middleware)

## Future Enhancements

### Planned Features
- 📧 Email notifications for events
- 📅 Direct calendar integration (Google, Apple)
- 🔔 Deadline reminders
- 👥 Multi-school support
- 🔐 User authentication
- 💾 Persistent storage
- 📊 Analytics dashboard
- 🌐 Internationalization

### Technical Improvements
- GraphQL API
- WebSocket for real-time updates
- Streaming responses
- Advanced caching
- A/B testing framework
- Automated testing (E2E)

## Development Workflow

```
1. Make changes locally
2. Test backend: python test_api.py
3. Test frontend: npm run dev
4. Commit changes
5. Deploy backend: vercel (from root)
6. Deploy frontend: vercel (from frontend/)
7. Verify deployment
8. Monitor errors
```

## References

- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment instructions
- [CHANGES.md](CHANGES.md) - What was changed
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Deployment checklist

