from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.access import require_pro_user
from app.models.training import Training
from app.models.user import User
from app.schemas.training import TrainingCreate, TrainingRead, TrainingUpdate

router = APIRouter(prefix="/training", tags=["training"])


@router.get("/", response_model=list[TrainingRead])
def list_training(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Training).where(Training.user_id == user.id).order_by(Training.created_at.desc())).all()
    return rows


@router.post("/", response_model=TrainingRead)
def create_training(payload: TrainingCreate, db: Session = Depends(get_db), user: User = Depends(require_pro_user)):
    now = datetime.utcnow()
    tr = Training(
        user_id=user.id,
        title=payload.title,
        assignee=payload.assignee,
        assigned_date=payload.assigned_date,
        completed_date=payload.completed_date,
        status=payload.status,
        created_at=now,
        updated_at=now,
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


@router.put("/{training_id}", response_model=TrainingRead)
def update_training(training_id: int, payload: TrainingUpdate, db: Session = Depends(get_db), user: User = Depends(require_pro_user)):
    tr = db.get(Training, training_id)
    if not tr or tr.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tr, field, value)
    tr.updated_at = datetime.utcnow()

    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr