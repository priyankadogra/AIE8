# Scout - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API Key

## Local Development

### Step 1: Install Backend Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### Step 2: Start the Backend

```bash
./start_backend.sh
```

Or manually:
```bash
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

Backend will be at: http://localhost:8000

### Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 4: Start the Frontend

```bash
./start_frontend.sh
```

Or manually:
```bash
npm run dev
```

Frontend will be at: http://localhost:3000

### Step 5: Configure and Use

1. Open http://localhost:3000
2. Click **"⚙️ Settings"**
3. Enter your **OpenAI API Key**
4. (Optional) Enter **Cohere API Key** for better retrieval
5. Click **"🔄 Prepare Data"** to process newsletters
6. Start asking questions!

## Example Questions

- "What events are happening this week?"
- "When is Spirit Day?"
- "Are there any upcoming deadlines?"
- "What should I bring for the field trip?"

## Troubleshooting

### Backend won't start
- Make sure you're in the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- Make sure you're in the `frontend/` directory
- Run `npm install` first
- Check that Node.js 18+ is installed: `node --version`

### "Failed to connect to server"
- Make sure backend is running on port 8000
- Check the API URL in Settings matches your backend

### No responses or empty results
- Click "🔄 Prepare Data" to extract events and build the index
- Make sure your API key is correct
- Check that PDF files exist in `data/newsletters/`

## Testing the API

Run the test script to verify everything works:

```bash
python test_api.py
```

## Next Steps

- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment to Vercel/Railway
- See [README.md](README.md) for full project documentation
- Add more newsletter PDFs to `data/newsletters/` and click "🔄 Prepare Data"

## Architecture

```
┌─────────────┐      HTTP/REST      ┌─────────────┐
│   React     │ ──────────────────> │   FastAPI   │
│  Frontend   │                     │   Backend   │
│ (Next.js)   │ <────────────────── │  (Python)   │
└─────────────┘      JSON           └─────────────┘
                                            │
                                            ▼
                                    ┌─────────────┐
                                    │   Qdrant    │
                                    │   Vector    │
                                    │     DB      │
                                    └─────────────┘
```

The frontend sends chat messages to the backend, which:
1. Extracts structured events from PDFs
2. Uses vector search (Qdrant) to find relevant context
3. Calls OpenAI agent to generate responses
4. Optionally uses Cohere for reranking results

## Need Help?

- Check the [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide
- Review [README.md](README.md) for project overview
- Open an issue on GitHub

