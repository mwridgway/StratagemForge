from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...domain.demos.schemas import DemoCollection, DemoDetail, DemoProcessingStatus, DemoUploadResponse
from .. import deps

router = APIRouter(prefix="/api/demos", tags=["demos"])


@router.get("", response_model=DemoCollection)
def list_demos(
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_demo_service),
) -> DemoCollection:
    demos = service.list_demos(session)
    return DemoCollection(demos=demos, count=len(demos))


@router.get("/{demo_id}", response_model=DemoDetail)
def get_demo(
    demo_id: str,
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_demo_service),
) -> DemoDetail:
    demo = service.get_demo(session, demo_id)
    if not demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo not found")
    return DemoDetail.from_orm(demo)


@router.post("/upload", response_model=DemoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_demo(
    demo: UploadFile = File(...),
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_demo_service),
) -> DemoUploadResponse:
    try:
        stored, created = await service.upload_demo(demo, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    message = "Demo uploaded and processed" if created else "Demo already processed"
    return DemoUploadResponse.from_orm(stored).copy(update={"message": message})


@router.get("/{demo_id}/status", response_model=DemoProcessingStatus)
def processing_status(
    demo_id: str,
    session: Session = Depends(deps.get_db),
    service=Depends(deps.get_demo_service),
) -> DemoProcessingStatus:
    demo = service.get_demo(session, demo_id)
    if not demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo not found")

    status_message = "processed" if demo.status == "processed" else "pending"
    return DemoProcessingStatus(
        demo_id=demo.id,
        status=demo.status,
        message=f"Demo is {status_message}",
        processed_at=demo.processed_at,
        processed_path=demo.processed_path,
        extra_metadata=demo.extra_metadata or {},
    )
