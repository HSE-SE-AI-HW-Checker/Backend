"""Операции с комнатами (только для SQLAlchemyDB)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from ..models.orm import Room, RoomCriterion, RoomMembership, RoomVisit


def _utcnow_naive():
    return datetime.utcnow()


def generate_room_uuid() -> str:
    return str(uuid4())


def create_room(
    session,
    *,
    creator_user_id: int,
    name: str,
    description: str,
    language: str,
    password_hash: str,
    criteria_texts: List[str],
    deadline: datetime | None,
) -> Room:
    room_id = generate_room_uuid()
    room = Room(
        id=room_id,
        name=name.strip(),
        description=description.strip() or "",
        language=language.strip().lower(),
        password_hash=password_hash,
        creator_id=creator_user_id,
        deadline=deadline,
    )
    session.add(room)
    for pos, txt in enumerate(criteria_texts):
        session.add(
            RoomCriterion(
                room_id=room_id,
                text=txt.strip(),
                ctype=0,
                position=pos,
            )
        )
    session.flush()
    return room


def list_all_rooms(session) -> List[Room]:
    return session.query(Room).order_by(Room.created_at.desc()).all()


def get_room(session, room_id: str) -> Optional[Room]:
    return session.query(Room).filter(Room.id == room_id).first()


def membership_for(session, *, room_id: str, user_id: int) -> Optional[RoomMembership]:
    return (
        session.query(RoomMembership)
        .filter(RoomMembership.room_id == room_id, RoomMembership.user_id == user_id)
        .first()
    )


def upsert_visit(session, *, user_id: int, room_id: str) -> None:
    visit = (
        session.query(RoomVisit)
        .filter(RoomVisit.user_id == user_id, RoomVisit.room_id == room_id)
        .first()
    )
    if visit:
        visit.last_visited = _utcnow_naive()
    else:
        session.add(RoomVisit(user_id=user_id, room_id=room_id, last_visited=_utcnow_naive()))
    session.flush()


def list_recent_visits(session, user_id: int) -> List[Tuple[Room, datetime]]:
    q = (
        session.query(Room, RoomVisit.last_visited)
        .join(RoomVisit, RoomVisit.room_id == Room.id)
        .filter(RoomVisit.user_id == user_id)
        .order_by(RoomVisit.last_visited.desc())
    )
    return list(q.all())


def ensure_membership(
    session,
    *,
    room_id: str,
    user_id: int,
    room_deadline_snapshot: datetime | None,
) -> RoomMembership:
    existing = membership_for(session, room_id=room_id, user_id=user_id)
    if existing:
        return existing
    m = RoomMembership(
        room_id=room_id,
        user_id=user_id,
        deadline_at=room_deadline_snapshot,
        status="active",
    )
    session.add(m)
    session.flush()
    return m


def computed_member_status(m: RoomMembership, room: Room) -> str:
    if m.status == "completed":
        return "completed"
    deadline = m.deadline_at or room.deadline
    if deadline is not None:
        expiry = deadline
        if isinstance(expiry, datetime) and expiry.tzinfo is not None:
            expiry = expiry.replace(tzinfo=None)
        if _utcnow_naive() > expiry:
            return "expired"
    return "active"


def room_to_detail_dict(room: Room) -> dict:
    criteria = [{"text": c.text, "type": int(c.ctype)} for c in room.criteria]
    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "language": room.language,
        "criteria": criteria,
        "created_at": room.created_at,
        "deadline": room.deadline,
    }
