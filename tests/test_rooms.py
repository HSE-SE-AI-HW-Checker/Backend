"""Интеграционные тесты эндпоинтов комнат (SQLAlchemy + in-memory SQLite)."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _unique_email(prefix: str = "roomtest") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.com"


def _sign_up(client, username: str, email: str, password: str = "securepass1234") -> dict:
    r = client.post(
        "/sign_up",
        json={"username": username, "email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("error") is False, data
    assert "access_token" in data
    return data


def _headers_from_signup(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
def user_a(client):
    email = _unique_email("user_a")
    return _sign_up(client, "UserA", email), email


@pytest.fixture
def user_b(client):
    email = _unique_email("user_b")
    return _sign_up(client, "UserB", email), email


def test_languages_returns_non_empty(client):
    r = client.get("/languages")
    assert r.status_code == 200
    body = r.json()
    assert "languages" in body
    assert len(body["languages"]) >= 1
    row = body["languages"][0]
    assert "id" in row and "name" in row and "extensions" in row


def test_create_room_requires_auth(client):
    r = client.post(
        "/create_room",
        json={
            "name": "X",
            "description": "d",
            "language": "python",
            "criteria": ["c1"],
            "password": "roompass1234",
        },
    )
    assert r.status_code == 401


def test_create_room_invalid_language(client, user_a):
    data, _ = user_a
    r = client.post(
        "/create_room",
        headers=_headers_from_signup(data),
        json={
            "name": "BadLang",
            "description": "",
            "language": "not_a_real_lang_id",
            "criteria": ["критерий"],
            "password": "roompass1234",
        },
    )
    assert r.status_code == 400
    assert "Недопустимый" in r.json().get("detail", "")


def test_create_room_empty_criteria(client, user_a):
    data, _ = user_a
    r = client.post(
        "/create_room",
        headers=_headers_from_signup(data),
        json={
            "name": "NoCrit",
            "description": "",
            "language": "python",
            "criteria": ["  ", ""],
            "password": "roompass1234",
        },
    )
    assert r.status_code == 400


def test_create_room_list_get_join_flow(client, user_a, user_b):
    a, _ = user_a
    b, _ = user_b
    h_a = _headers_from_signup(a)
    h_b = _headers_from_signup(b)

    create = client.post(
        "/create_room",
        headers=h_a,
        json={
            "name": "Курс 101",
            "description": "Проверка",
            "language": "python",
            "criteria": ["Код читаемый", "Нет утечек памяти"],
            "password": "joinsecret99",
        },
    )
    assert create.status_code == 200, create.text
    room_id = create.json()["room_id"]
    assert len(room_id) == 36

    listed = client.get("/rooms")
    assert listed.status_code == 200
    ids = {x["id"] for x in listed.json()}
    assert room_id in ids

    detail_anon = client.get(f"/rooms/{room_id}")
    assert detail_anon.status_code == 200
    d = detail_anon.json()
    assert d["name"] == "Курс 101"
    assert len(d["criteria"]) == 2
    assert d["criteria"][0]["text"] == "Код читаемый"

    me_before = client.get(f"/rooms/{room_id}/members/me", headers=h_b)
    assert me_before.status_code == 404

    bad_join = client.post(
        f"/rooms/{room_id}/join",
        headers=h_b,
        json={"password": "wrong"},
    )
    assert bad_join.status_code == 403

    ok_join = client.post(
        f"/rooms/{room_id}/join",
        headers=h_b,
        json={"password": "joinsecret99"},
    )
    assert ok_join.status_code == 200, ok_join.text
    assert ok_join.json()["success"] is True
    assert ok_join.json()["room"]["id"] == room_id

    me_after = client.get(f"/rooms/{room_id}/members/me", headers=h_b)
    assert me_after.status_code == 200
    assert me_after.json()["status"] == "active"


def test_creator_has_membership_after_create(client, user_a):
    """Организатор должен состоять в созданной комнате без отдельного join."""
    a, _ = user_a
    h = _headers_from_signup(a)
    create = client.post(
        "/create_room",
        headers=h,
        json={
            "name": "Owner room",
            "description": "",
            "language": "cpp",
            "criteria": ["Один критерий"],
            "password": "roompw1234",
        },
    )
    assert create.status_code == 200
    room_id = create.json()["room_id"]
    me = client.get(f"/rooms/{room_id}/members/me", headers=h)
    assert me.status_code == 200
    assert me.json()["status"] == "active"


def test_rooms_recent_reflects_visits(client, user_a):
    a, _ = user_a
    h = _headers_from_signup(a)

    def make_room(name_suffix: str) -> str:
        r = client.post(
            "/create_room",
            headers=h,
            json={
                "name": f"R{name_suffix}",
                "description": "",
                "language": "java",
                "criteria": ["c"],
                "password": "roompw1234",
            },
        )
        assert r.status_code == 200
        return r.json()["room_id"]

    r1 = make_room("1")
    r2 = make_room("2")

    client.get(f"/rooms/{r1}", headers=h)
    recent = client.get("/rooms/recent", headers=h)
    assert recent.status_code == 200
    rows = recent.json()
    assert len(rows) >= 2
    # Последний просмотр r1 — первый в списке
    assert rows[0]["id"] == r1


def test_member_status_expired_when_deadline_passed(client, user_a):
    a, _ = user_a
    h = _headers_from_signup(a)
    past = datetime.utcnow() - timedelta(days=1)
    r = client.post(
        "/create_room",
        headers=h,
        json={
            "name": "Expired",
            "description": "",
            "language": "csharp",
            "criteria": ["x"],
            "password": "roompw1234",
            "deadline": past.isoformat(),
        },
    )
    assert r.status_code == 200
    room_id = r.json()["room_id"]
    me = client.get(f"/rooms/{room_id}/members/me", headers=h)
    assert me.status_code == 200
    assert me.json()["status"] == "expired"


@patch("src.routers.rooms.can_ai_verify_single_criterion", return_value=True)
def test_criteria_verify_uses_ml_gate_mock(mock_gate, client, user_a):
    data, _ = user_a
    r = client.post(
        "/criteria/verify",
        headers=_headers_from_signup(data),
        json={"criteria_text": "Проверить наличие unit-тестов"},
    )
    assert r.status_code == 200
    assert r.json()["can_ai_verified"] is True
    mock_gate.assert_called_once()


def test_get_room_unknown_404(client, user_a):
    a, _ = user_a
    fake_id = str(uuid.uuid4())
    r = client.get(f"/rooms/{fake_id}", headers=_headers_from_signup(a))
    assert r.status_code == 404
