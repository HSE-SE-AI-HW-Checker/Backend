"""
HTTP-маршруты приложения (комнаты, критерии, языки), привязанные к экземпляру Server.
Регистрируются на том же FastAPI app, что и обработчики Server._setup_handlers.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import TYPE_CHECKING, List

from fastapi import Depends, HTTPException

from src.models.schemas import (
    CriterionRecord,
    CriterionRoomRecord,
    CriterionVerifyRequest,
    CriterionVerifyResponse,
    JoinRoomRequest,
    LanguageCreate,
    OwnerScoreUpdate,
    RecentRoomResponse,
    RoomCreate,
    RoomMemberResponse,
    RoomResponse,
    ScoresUpdate,
)
from src.services.ml_client import ml_verify_criterion
from src.security import get_current_user

if TYPE_CHECKING:
    from src.core.server import Server


def register_application_routes(server: "Server") -> None:
    app = server.app
    db = server.db

    @app.post("/create_room", response_model=RoomResponse)
    async def create_room(room_data: RoomCreate, current_user: dict = Depends(get_current_user)):
        langs_result = db.get_all_languages()
        if langs_result.get("error"):
            raise HTTPException(status_code=500, detail=langs_result["message"])
        if room_data.language not in langs_result["languages"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Язык программирования '{room_data.language}' не найден. "
                    f"Доступные: {langs_result['languages']}"
                ),
            )

        for criterion in room_data.criteria:
            if not criterion.is_ai_verified:
                continue
            existing = db.get_criterion(criterion.criterion_text)
            if existing.get("error"):
                raise HTTPException(status_code=500, detail=existing["message"])
            record = existing["criterion"]
            if record is None or not record["ai_verified"]:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Критерий '{criterion.criterion_text}' не совпадает со статусом "
                        "верификации через AI. Сначала вызовите /criteria/verify"
                    ),
                )

        result = db.create_room(
            creator_id=current_user["user_id"],
            name=room_data.name,
            description=room_data.description,
            language=room_data.language,
            criteria=[c.model_dump() for c in room_data.criteria],
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["message"])

        room_id = result["room_id"]

        for criterion in room_data.criteria:
            cr_result = db.create_criterion_room(
                criterion_text=criterion.criterion_text,
                room_id=room_id,
                can_ai_verified=criterion.is_ai_verified,
            )
            if cr_result.get("error"):
                raise HTTPException(status_code=400, detail=cr_result["message"])

        room = db.get_room(room_id)
        return room["room"]

    @app.delete("/rooms", summary="[dev only] Удалить все комнаты текущего пользователя")
    async def delete_user_rooms(current_user: dict = Depends(get_current_user)):
        result = db.delete_user_rooms(current_user["user_id"])
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        return {"deleted_count": result["deleted_count"]}

    @app.get("/rooms", response_model=List[RoomResponse], summary="Получить все комнаты пользователя")
    async def get_user_rooms(current_user: dict = Depends(get_current_user)):
        result = db.get_all_user_rooms(current_user["user_id"])
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["message"])
        return result["rooms"]

    @app.get(
        "/rooms/recent",
        response_model=List[RecentRoomResponse],
        summary="Недавние комнаты пользователя",
    )
    async def get_recent_rooms(current_user: dict = Depends(get_current_user)):
        result = db.get_user_recent_rooms(current_user["user_id"])
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        return result["rooms"]

    @app.get("/rooms/{room_id}", response_model=RoomResponse)
    async def get_room(room_id: str, current_user: dict = Depends(get_current_user)):
        result = db.get_room(room_id)
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["message"])
        return result["room"]

    @app.get("/criteria", response_model=List[CriterionRecord], summary="[dev only] Получить все критерии")
    async def get_all_criteria(_: dict = Depends(get_current_user)):
        result = db.get_all_criteria()
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        return result["criteria"]

    @app.get(
        "/criteria_room",
        response_model=List[CriterionRoomRecord],
        summary="[dev only] Получить все записи criteria_room",
    )
    async def get_all_criteria_room(_: dict = Depends(get_current_user)):
        result = db.get_all_criteria_room()
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        return result["criteria_room"]

    @app.post("/criteria/verify", response_model=CriterionVerifyResponse)
    async def verify_criterion(
        data: CriterionVerifyRequest,
        _: dict = Depends(get_current_user),
    ):
        existing = db.get_criterion(data.criterion_text)
        if existing.get("error"):
            raise HTTPException(status_code=500, detail=existing["message"])

        if existing["criterion"] is not None:
            return {"can_ai_verified": existing["criterion"]["ai_verified"]}

        ml_url = getattr(server.config, "ml_url", None) or ""
        if ml_url:
            try:
                can_ai_verified = ml_verify_criterion(ml_url, data.criterion_text)
            except Exception:
                can_ai_verified = random.choice([True, False])
        else:
            can_ai_verified = random.choice([True, False])

        result = db.create_criterion(
            criterion_text=data.criterion_text,
            ai_verified=can_ai_verified,
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["message"])

        return {"can_ai_verified": can_ai_verified}

    @app.get("/languages", response_model=List[str])
    async def get_languages():
        result = db.get_all_languages()
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        return result["languages"]

    @app.post("/languages", summary="[dev only] Добавить язык программирования")
    async def add_language(data: LanguageCreate, _: dict = Depends(get_current_user)):
        result = db.add_language(data.language)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["message"])
        return {"language": data.language}

    @app.delete("/languages/{language}", summary="[dev only] Удалить язык программирования")
    async def delete_language(language: str, _: dict = Depends(get_current_user)):
        result = db.delete_language(language)
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["message"])
        return {"language": language}

    @app.post("/rooms/{room_id}/join", response_model=RoomMemberResponse)
    async def join_room(
        room_id: str,
        data: JoinRoomRequest,
        current_user: dict = Depends(get_current_user),
    ):
        room = db.get_room(room_id)
        if room.get("error") or room["room"] is None:
            raise HTTPException(status_code=404, detail=f"Комната '{room_id}' не найдена")
        if room["room"]["password"] != data.password:
            raise HTTPException(status_code=403, detail="Неверный пароль комнаты")

        result = db.join_room(current_user["user_id"], room_id)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["message"])

        member = db.get_room_member(current_user["user_id"], room_id)
        if member.get("error"):
            raise HTTPException(status_code=500, detail=member["message"])
        return member["member"]

    @app.get("/rooms/{room_id}/members", response_model=List[RoomMemberResponse])
    async def get_room_members(room_id: str, _: dict = Depends(get_current_user)):
        result = db.get_room_members_with_users(room_id)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        return result["members"]

    @app.get("/rooms/{room_id}/members/me", response_model=RoomMemberResponse)
    async def get_my_room_member(room_id: str, current_user: dict = Depends(get_current_user)):
        result = db.get_room_member(current_user["user_id"], room_id)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["message"])
        if result["member"] is None:
            raise HTTPException(status_code=404, detail="Вы не являетесь участником этой комнаты")
        db.update_member_scores(
            current_user["user_id"], room_id,
            last_visit=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        return result["member"]

    @app.patch("/rooms/{room_id}/members/{user_id}/score", response_model=RoomMemberResponse)
    async def update_member_score(
        room_id: str,
        user_id: int,
        data: OwnerScoreUpdate,
        current_user: dict = Depends(get_current_user),
    ):
        room = db.get_room(room_id)
        if room.get("error") or room["room"] is None:
            raise HTTPException(status_code=404, detail=f"Комната '{room_id}' не найдена")
        if room["room"]["creator_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Только владелец комнаты может выставлять оценки")

        result = db.update_owner_score(user_id, room_id, data.owner_score, data.owner_comment)
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["message"])

        member = db.get_room_member(user_id, room_id)
        if member.get("error"):
            raise HTTPException(status_code=500, detail=member["message"])
        return member["member"]

    @app.patch(
        "/rooms/{room_id}/members/{user_id}/scores",
        response_model=RoomMemberResponse,
        summary="[dev only] Выставить оценки участнику",
    )
    async def update_member_scores(
        room_id: str,
        user_id: int,
        data: ScoresUpdate,
        _: dict = Depends(get_current_user),
    ):
        result = db.update_member_scores(
            user_id,
            room_id,
            ai_score=data.ai_score,
            final_score=data.final_score,
            owner_score=data.owner_score,
            deadline=data.deadline,
            submissions_count=data.submissions_count,
        )
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["message"])

        member = db.get_room_member(user_id, room_id)
        if member.get("error"):
            raise HTTPException(status_code=500, detail=member["message"])
        return member["member"]
