from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...domain.analysis.schemas import AnalysisRequest, AnalysisResult
from ...domain.demos.schemas import DemoCollection
from .. import deps

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/demos", response_model=DemoCollection)
def list_available_demos(
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_analysis_service),
) -> DemoCollection:
    demos = service.list_available_demos(session)
    return DemoCollection(demos=demos, count=len(demos))


@router.post("", response_model=AnalysisResult)
def run_analysis(
    request: AnalysisRequest,
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_analysis_service),
) -> AnalysisResult:
    try:
        return service.run_analysis(session, request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
