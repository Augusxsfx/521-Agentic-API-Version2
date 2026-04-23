from __future__ import annotations

import importlib
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import llm


ROOT = Path(__file__).resolve().parent
PARSER_CASES_PATH = ROOT / "eval_parser_cases.json"
STABILITY_CASES_PATH = ROOT / "eval_stability_cases.json"

app = FastAPI(
    title="BAMS 521 Movie Recommender",
    description="Deployable API wrapper around the llm.py movie recommender.",
    version="1.0.0",
)


class RecommendationRequest(BaseModel):
    preferences: str = Field(..., min_length=1, description="Free-text movie request.")
    history: list[str] = Field(default_factory=list, description="Previously watched movie titles.")
    history_ids: list[int] = Field(default_factory=list, description="Previously watched TMDB ids.")


class RegressionRequest(BaseModel):
    case_names: list[str] = Field(default_factory=list)
    limit: int | None = Field(default=None, ge=1)
    show_only_failures: bool = False


def _load_optional_module(module_name: str, required_path: Path):
    if not required_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{module_name} is not available in this deployment.",
        )
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"{module_name} is not available in this deployment.",
        ) from exc


def _filter_case_list(cases: list[dict], case_names: list[str] | None = None, limit: int | None = None) -> list[dict]:
    if case_names:
        wanted = set(case_names)
        cases = [case for case in cases if case["name"] in wanted]
    if limit is not None:
        cases = cases[:limit]
    return cases


@app.get("/")
def read_root() -> dict[str, object]:
    routes = ["/health", "/recommend"]
    if PARSER_CASES_PATH.exists():
        routes.append("/regressions/parser")
    if STABILITY_CASES_PATH.exists():
        routes.append("/regressions/stability")
    return {
        "service": "bams-521-movie-recommender",
        "status": "ok",
        "routes": routes,
    }


@app.get("/health")
def read_health() -> dict[str, object]:
    return {
        "status": "ok",
        "model": llm.MODEL,
        "data_path": str(llm.DATA_PATH.name),
    }


@app.get("/kaithhealthcheck")
def read_kaith_healthcheck() -> dict[str, object]:
    return read_health()


@app.post("/recommend")
def recommend(request: RecommendationRequest) -> dict[str, object]:
    try:
        return llm.get_recommendation(request.preferences, request.history, request.history_ids)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {type(exc).__name__}: {exc}") from exc


@app.post("/regressions/parser")
def run_parser_regressions(request: RegressionRequest) -> dict[str, object]:
    try:
        eval_parser_regressions = _load_optional_module("eval_parser_regressions", PARSER_CASES_PATH)
        cases = eval_parser_regressions.load_cases(PARSER_CASES_PATH)
        cases = _filter_case_list(cases, case_names=request.case_names, limit=request.limit)
        results = eval_parser_regressions.run_cases(cases)
        visible = [result for result in results if not request.show_only_failures or not result["passed"]]
        return {
            "cases_run": len(results),
            "cases_passed": sum(1 for result in results if result["passed"]),
            "cases_failed": sum(1 for result in results if not result["passed"]),
            "results": visible,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Parser regressions failed: {type(exc).__name__}: {exc}") from exc


@app.post("/regressions/stability")
def run_stability_regressions(request: RegressionRequest) -> dict[str, object]:
    try:
        eval_output_stability = _load_optional_module("eval_output_stability", STABILITY_CASES_PATH)
        cases = eval_output_stability.load_cases(STABILITY_CASES_PATH)
        cases = _filter_case_list(cases, case_names=request.case_names, limit=request.limit)
        results = eval_output_stability.run_cases(cases)
        visible = [result for result in results if not request.show_only_failures or not result["passed"]]
        return {
            "cases_run": len(results),
            "cases_passed": sum(1 for result in results if result["passed"]),
            "cases_failed": sum(1 for result in results if not result["passed"]),
            "results": visible,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Stability regressions failed: {type(exc).__name__}: {exc}") from exc