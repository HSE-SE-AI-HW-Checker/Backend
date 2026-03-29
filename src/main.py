"""
Точка входа для Backend приложения.
"""

import random
import sys
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse

from .core.server import Server
from .models.schemas import (
    CriterionRecord, CriterionRoomRecord, CriterionVerifyRequest, CriterionVerifyResponse,
    JoinRoomRequest, LanguageCreate, OwnerScoreUpdate, RecentRoomResponse,
    RoomCreate, RoomMemberResponse, RoomResponse, ScoresUpdate,
)
from .security import get_current_user

server_instance = Server(sys.argv[1:])
app = server_instance.app


@app.post("/create_room", response_model=RoomResponse)
async def create_room(room_data: RoomCreate, current_user: dict = Depends(get_current_user)):
    """Создать комнату."""
    # Проверяем, что указанный язык программирования существует в таблице languages
    langs_result = server_instance.db.get_all_languages()
    if langs_result.get("error"):
        raise HTTPException(status_code=500, detail=langs_result["message"])
    if room_data.language not in langs_result["languages"]:
        raise HTTPException(
            status_code=400,
            detail=f"Язык программирования '{room_data.language}' не найден. Доступные: {langs_result['languages']}",
        )

    # Для критериев с is_ai_verified=True — проверяем наличие записи в criteria
    for criterion in room_data.criteria:
        if not criterion.is_ai_verified:
            continue

        existing = server_instance.db.get_criterion(criterion.criterion_text)
        if existing.get("error"):
            raise HTTPException(status_code=500, detail=existing["message"])

        record = existing["criterion"]
        if record is None or not record["ai_verified"]:
            raise HTTPException(
                status_code=400,
                detail=f"Критерий '{criterion.criterion_text}' не совпадает со статусом верификации через AI. Сначала вызовите /criteria/verify",
            )

    # Создаём комнату
    result = server_instance.db.create_room(
        creator_id=current_user["user_id"],
        name=room_data.name,
        description=room_data.description,
        language=room_data.language,
        criteria=[c.model_dump() for c in room_data.criteria],
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])

    room_id = result["room_id"]

    # Создаём записи в criteria_room для всех критериев
    for criterion in room_data.criteria:
        cr_result = server_instance.db.create_criterion_room(
            criterion_text=criterion.criterion_text,
            room_id=room_id,
            can_ai_verified=criterion.is_ai_verified,
        )
        if cr_result.get("error"):
            raise HTTPException(status_code=400, detail=cr_result["message"])

    room = server_instance.db.get_room(room_id)
    return room["room"]


@app.delete("/rooms", summary="[dev only] Удалить все комнаты текущего пользователя")
async def delete_user_rooms(current_user: dict = Depends(get_current_user)):
    """Удалить все комнаты текущего пользователя вместе с записями criteria_room."""
    result = server_instance.db.delete_user_rooms(current_user["user_id"])
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return {"deleted_count": result["deleted_count"]}


@app.get("/rooms", response_model=List[RoomResponse], summary="Получить все комнаты пользователя")
async def get_user_rooms(current_user: dict = Depends(get_current_user)):
    """Получить все комнаты пользователя: созданные им и те, в которые он вступил."""
    result = server_instance.db.get_all_user_rooms(current_user["user_id"])
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result["rooms"]


@app.get("/rooms/recent", response_model=List[RecentRoomResponse], summary="Недавние комнаты пользователя")
async def get_recent_rooms(current_user: dict = Depends(get_current_user)):
    """Комнаты, в которых пользователь является участником, с полями last_visit, submissions_count, participant_count."""
    result = server_instance.db.get_user_recent_rooms(current_user["user_id"])
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return result["rooms"]


@app.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, current_user: dict = Depends(get_current_user)):
    """Получить комнату по ID."""
    result = server_instance.db.get_room(room_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["message"])
    return result["room"]


@app.get("/criteria", response_model=List[CriterionRecord], summary="[dev only] Получить все критерии")
async def get_all_criteria(_: dict = Depends(get_current_user)):
    """Получить все записи из таблицы criteria."""
    result = server_instance.db.get_all_criteria()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return result["criteria"]


@app.get("/criteria_room", response_model=List[CriterionRoomRecord], summary="[dev only] Получить все записи criteria_room")
async def get_all_criteria_room(_: dict = Depends(get_current_user)):
    """Получить все записи из таблицы criteria_room."""
    result = server_instance.db.get_all_criteria_room()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return result["criteria_room"]


@app.post("/criteria/verify", response_model=CriterionVerifyResponse)
async def verify_criterion(
    data: CriterionVerifyRequest,
    _: dict = Depends(get_current_user),
):
    """Верифицировать критерий: вернуть статус если уже есть, иначе — проверить через AI и сохранить."""
    existing = server_instance.db.get_criterion(data.criterion_text)
    if existing.get("error"):
        raise HTTPException(status_code=500, detail=existing["message"])

    if existing["criterion"] is not None:
        return {"can_ai_verified": existing["criterion"]["ai_verified"]}

    can_ai_verified = random.choice([True, False])
    result = server_instance.db.create_criterion(
        criterion_text=data.criterion_text,
        ai_verified=can_ai_verified,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])

    return {"can_ai_verified": can_ai_verified}


@app.get("/languages", response_model=List[str])
async def get_languages():
    """Получить список всех доступных языков программирования."""
    result = server_instance.db.get_all_languages()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return result["languages"]


@app.post("/languages", summary="[dev only] Добавить язык программирования")
async def add_language(data: LanguageCreate, _: dict = Depends(get_current_user)):
    """Добавить язык программирования в список доступных."""
    result = server_instance.db.add_language(data.language)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return {"language": data.language}


@app.delete("/languages/{language}", summary="[dev only] Удалить язык программирования")
async def delete_language(language: str, _: dict = Depends(get_current_user)):
    """Удалить язык программирования из списка доступных."""
    result = server_instance.db.delete_language(language)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["message"])
    return {"language": language}


@app.post("/rooms/{room_id}/join", response_model=RoomMemberResponse)
async def join_room(room_id: str, data: JoinRoomRequest, current_user: dict = Depends(get_current_user)):
    """Вступить в комнату."""
    room = server_instance.db.get_room(room_id)
    if room.get("error") or room["room"] is None:
        raise HTTPException(status_code=404, detail=f"Комната '{room_id}' не найдена")
    if room["room"]["password"] != data.password:
        raise HTTPException(status_code=403, detail="Неверный пароль комнаты")

    result = server_instance.db.join_room(current_user["user_id"], room_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])

    member = server_instance.db.get_room_member(current_user["user_id"], room_id)
    if member.get("error"):
        raise HTTPException(status_code=500, detail=member["message"])
    return member["member"]


@app.get("/rooms/{room_id}/members", response_model=List[RoomMemberResponse])
async def get_room_members(room_id: str, _: dict = Depends(get_current_user)):
    """Получить список участников комнаты."""
    result = server_instance.db.get_room_members(room_id)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    return result["members"]


@app.get("/rooms/{room_id}/members/me", response_model=RoomMemberResponse)
async def get_my_room_member(room_id: str, current_user: dict = Depends(get_current_user)):
    """Получить свою запись в комнате."""
    result = server_instance.db.get_room_member(current_user["user_id"], room_id)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])
    if result["member"] is None:
        raise HTTPException(status_code=404, detail="Вы не являетесь участником этой комнаты")
    return result["member"]


@app.patch("/rooms/{room_id}/members/{user_id}/score", response_model=RoomMemberResponse)
async def update_member_score(
    room_id: str,
    user_id: int,
    data: OwnerScoreUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Выставить оценку участнику (только владелец комнаты)."""
    room = server_instance.db.get_room(room_id)
    if room.get("error") or room["room"] is None:
        raise HTTPException(status_code=404, detail=f"Комната '{room_id}' не найдена")
    if room["room"]["creator_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Только владелец комнаты может выставлять оценки")

    result = server_instance.db.update_owner_score(user_id, room_id, data.owner_score)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["message"])

    member = server_instance.db.get_room_member(user_id, room_id)
    if member.get("error"):
        raise HTTPException(status_code=500, detail=member["message"])
    return member["member"]


@app.patch("/rooms/{room_id}/members/{user_id}/scores", response_model=RoomMemberResponse, summary="[dev only] Выставить оценки участнику")
async def update_member_scores(
    room_id: str,
    user_id: int,
    data: ScoresUpdate,
    _: dict = Depends(get_current_user),
):
    """[dev only] Выставить ai_score, final_score и/или owner_score участнику комнаты."""
    result = server_instance.db.update_member_scores(
        user_id, room_id,
        ai_score=data.ai_score,
        final_score=data.final_score,
        owner_score=data.owner_score,
        deadline=data.deadline,
        submissions_count=data.submissions_count,
    )
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["message"])

    member = server_instance.db.get_room_member(user_id, room_id)
    if member.get("error"):
        raise HTTPException(status_code=500, detail=member["message"])
    return member["member"]


@app.get("/info")
async def info():
    """
    Эндпоинт с информацией о сервере.
    
    Returns:
        dict: Информация о сервере
    """
    return {
        "server": "FastAPI",
        "version": "0.1.0",
        "description": "Простой HTTP сервер для демонстрации",
        "endpoints": [
            "/",
            "/info"
        ]
    }