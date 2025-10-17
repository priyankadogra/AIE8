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

1. Place your newsletter PDFs in the `data/newsletters/` directory

2. Open and run the `school_events.ipynb` notebook:
```bash
uv run jupyter lab school_events.ipynb
```

3. Follow the notebook cells to:
   - Extract events from PDFs
   - Filter and deduplicate events
   - Export to calendar format

## Project Structure

```
ai8-cert-challenge/
├── school_events.ipynb    # Main notebook with event extraction logic
├── data/
│   └── newsletters/       # Place your PDF newsletters here
├── app/                   # Application code (future)
├── pyproject.toml         # Project dependencies
└── README.md             # This file
```

## Dependencies

- `pypdf` - PDF text extraction
- `python-dateutil` & `dateparser` - Date parsing
- `pydantic` - Data validation
- `icalendar` - Calendar file generation
- `openai` - AI-powered event extraction
- `streamlit` - Web interface (future)
- `tqdm` - Progress bars

## Timezone

Events are processed in the `America/Los_Angeles` timezone by default.

## License

[Add your license here]

