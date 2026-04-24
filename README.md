# Movie Recommender Submission

This project stays intentionally compact.

The main recommendation logic lives in `llm.py`. The deployment wrapper is `app.py`. The movie catalog is stored in `tmdb_top1000_movies.csv`.

## Submission Files

For the current submission bundle, include these files:

- `llm.py`
- `app.py`
- `requirements.txt`
- `tmdb_top1000_movies.csv`
- `README.md`

`llm.py` is the core grader-facing file. `app.py` is only needed if you are also submitting the API/deployment wrapper.

## Core Files

- `llm.py`: main recommender entrypoint
- `app.py`: FastAPI wrapper for deployment and API testing
- `requirements.txt`: Python and API dependencies
- `tmdb_top1000_movies.csv`: movie catalog used by the recommender

## Output Format

`llm.py` exposes `get_recommendation(preferences, history, history_ids)` and returns:

```python
{
    "tmdb_id": 123,
    "description": "A short recommendation blurb"
}
```

## How `llm.py` Works

The ranking pipeline has two stages: deterministic ranking first, then a constrained final choice.

### 1. Catalog loading

The system reads `tmdb_top1000_movies.csv`, converts each row into a movie object, and caches the result so repeated calls do not reload the catalog.

By default, `llm.py` looks for `tmdb_top1000_movies.csv` in the same folder. It can also take an explicit CSV path through the optional `data_file` argument or the CLI `--data-file` flag.

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

## Environment

Required environment variable:

- `OLLAMA_API_KEY`

Optional environment variable:

- `MOVIE_DATA_PATH`: override the default CSV path

## Install

### PowerShell

```powershell
Set-Location "h:/521 files"
pip install -r requirements.txt
```

### CMD

```cmd
cd /d h:\521 files
pip install -r requirements.txt
```

## Use `llm.py` From Python

Use this when you want to call the recommender directly from a Python script, notebook, or interactive Python terminal.

```python
import os
os.environ["OLLAMA_API_KEY"] = "YOUR_OLLAMA_KEY"

from llm import get_recommendation

result = get_recommendation(
    preferences="I want a smart sci-fi movie with strong visuals",
    history=["Interstellar"],
    history_ids=[157336],
)

print(result)
```

With an explicit CSV file:

```python
import os
os.environ["OLLAMA_API_KEY"] = "YOUR_OLLAMA_KEY"

from llm import get_recommendation

result = get_recommendation(
    preferences="I want a smart sci-fi movie with strong visuals",
    history=["Interstellar"],
    history_ids=[157336],
    data_file="tmdb_top1000_movies.csv",
)

print(result)
```

## Run `llm.py` From PowerShell

Use this when you want to test the recommender from a Windows PowerShell terminal.

```powershell
Set-Location "h:/521 files"
$env:OLLAMA_API_KEY="YOUR_OLLAMA_KEY"
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336
```

With an explicit CSV path:

```powershell
Set-Location "h:/521 files"
$env:OLLAMA_API_KEY="YOUR_OLLAMA_KEY"
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336 --data-file tmdb_top1000_movies.csv
```

## Run `llm.py` From CMD

Use this when you want the same direct test flow in Command Prompt.

```cmd
cd /d h:\521 files
set OLLAMA_API_KEY=YOUR_OLLAMA_KEY
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336
```

With an explicit CSV path:

```cmd
cd /d h:\521 files
set OLLAMA_API_KEY=YOUR_OLLAMA_KEY
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336 --data-file tmdb_top1000_movies.csv
```

## Run `test.py`

### Python terminal or notebook

```python
import os
os.environ["OLLAMA_API_KEY"] = "YOUR_OLLAMA_KEY"

import test
test.main()
```

### PowerShell

```powershell
Set-Location "h:/521 files"
$env:OLLAMA_API_KEY="YOUR_OLLAMA_KEY"
python test.py
```

### CMD

```cmd
cd /d h:\521 files
set OLLAMA_API_KEY=YOUR_OLLAMA_KEY
python test.py
```

## Use The API Locally

`app.py` wraps `llm.py` in a FastAPI service so the recommender can be deployed or tested through HTTP.

Main routes:

- `GET /health`
- `POST /recommend`

Start the API locally:

```powershell
Set-Location "h:/521 files"
$env:OLLAMA_API_KEY="YOUR_OLLAMA_KEY"
uvicorn app:app --host 0.0.0.0 --port 8080
```

Request body for `/recommend`:

```json
{
  "preferences": "I want a smart sci-fi movie with strong visuals",
  "history": ["Interstellar"],
  "history_ids": [157336]
}
```

Python request example:

```python
import requests

response = requests.post(
    "http://127.0.0.1:8080/recommend",
    json={
        "preferences": "I want a smart sci-fi movie with strong visuals",
        "history": ["Interstellar"],
        "history_ids": [157336],
    },
    timeout=30,
)

print(response.status_code)
print(response.json())
```

PowerShell request example:

```powershell
$body = @{
  preferences = "I want a smart sci-fi movie with strong visuals"
  history = @("Interstellar")
  history_ids = @(157336)
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/recommend" -ContentType "application/json" -Body $body
```

CMD request example:

```cmd
curl.exe -X POST http://127.0.0.1:8080/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"preferences\":\"I want a smart sci-fi movie with strong visuals\",\"history\":[\"Interstellar\"],\"history_ids\":[157336]}"
```

## Deploy On Leapcell

Use `app.py` as the entrypoint.

Suggested setup:

- Runtime: Python 3.10+
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Required environment variable: `OLLAMA_API_KEY`

Files to include in the deployment:

- `app.py`
- `llm.py`
- `requirements.txt`
- `tmdb_top1000_movies.csv`

Optional regression files if you want the regression endpoints available:

- `eval_parser_regressions.py`
- `eval_output_stability.py`
- `eval_parser_cases.json`
- `eval_stability_cases.json`

After deployment, verify the service:

```powershell
Invoke-RestMethod -Method Get -Uri "https://YOUR-LEAPCELL-URL/health"
```

Then request a recommendation:

```powershell
$body = @{
  preferences = "I want a smart sci-fi movie with strong visuals"
  history = @("Interstellar")
  history_ids = @(157336)
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "https://YOUR-LEAPCELL-URL/recommend" -ContentType "application/json" -Body $body
```

## Notes

- `llm.py` does not depend on other project Python files.
- `llm.py` reads the movie catalog from CSV only.
- `tmdb_top1000_movies.csv` should stay in the same folder as `llm.py` unless you pass a different CSV path explicitly.
- `app.py` is optional for direct Python use, but required for deployment as a web service.
- The output is designed to match the assignment format: one `tmdb_id` and one short `description`.