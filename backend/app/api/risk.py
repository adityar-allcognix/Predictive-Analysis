from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas.risk import EvaluateRiskRequest, RiskEvaluationResponse
from app.services.risk_service import evaluate_policy_risk, get_latest_evaluation

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/evaluate", response_model=RiskEvaluationResponse)
async def post_risk_evaluate(payload: EvaluateRiskRequest) -> RiskEvaluationResponse:
    try:
        return await evaluate_policy_risk(payload.policy_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logging.exception("Unhandled error in POST /risk/evaluate")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/{policy_number}", response_model=RiskEvaluationResponse)
async def get_risk_by_policy(policy_number: str) -> RiskEvaluationResponse:
    try:
        return await get_latest_evaluation(policy_number)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logging.exception("Unhandled error in GET /risk/{policy_number}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
