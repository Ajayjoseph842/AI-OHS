from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.access import require_pro_user
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Incident).where(Incident.user_id == user.id).order_by(Incident.created_at.desc())).all()
    return rows


@router.post("/", response_model=IncidentRead)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db), user: User = Depends(require_pro_user)):
    now = datetime.utcnow()
    inc = Incident(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        incident_date=payload.incident_date,
        status=payload.status,
        created_at=now,
        updated_at=now,
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


@router.put("/{incident_id}", response_model=IncidentRead)
def update_incident(incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db), user: User = Depends(require_pro_user)):
    inc = db.get(Incident, incident_id)
    if not inc or inc.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inc, field, value)
    inc.updated_at = datetime.utcnow()

    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc