# Movie Recommender Submission

This submission is intentionally simple.

The main file is `llm.py`, and the only project files it needs are `requirements.txt` and `tmdb_top1000_movies.xlsx`.

## Required Files

- `llm.py`: main recommender entrypoint
- `requirements.txt`: Python dependencies
- `tmdb_top1000_movies.xlsx`: movie catalog used by the recommender

## What `llm.py` Does

`llm.py` exposes `get_recommendation(preferences, history, history_ids)` and returns a dictionary with two keys:

```python
{
    "tmdb_id": 123,
    "description": "A short recommendation blurb"
}
```

The recommender:

1. Loads the provided movie catalog from `tmdb_top1000_movies.xlsx`
2. Removes movies already seen by the user
3. Parses the user's request and ranks candidates deterministically
4. Uses `gemma4:31b-cloud` through Ollama Cloud to choose from the shortlist
5. Falls back to a deterministic recommendation if needed

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

## Run From Terminal

```powershell
python llm.py --preferences "I want a smart sci-fi movie with strong visuals" --history Interstellar --history-ids 157336
```

## Notes

- `llm.py` does not depend on other project Python files.
- `tmdb_top1000_movies.xlsx` should stay in the same folder as `llm.py`.
- The output is designed to match the assignment format: one `tmdb_id` and one short `description`.