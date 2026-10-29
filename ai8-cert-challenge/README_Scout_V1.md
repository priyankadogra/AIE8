# Scout - School Newsletter RAG Agent

## The Problem

Parents get flooded with school emails and newsletters. Important dates like picture day, field trips, minimum days, spirit days get buried in long messages that arrive at odd hours. Manually tracking them is error-prone and time-consuming.

## What Scout Does

Scout is a conversational RAG agent that lets parents ask natural language questions about their school's communications. Instead of reading every newsletter, a parent can ask "When is Spirit Day?" or "Do I need to bring anything tomorrow?" and get an accurate answer pulled directly from their school's emails and PDFs.

## Architecture

School PDFs → Chunking (800 char / 100 char overlap) → Embeddings → Qdrant Vector DB → Cohere Rerank → GPT-4o-mini → Answer

**Stack:**

- **Frontend:** Streamlit
- **LLM:** OpenAI GPT-4o-mini
- **Embeddings:** OpenAI text-embedding-3-small
- **Vector DB:** Qdrant (in-memory)
- **Reranking:** Cohere Rerank
- **Evaluation:** RAGAS
- **PDF parsing:** PyPDF

## Evaluation Results

Evaluated using RAGAS on a manually curated test set.

**Naive Retrieval:**

- Faithfulness: Low - answers not always grounded in retrieved context
- Answer Relevancy: 0.8 - responses address the question well
- Context Precision: 0.5
- Context Recall: 0.5

**With Cohere Reranking (top 15 fetched, reranked to top 5):**

- Marginal improvement in answer relevancy (+0.1%)
- No material change in precision or recall

**Key insight:** Answer generation is good. The bottleneck is retrieval. Fixed-size chunking breaks apart event names, dates, and instructions the exact structures parents care about.

## What I Learned

This version revealed a fundamental mismatch between chunking strategy and the data structure. School newsletters aren't prose they're lists of events with dates, times, and instructions. Chunking them at fixed character sizes fragments exactly the information the agent needs to retrieve accurately.

This led directly to a full rebuild. See Scout v2 for the two-stage LLM pipeline approach.

## Running Locally

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

School newsletters as PDFs go in `data/`. RAGAS evaluation scripts are in `evaluation/`.
