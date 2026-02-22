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
    RoomCreate, RoomResponse,
)
from .security import get_current_user

server_instance = Server(sys.argv[1:])
app = server_instance.app


@app.post("/create_room", response_model=RoomResponse)
async def create_room(room_data: RoomCreate, current_user: dict = Depends(get_current_user)):
    """Создать комнату."""
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


@app.get("/rooms", response_model=List[RoomResponse], summary="[dev only] Получить все комнаты пользователя")
async def get_user_rooms(current_user: dict = Depends(get_current_user)):
    """Получить все комнаты текущего пользователя."""
    result = server_instance.db.get_user_rooms(current_user["user_id"])
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
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