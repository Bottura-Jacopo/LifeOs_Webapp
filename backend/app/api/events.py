from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.api.deps import get_db
from app.core.auth import get_current_user
from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventCreate, EventOut, EventUpdate, EventStart, EventStop

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = Event(
        user_id=current_user.id,
        type=event_in.type,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        score=event_in.score,
        notes=event_in.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("", response_model=list[EventOut])
def list_events(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Event).filter(Event.user_id == current_user.id)

    if type is not None:
        q = q.filter(Event.type == type)
    if from_ is not None:
        q = q.filter(Event.start_time >= from_)
    if to is not None:
        q = q.filter(Event.end_time <= to)

    events = (
        q.order_by(Event.start_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return events

@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: str,
    event_in: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not Found")
    
    data = event_in.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(event, key, value)

    # Validazione base: end_time non può essere prima di start_time
    if(event.end_time is not None and event.start_time is not None):
        if(event.end_time < event.start_time):
            raise HTTPException(status_code=400, detail="end_time must be >= start_time")
    
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}", response_model=EventOut)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    return None

@router.post("/start", response_model=EventOut)
def start_event(
    event_in: EventStart,
    db: Session = Depends(get_db),
    get_current_user: User = Depends(get_current_user),
):
    active = (
        db.query(Event)
        .filter(Event.user_id == current_user.id, Event.end_time.is_(None))
        .first()
    )
    if(active):
        raise HTTPException(status_code=400, detail="You already have an active event")

    now = datetime.now(timezone.utc)
    event = Event(
        user_id = current_user.id,
        type=event_in.type,
        start_time=now,
        end_time=None,
        notes=event_in.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.post("/{event_id}/stop", response_model=EventOut)
def stop_event(
    event_id: UUID,
    event_in: EventStop,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.end_time is not None:
        raise HTTPException(status_code=400, detail="Event is already stopped")

    now = datetime.now(timezone.utc)
    event.end_time = now

    # opzionale: aggiorna score/notes allo stop
    data = event_in.model_dump(exclude_unset=True)
    if "score" in data:
        event.score = data["score"]
    if "notes" in data and data["notes"] is not None:
        # append semplice: mantieni note già presenti
        if event.notes:
            event.notes = event.notes + "\n" + data["notes"]
        else:
            event.notes = data["notes"]

    # validazione base: end_time >= start_time (sempre vero, ma safe)
    if event.end_time < event.start_time:
        raise HTTPException(status_code=400, detail="Invalid end_time")

    db.commit()
    db.refresh(event)
    return event