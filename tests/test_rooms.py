"""Интеграционные тесты комнат (API из main / app_routes, SQLAlchemy in-memory)."""

from __future__ import annotations

import os
import sys
import uuid
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _email(prefix: str = "rt") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _sign_up(client, username: str, email: str, password: str = "securepass1234") -> dict:
    r = client.post("/sign_up", json={"username": username, "email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("error") is False, data
    assert "access_token" in data
    return data


def _hdr(tok: dict) -> dict:
    return {"Authorization": f"Bearer {tok['access_token']}"}


@pytest.fixture
def user_a(client):
    return _sign_up(client, "UserA", _email("a"))


@pytest.fixture
def user_b(client):
    return _sign_up(client, "UserB", _email("b"))


def _seed_language(client, token_data: dict, lang: str = "python") -> None:
    r = client.post("/languages", headers=_hdr(token_data), json={"language": lang})
    assert r.status_code == 200, r.text


def test_languages_list_empty_then_add(client, user_a):
    r = client.get("/languages")
    assert r.status_code == 200
    assert r.json() == []

    _seed_language(client, user_a)
    r2 = client.get("/languages")
    assert r2.status_code == 200
    assert "python" in r2.json()


def test_create_room_requires_language_and_auth(client, user_a):
    r = client.post(
        "/create_room",
        headers=_hdr(user_a),
        json={
            "name": "R1",
            "description": "Описание",
            "language": "python",
            "criteria": [{"criterion_text": "К1", "is_ai_verified": False}],
        },
    )
    assert r.status_code == 400
    assert "не найден" in r.json()["detail"]

    _seed_language(client, user_a)
    r2 = client.post(
        "/create_room",
        headers=_hdr(user_a),
        json={
            "name": "R1",
            "description": "Описание",
            "language": "python",
            "criteria": [{"criterion_text": "К1", "is_ai_verified": False}],
        },
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert "id" in body and "password" in body
    assert len(body["criteria"]) == 1


def test_join_and_members_me(client, user_a, user_b):
    _seed_language(client, user_a)
    create = client.post(
        "/create_room",
        headers=_hdr(user_a),
        json={
            "name": "Курс",
            "description": "Описание курса",
            "language": "python",
            "criteria": [
                {"criterion_text": "Стиль", "is_ai_verified": False},
            ],
        },
    )
    assert create.status_code == 200
    room = create.json()
    room_id = room["id"]
    pwd = room["password"]

    me_b = client.get(f"/rooms/{room_id}/members/me", headers=_hdr(user_b))
    assert me_b.status_code == 404

    bad = client.post(
        f"/rooms/{room_id}/join",
        headers=_hdr(user_b),
        json={"password": "WRONGXXX"},
    )
    assert bad.status_code == 403

    ok = client.post(
        f"/rooms/{room_id}/join",
        headers=_hdr(user_b),
        json={"password": pwd},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["room_id"] == room_id

    me_ok = client.get(f"/rooms/{room_id}/members/me", headers=_hdr(user_b))
    assert me_ok.status_code == 200


def test_get_user_rooms_includes_created(client, user_a):
    _seed_language(client, user_a)
    client.post(
        "/create_room",
        headers=_hdr(user_a),
        json={
            "name": "OnlyMine",
            "description": "D",
            "language": "python",
            "criteria": [{"criterion_text": "c", "is_ai_verified": False}],
        },
    )
    r = client.get("/rooms", headers=_hdr(user_a))
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert any(x["name"] == "OnlyMine" for x in r.json())


@patch("src.app_routes.random.choice", return_value=True)
def test_criteria_verify_persists(mock_choice, client, user_a):
    _ = mock_choice
    r = client.post(
        "/criteria/verify",
        headers=_hdr(user_a),
        json={"criterion_text": "Уникальный критерий для теста"},
    )
    assert r.status_code == 200
    assert r.json()["can_ai_verified"] is True


def test_create_room_rejects_unverified_ai_criterion(client, user_a):
    _seed_language(client, user_a)
    r = client.post(
        "/create_room",
        headers=_hdr(user_a),
        json={
            "name": "Bad",
            "description": "D",
            "language": "python",
            "criteria": [{"criterion_text": "Нет в БД", "is_ai_verified": True}],
        },
    )
    assert r.status_code == 400
