from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.access import require_pro_user
from app.models.incident import Incident
from app.models.training import Training
from app.models.user import User
from app.services.pdf import generate_audit_binder_pdf

router = APIRouter(prefix="/export", tags=["export"]) 


@router.post("/audit-binder", response_class=Response)
def export_audit_binder(db: Session = Depends(get_db), user: User = Depends(require_pro_user)):
    incidents = db.scalars(select(Incident).where(Incident.user_id == user.id).order_by(Incident.created_at.desc())).all()
    trainings = db.scalars(select(Training).where(Training.user_id == user.id).order_by(Training.created_at.desc())).all()

    incidents_payload = [
        {
            "title": inc.title,
            "status": inc.status,
            "incident_date": inc.incident_date.isoformat(),
        }
        for inc in incidents
    ]
    trainings_payload = [
        {
            "title": tr.title,
            "assignee": tr.assignee,
            "status": tr.status,
            "assigned_date": tr.assigned_date.isoformat(),
        }
        for tr in trainings
    ]

    pdf_bytes = generate_audit_binder_pdf(user_email=user.email, incidents=incidents_payload, trainings=trainings_payload)
    headers = {"Content-Disposition": "attachment; filename=hazero-audit-binder.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)