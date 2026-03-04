"""
Эндпоинты комнат и верификации критериев (пояснительная записка).
"""

from __future__ import annotations

from typing import Annotated, Generator, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.core.config_manager import get_ml_server_address
from src.models.schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    CriteriaVerifyRequest,
    CriteriaVerifyResponse,
    JoinRoomBody,
    JoinRoomResponse,
    LanguageRow,
    MemberMeResponse,
    RecentRoomRow,
    RoomDetailOut,
    RoomListItem,
    LanguagesOutResponse,
)
from src.security.dependencies import get_current_user, get_optional_current_user
from src.security.encryptors import hash_password, verify_password
from src.services.criterion_ai_gate import can_ai_verify_single_criterion
from src.services.languages_catalog import LanguagesCatalog
from src.services.room_queries import (
    computed_member_status,
    create_room,
    ensure_membership,
    get_room,
    list_all_rooms,
    list_recent_visits,
    membership_for,
    room_to_detail_dict,
    upsert_visit,
)
from src.utils.helpers import get_languages_catalog

router = APIRouter(tags=["rooms"])


def _require_sqlalchemy(request: Request):
    srv = request.app.state.server
    if srv.db.__class__.__name__ != "SQLAlchemyDB":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Раздел комнат требует database_implementation: SQLAlchemyDB",
        )
    return srv


def _cat_for_request(request: Request) -> LanguagesCatalog:
    srv = request.app.state.server
    return get_languages_catalog(srv.config.available_languages_path)


def get_db_session(request: Request) -> Generator[Session, None, None]:
    srv = request.app.state.server
    db = srv.db
    if db.__class__.__name__ != "SQLAlchemyDB":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="База комнат доступна только с SQLAlchemyDB",
        )
    sess = db.get_session()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()


DbSession = Annotated[Session, Depends(get_db_session)]


@router.get("/languages", response_model=LanguagesOutResponse)
async def languages_list(request: Request) -> LanguagesOutResponse:
    _require_sqlalchemy(request)
    cat = _cat_for_request(request)
    payload = cat.api_languages_payload()
    return LanguagesOutResponse(
        languages=[LanguageRow(**row) for row in payload],
    )


@router.post("/create_room", response_model=CreateRoomResponse)
async def create_room_route(
    request: Request,
    body: CreateRoomRequest,
    session: DbSession,
    user: dict = Depends(get_current_user),
):
    _require_sqlalchemy(request)
    cat = _cat_for_request(request)
    lid = body.language.strip().lower()
    if not cat.language_exists(lid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый language: {body.language}",
        )

    pwd_hash = hash_password(body.password)

    raw_criteria = [str(t).strip() for t in body.criteria if str(t).strip()]
    if not raw_criteria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Список criteria не может быть пустым",
        )
    texts = raw_criteria
    room = create_room(
        session,
        creator_user_id=user["user_id"],
        name=body.name,
        description=body.description or "",
        language=lid,
        password_hash=pwd_hash,
        criteria_texts=texts,
        deadline=body.deadline,
    )
    ensure_membership(
        session,
        room_id=room.id,
        user_id=user["user_id"],
        room_deadline_snapshot=room.deadline,
    )
    upsert_visit(session, user_id=user["user_id"], room_id=room.id)
    return CreateRoomResponse(
        room_id=room.id,
        name=room.name,
        created_at=room.created_at,
    )


@router.get("/rooms", response_model=List[RoomListItem])
async def rooms_all(request: Request, session: DbSession):
    _require_sqlalchemy(request)
    rooms = list_all_rooms(session)
    return [
        RoomListItem(id=r.id, name=r.name, description=r.description or "", created_at=r.created_at)
        for r in rooms
    ]


@router.get("/rooms/recent", response_model=List[RecentRoomRow])
async def rooms_recent(
    request: Request,
    session: DbSession,
    user: dict = Depends(get_current_user),
):
    _require_sqlalchemy(request)
    pairs = list_recent_visits(session, user["user_id"])
    rows: List[RecentRoomRow] = []
    for room, visited in pairs:
        rows.append(RecentRoomRow(id=room.id, name=room.name, last_visited=visited))
    return rows


@router.get("/rooms/{room_id}", response_model=RoomDetailOut)
async def rooms_get_detail(
    request: Request,
    room_id: str,
    session: DbSession,
    user_opt: dict | None = Depends(get_optional_current_user),
):
    _require_sqlalchemy(request)
    room = get_room(session, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")
    # Инициализатор посещений для списка recent (для авторизованных клиентов)
    if user_opt:
        upsert_visit(session, user_id=user_opt["user_id"], room_id=room_id)
    data = room_to_detail_dict(room)
    return RoomDetailOut.model_validate(data)


@router.get("/rooms/{room_id}/members/me", response_model=MemberMeResponse)
async def room_member_me(
    request: Request,
    room_id: str,
    session: DbSession,
    user: dict = Depends(get_current_user),
):
    _require_sqlalchemy(request)
    room = get_room(session, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")
    m = membership_for(session, room_id=room_id, user_id=user["user_id"])
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вы не состоите в этой комнате")

    dl = m.deadline_at or room.deadline

    stat = computed_member_status(m, room)

    return MemberMeResponse(
        user_id=str(user["user_id"]),
        joined_at=m.joined_at,
        deadline=dl,
        status=stat,
    )


@router.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def room_join(
    request: Request,
    room_id: str,
    body: JoinRoomBody,
    session: DbSession,
    user: dict = Depends(get_current_user),
):
    _require_sqlalchemy(request)
    room = get_room(session, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")

    existing = membership_for(session, room_id=room_id, user_id=user["user_id"])
    if not existing:
        if not verify_password(body.password, room.password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверный пароль",
            )

    ensure_membership(
        session,
        room_id=room_id,
        user_id=user["user_id"],
        room_deadline_snapshot=room.deadline,
    )
    upsert_visit(session, user_id=user["user_id"], room_id=room_id)
    refreshed = room_to_detail_dict(get_room(session, room_id))
    return JoinRoomResponse(
        success=True,
        message="Подключение успешно",
        room=RoomDetailOut.model_validate(refreshed),
    )


@router.post("/criteria/verify", response_model=CriteriaVerifyResponse)
async def criteria_verify_route(
    request: Request,
    body: CriteriaVerifyRequest,
    _user: dict = Depends(get_current_user),
):
    _ = request
    ml_url = get_ml_server_address()
    try:
        ok = can_ai_verify_single_criterion(ml_url, body.criteria_text.strip())
        return CriteriaVerifyResponse(can_ai_verified=ok)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML-сервис недоступен или вернул ошибку: {exc}",
        ) from exc
