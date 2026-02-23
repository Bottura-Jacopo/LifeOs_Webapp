from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import get_current_user
from app.models.event import Event
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary")
def summary(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Event).filter(Event.user_id == current_user.id)

    if from_ is not None:
        q = q.filter(Event.start_time >= from_)

    if to is not None:
        q = q.filter(Event.start_time <= to)

    events = q.all()

    # Calcolo semplice: somma durata per type (solo se end_time esiste)
    totals_seconds: dict[str, int] = {}
    counts: dict[str, int] = {}

    for e in events:
        counts[e.type] = counts.get(e.type, 0) + 1

        if e.end_time is None:
            continue
        duration = (e.end_time - e.start_time).total_seconds()
        if duration < 0:
            continue

        totals_seconds[e.type] = totals_seconds.get(e.type, 0) + int(duration)

    totals_hours = {k: round(v / 3600, 2) for k, v in totals_seconds.items()}

    return {
        "range": {"from": from_, "to": to},
        "counts": counts,
        "hours_by_type": totals_hours,
    }