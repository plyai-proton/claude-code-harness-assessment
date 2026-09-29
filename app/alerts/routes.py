from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.alerts import service
from app.alerts.models import Notification
from app.shared.auth import get_current_user
from app.staff.models import User

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[Notification])
def list_alerts(user: CurrentUser) -> list[Notification]:
    return service.list_alerts_for_user(user.id)
