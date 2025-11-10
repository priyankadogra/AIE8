# AI8 Certification Challenge - School Events Extractor

This project extracts school events from newsletter PDFs and converts them into structured formats (JSON, ICS calendar files).

## Features

- PDF text extraction from school newsletters
- AI-powered event extraction using OpenAI
- Date parsing and timezone handling (America/Los_Angeles)
- Event deduplication
- iCalendar (.ics) file generation for easy import into calendar apps
- Filter events by grade level and date range
- Identify upcoming deadlines

## Setup

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai8-cert-challenge
```

2. Install dependencies using `uv`:
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

3. Set up your OpenAI API key:
   - The notebook will prompt you for your API key when you run it
   - Or set it as an environment variable: `export OPENAI_API_KEY=your_key_here`

## Usage

### Option 1: React Frontend (Recommended for Deployment)

1. Place your newsletter PDFs in the `data/newsletters/` directory

2. Start the backend:
```bash
./start_backend.sh
# or manually: uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

3. In a new terminal, start the frontend:
```bash
cd frontend
npm install  # first time only
./start_frontend.sh
# or manually: npm run dev
```

4. Open http://localhost:3000 and enter your API keys in Settings

### Option 2: Streamlit Interface

1. Place your newsletter PDFs in the `data/newsletters/` directory

2. Install dependencies

3. Run the app: `uv run streamlit run app/streamlit_app.py`

## Project Structure

```
ai8-cert-challenge/
├── app/
│   ├── agent.py           # LangChain agent logic
│   ├── api.py             # FastAPI backend (NEW)
│   ├── cohere_rag.py      # Cohere reranking
│   ├── data_processing.py # Event extraction
│   ├── rag.py             # Vector search
│   ├── streamlit_app.py   # Streamlit interface
│   └── tools.py           # Agent tools
├── frontend/              # React frontend (NEW)
│   ├── app/
│   │   ├── page.tsx       # Main chat interface
│   │   └── layout.tsx     # App layout
│   └── package.json       # Node dependencies
├── data/
│   └── newsletters/       # Place your PDF newsletters here
├── evaluation/            # RAGAS evaluation
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md          # Deployment guide (NEW)
└── README.md             # This file
```

## Dependencies

### Backend (Python)
- `fastapi` & `uvicorn` - API backend
- `pypdf` - PDF text extraction
- `python-dateutil` & `dateparser` - Date parsing
- `pydantic` - Data validation
- `openai` - AI-powered event extraction
- `cohere` - Reranking (optional)
- `langchain` - Agent framework
- `qdrant-client` - Vector database
- `streamlit` - Alternative web interface
- `tqdm` - Progress bars

### Frontend (Node.js)
- `next` - React framework
- `react` - UI library
- `tailwindcss` - Styling

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions for:
- Vercel (frontend & backend)
- Railway (backend alternative)
- Local development setup

## Timezone

Events are processed in the `America/Los_Angeles` timezone by default.

## License

[Add your license here]

