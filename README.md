# Agentic DSA Mentor

A standalone multi-agent DSA learning application using LangGraph orchestration, Groq
inference, Qdrant retrieval, Voyage embeddings, and Streamlit.

## What It Understands

You can provide:

- A LeetCode URL: `https://leetcode.com/problems/longest-substring-without-repeating-characters/`
- A number: `Give me a hint for LeetCode 3`
- An explicit title: `LeetCode: Two Sum`
- A complete pasted problem statement
- Your code plus a request such as `review my code`

The dedicated Problem Resolver loads the problem before the orchestrator sends it to a Tutor,
Hint Coach, Code Reviewer, Interviewer, or Pattern Mapper.

## Model Selection

The Streamlit sidebar lets users select any configured Groq model. Configure the choices using
the comma-separated `GROQ_MODELS` environment variable. Model IDs change over time, so validate
and pin the models available in your Groq account before deployment.

## Run

```powershell
Copy-Item .env.example .env
# Add GROQ_API_KEY. Add VOYAGE_API_KEY to enable retrieval.

python -m pip install -e ".[dev]"
docker compose up -d
python scripts/ingest_knowledge.py
streamlit run app.py
```

Qdrant and Voyage are optional for the first chat run. Without `VOYAGE_API_KEY`, the app uses a
no-op retriever.

## Verify

```powershell
python -m pytest -q
python -m ruff check .
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the orchestration flow and package boundaries.
