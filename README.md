# Movie Recommender Submission

This project stays intentionally compact.

The main recommendation logic lives in `llm.py`. The deployment wrapper is `app.py`. The movie catalog is stored in `tmdb_top1000_movies.xlsx`.

## Submission Files

For the current submission bundle, include these files:

- `llm.py`
- `app.py`
- `requirements.txt`
- `tmdb_top1000_movies.xlsx`
- `README.md`

`llm.py` is the core grader-facing file. `app.py` is only needed if you are also submitting the API/deployment wrapper.

## Core Files

- `llm.py`: main recommender entrypoint
- `app.py`: FastAPI wrapper for deployment and API testing
- `requirements.txt`: Python dependencies
- `tmdb_top1000_movies.xlsx`: movie catalog used by the recommender

## What `llm.py` Returns

`llm.py` exposes `get_recommendation(preferences, history, history_ids)` and returns:

```python
{
    "tmdb_id": 123,
    "description": "A short recommendation blurb"
}
```

## How The Ranking System Works

The ranking pipeline has two stages: deterministic ranking first, then a constrained final choice.

### 1. Catalog loading

The system reads `tmdb_top1000_movies.xlsx`, converts each row into a movie object, and caches the result so repeated calls do not reload the spreadsheet.

By default, `llm.py` looks for `tmdb_top1000_movies.xlsx` in the same folder. It can also take an explicit spreadsheet path through the optional `data_file` argument or the CLI `--data-file` flag.

### 2. Preference parsing

The user prompt is parsed into structured signals such as:

- preferred genres
- avoided genres
- title exclusions
- language preferences
- country and studio hints
- runtime limits
- year constraints
- low-rated or bad-movie intent
- happy-ending intent

This parsing layer also handles negations like `not Marvel`, runtime prompts like `1 and a half hour`, and language prompts including Chinese requests.

### 3. Hard filtering

Before ranking, the system removes:

- movies already in the user's watch history
- movies that violate strict runtime limits
- movies that violate strict year constraints

### 4. Deterministic scoring

Each remaining movie gets a score based on a combination of:

- overlap between the prompt and movie tokens
- genre matches and genre avoidances
- language, country, and studio matches
- keyword and metadata matches
- history-based taste signals from the user's watched titles
- quality signals such as vote average, vote count, and popularity

The scorer also applies strong penalties for things the user explicitly ruled out.

For low-rated requests such as `worst movie ever` or `bad movie`, the scoring logic changes direction and intentionally favors lower-rated candidates instead of prestige picks.

### 5. Semantic reranking

After the first scoring pass, the model reranks the strongest candidates using semantic similarity on the top pool only. This helps recover good matches when the wording is broad or indirect.

### 6. Final shortlist selection

The top-ranked candidates become the shortlist.

- For absolute-worst prompts, the system returns the lowest-rated deterministic candidate directly.
- For normal prompts, the shortlist is sent to `gemma4:31b-cloud`, which must choose from that shortlist only.

### 7. Fallback behavior

If the LLM call fails, times out, or returns something invalid, the system falls back to the top deterministic candidate and writes a deterministic description.

## What `app.py` Does

`app.py` wraps `llm.py` in a FastAPI service so the recommender can be deployed or tested through HTTP.

Main routes:

- `GET /health`: health check
- `POST /recommend`: main recommendation endpoint

Request shape for `/recommend`:

```json
{
  "preferences": "I want a smart sci-fi movie with strong visuals",
  "history": ["Interstellar"],
  "history_ids": [157336]
}
```

## Environment

Required environment variable:

- `OLLAMA_API_KEY`

## Install

```powershell
pip install -r requirements.txt
```

## Run From Python

```python
from llm import get_recommendation

result = get_recommendation(
    preferences="I want a smart sci-fi movie with strong visuals",
    history=["Interstellar"],
    history_ids=[157336],
)

print(result)
```

To point to an explicit spreadsheet file:

```python
from llm import get_recommendation

result = get_recommendation(
  preferences="I want a smart sci-fi movie with strong visuals",
  history=["Interstellar"],
  history_ids=[157336],
  data_file="tmdb_top1000_movies.xlsx",
)
```

## Run From Terminal

```powershell
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336
```

With an explicit spreadsheet path:

```powershell
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336 --data-file tmdb_top1000_movies.xlsx
```

## Run As API

```powershell
uvicorn app:app --host 0.0.0.0 --port 8080
```

## Notes

- `llm.py` does not depend on other project Python files.
- `llm.py` reads the movie catalog from `.xlsx`, not from a CSV loader.
- `tmdb_top1000_movies.xlsx` should stay in the same folder as `llm.py` unless you pass a different spreadsheet path explicitly.
- `app.py` is optional for direct Python use, but required for deployment as a web service.
- The output is designed to match the assignment format: one `tmdb_id` and one short `description`.