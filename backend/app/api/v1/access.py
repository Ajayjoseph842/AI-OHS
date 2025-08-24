from datetime import date, timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User


TRIAL_DAYS = 30


def require_pro_user(user: User = Depends(get_current_user)) -> User:
    if user.is_paid:
        return user
    # Trial window check
    if user.trial_start is not None:
        if date.today() <= user.trial_start + timedelta(days=TRIAL_DAYS):
            return user
    raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Pro subscription required")