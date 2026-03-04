from datetime import datetime, timezone, time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from typing import Optional

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

    totals_seconds: dict[str, int] = {}
    counts: dict[str, int] = {}

    now = datetime.now(timezone.utc)

    for e in events:
        counts[e.type] = counts.get(e.type, 0) + 1

        end = e.end_time or now

        duration = (end - e.start_time).total_seconds()
        if duration < 0:
            continue

        totals_seconds[e.type] = totals_seconds.get(e.type, 0) + int(duration)

    totals_hours = {k: round(v / 3600, 2) for k, v in totals_seconds.items()}

    return {
        "range": {"from": from_, "to": to},
        "counts": counts,
        "hours_by_type": totals_hours,
    }

@router.get("/today")
def today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    events = (
        db.query(Event)
        .filter(Event.user_id == current_user.id)
        .filter(Event.start_time >= start)
        .filter(Event.start_time <= now)
        .all()
    )

    totals_seconds: dict[str, int] = {}
    counts: dict[str, int] = {}

    for e in events:
        # conta per type
        key = e.type or "unknown"
        counts[key] = counts.get(key, 0) + 1

        # durata: se end_time è None -> evento "in corso"
        end_time = e.end_time or now
        duration = (end_time - e.start_time).total_seconds()

        # protezione extra (in caso di dati strani)
        if duration < 0:
            continue

        totals_seconds[key] = totals_seconds.get(key, 0) + int(duration)

    return {
        "start_utc": start.isoformat(),
        "end_utc": now.isoformat(),
        "counts": counts,
        "hours_by_type": {k: round(v / 3600, 2) for k, v in totals_seconds.items()},
    }

@router.get("/streak")
def streak(
    type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Event).filter(Event.user_id == current_user.id)
    if type:
        q = q.filter(Event.type == type)

    events = q.all()

    # Giorni (UTC) in cui esiste almeno 1 evento
    days = set()
    for e in events:
        # normalizzo su UTC
        d = e.start_time.astimezone(timezone.utc).date()
        days.add(d)

    if not days:
        return {"type": type, "current_streak": 0, "longest_streak": 0}

    sorted_days = sorted(days)

    # longest streak
    longest = 1
    cur = 1
    for i in range(1, len(sorted_days)):
        if (sorted_days[i] - sorted_days[i - 1]).days == 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1

    # current streak (contando a ritroso da oggi UTC)
    today_utc = datetime.now(timezone.utc).date()
    current = 0
    d = today_utc
    while d in days:
        current += 1
        d = d.fromordinal(d.toordinal() - 1)

    return {"type": type, "current_streak": current, "longest_streak": longest}