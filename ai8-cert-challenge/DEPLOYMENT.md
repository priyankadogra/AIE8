# Scout - Deployment Guide

This guide will help you deploy the Scout app with a React frontend and FastAPI backend.

## Architecture

- **Frontend**: React (Next.js) - deployed on Vercel
- **Backend**: FastAPI (Python) - can be deployed on Vercel, Railway, or any Python hosting platform
- **Data**: Newsletter PDFs stored in `data/newsletters/`

## Quick Start (Local Development)

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the FastAPI backend
cd /path/to/ai8-cert-challenge
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Configure API Keys

1. Open the frontend at `http://localhost:3000`
2. Click "⚙️ Settings" in the top right
3. Enter your OpenAI API key (required)
4. Optionally enter your Cohere API key for better retrieval
5. Click "🔄 Prepare Data" to process the newsletters

### 4. Start Chatting!

Ask questions like:
- "What events are happening this week?"
- "When is Spirit Day?"
- "Are there any upcoming deadlines?"

## Deployment

### Deploy Backend to Vercel

1. **Push your code to GitHub**

2. **Deploy to Vercel**:
   ```bash
   cd /path/to/ai8-cert-challenge
   vercel
   ```

3. **Configure Environment** (optional):
   - You can set environment variables in Vercel dashboard if needed
   - API keys are passed from the frontend for security

4. **Note the backend URL** (e.g., `https://your-app.vercel.app`)

### Deploy Frontend to Vercel

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Update API URL in your frontend** (optional):
   - Edit `app/page.tsx` and change the default `apiUrl` to your backend URL
   - Or users can update it in Settings

3. **Deploy to Vercel**:
   ```bash
   vercel
   ```

4. **Access your app** at the provided URL!

## Alternative: Deploy Backend to Railway

Railway is great for Python apps and offers free tier:

1. **Create account at [railway.app](https://railway.app)**

2. **Deploy from GitHub**:
   - Connect your GitHub repository
   - Railway will auto-detect Python
   - Set start command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`

3. **Note the backend URL** and update it in your frontend

## Configuration

### Backend Configuration (`config.py`)

- `PDF_DIR`: Location of newsletter PDFs (default: `data/newsletters`)
- `EMBEDDING_MODEL`: OpenAI embedding model (default: `text-embedding-3-small`)
- `AGENT_MODEL`: LLM model for agent (default: `gpt-4o-mini`)

### Frontend Configuration

- Users enter API keys directly in the UI (more secure)
- API URL can be changed in Settings panel
- Supports both standard retrieval and Cohere reranking

## Adding More Newsletters

1. Add PDF files to `data/newsletters/` directory
2. Click "🔄 Prepare Data" in the frontend to reprocess

## Troubleshooting

### Backend Issues

**Error: "No module named 'app'"**
- Make sure you're running from the project root directory
- Check that `app/` directory exists with `__init__.py`

**Error: "Collection not found"**
- Click "🔄 Prepare Data" to initialize the index
- This extracts events and builds the RAG index

### Frontend Issues

**Error: "Failed to connect to server"**
- Check that backend is running
- Verify the API URL in Settings matches your backend
- Check CORS settings if deploying to different domains

**Error: "Please enter your OpenAI API key"**
- Add your API key in the Settings panel
- API keys are stored in browser session only (not persisted)

## API Endpoints

The backend exposes these endpoints:

- `POST /api/chat` - Send a message and get a response
- `POST /api/prepare` - Prepare data (extract events, build index)
- `POST /api/build-index` - Build RAG index
- `GET /api/health` - Check RAG index health
- `GET /` - Health check

## Security Notes

- API keys are passed from frontend to backend per request
- Keys are not stored on the server
- In production, consider using environment variables for API keys
- Update CORS settings in `app/api.py` to restrict origins

## Tech Stack

**Backend**:
- FastAPI - Fast Python web framework
- LangChain - Agent framework
- Qdrant - Vector database
- OpenAI - LLM and embeddings
- Cohere - Optional reranking

**Frontend**:
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Vercel - Hosting platform

## Need Help?

- Check the main [README.md](README.md) for project overview
- Review the [API documentation](http://localhost:8000/docs) when running locally
- Open an issue on GitHub

## License

[Add your license here]

