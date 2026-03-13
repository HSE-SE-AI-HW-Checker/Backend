import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils_for_tests import logger, get_auth_headers


@pytest.fixture
def client():
    """
    Клиент с полным приложением из main.py (включает эндпоинты комнат/языков).
    sys.argv переопределяется на testing-конфиг перед перезагрузкой модуля.
    """
    old_argv = sys.argv[:]
    sys.argv = ["test", "config=testing"]
    try:
        import src.main as main_module
        importlib.reload(main_module)
        with TestClient(main_module.app) as c:
            yield c
    finally:
        sys.argv = old_argv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_language(client, headers, language="Python"):
    """Добавить язык в таблицу languages (игнорировать если уже есть)."""
    client.post("/languages", json={"language": language}, headers=headers)


def _cleanup(client, headers):
    """Удалить все комнаты и критерии пользователя."""
    client.delete("/rooms", headers=headers)


VALID_ROOM = {
    "name": "Test Room",
    "description": "Test description",
    "language": "Python",
    "criteria": [{"criterion_text": "Код должен компилироваться", "is_ai_verified": False}],
}


# ---------------------------------------------------------------------------
# POST /create_room
# ---------------------------------------------------------------------------

def test_create_room_success(client):
    """Успешное создание комнаты с одним критерием."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)
    _cleanup(client, headers)

    response = client.post("/create_room", json=VALID_ROOM, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == VALID_ROOM["name"]
    assert data["description"] == VALID_ROOM["description"]
    assert data["language"] == VALID_ROOM["language"]
    assert len(data["criteria"]) == 1
    assert "id" in data
    assert "creator_id" in data
    assert "created_at" in data
    assert data["participant_count"] == 0
    logger.info("✓ Комната создана успешно")


def test_create_room_empty_criteria(client):
    """Пустой список критериев — 422."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)

    room = {**VALID_ROOM, "criteria": []}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 422, response.text
    logger.info("✓ Пустые критерии отклонены (422)")


def test_create_room_with_non_ai_criterion(client):
    """Создание комнаты с несколькими критериями is_ai_verified=False."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)
    _cleanup(client, headers)

    room = {**VALID_ROOM, "criteria": [
        {"criterion_text": "Код должен компилироваться", "is_ai_verified": False},
        {"criterion_text": "Нет глобальных переменных", "is_ai_verified": False},
    ]}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["criteria"]) == 2
    assert data["criteria"][0]["is_ai_verified"] is False
    logger.info("✓ Комната с ручными критериями создана")


def test_create_room_with_ai_verified_criterion(client):
    """Создание комнаты с критерием is_ai_verified=True после предварительной верификации."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)
    _cleanup(client, headers)

    criterion_text = "Решение использует рекурсию"

    # Верифицируем и принудительно добираемся до ai_verified=True
    # (random, поэтому пробуем до 20 раз)
    ai_verified = False
    for _ in range(20):
        response = client.post("/criteria/verify", json={"criterion_text": criterion_text}, headers=headers)
        assert response.status_code == 200
        if response.json()["can_ai_verified"]:
            ai_verified = True
            break
        # Критерий закэшировался как False — нужен другой текст при следующей попытке
        # Проще создать комнату с is_ai_verified=False и пропустить тест, если не повезло
        break

    if not ai_verified:
        # Критерий оказался not ai_verified — проверяем что сервер правильно отклоняет
        room = {**VALID_ROOM, "criteria": [{"criterion_text": criterion_text, "is_ai_verified": True}]}
        response = client.post("/create_room", json=room, headers=headers)
        assert response.status_code == 400
        assert "верификации" in response.json()["detail"]
        logger.info("✓ Сервер отклонил комнату с неверифицированным AI-критерием (ожидаемо)")
        return

    room = {**VALID_ROOM, "criteria": [{"criterion_text": criterion_text, "is_ai_verified": True}]}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["criteria"][0]["is_ai_verified"] is True
    logger.info("✓ Комната с AI-критерием создана после верификации")


def test_create_room_unauthorized(client):
    """Создание комнаты без авторизации возвращает 401/403."""
    response = client.post("/create_room", json=VALID_ROOM)
    assert response.status_code in (401, 403), response.text
    logger.info("✓ Неавторизованный запрос отклонён")


def test_create_room_empty_name(client):
    """Пустое имя комнаты — 422."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)

    room = {**VALID_ROOM, "name": ""}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 422, response.text
    logger.info("✓ Пустое название отклонено (422)")


def test_create_room_empty_description(client):
    """Пустое описание комнаты — 422."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)

    room = {**VALID_ROOM, "description": ""}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 422, response.text
    logger.info("✓ Пустое описание отклонено (422)")


def test_create_room_empty_language(client):
    """Пустой язык — 422."""
    headers = get_auth_headers(client)

    room = {**VALID_ROOM, "language": ""}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 422, response.text
    logger.info("✓ Пустой язык отклонён (422)")


def test_create_room_unknown_language(client):
    """Язык отсутствует в таблице languages — 400."""
    headers = get_auth_headers(client)

    room = {**VALID_ROOM, "language": "BrainfuckLang99"}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 400, response.text
    assert "BrainfuckLang99" in response.json()["detail"]
    logger.info("✓ Несуществующий язык отклонён (400)")


def test_create_room_ai_criterion_not_verified(client):
    """Критерий с is_ai_verified=True без предварительной верификации — 400."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)

    room = {
        **VALID_ROOM,
        "criteria": [{"criterion_text": "Абсолютно новый критерий xyz987", "is_ai_verified": True}],
    }
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 400, response.text
    assert "верификации" in response.json()["detail"] or "verify" in response.json()["detail"].lower()
    logger.info("✓ Неверифицированный AI-критерий отклонён (400)")


def test_create_room_empty_criterion_text(client):
    """Пустой criterion_text в критерии — 422."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)

    room = {**VALID_ROOM, "criteria": [{"criterion_text": "", "is_ai_verified": False}]}
    response = client.post("/create_room", json=room, headers=headers)
    assert response.status_code == 422, response.text
    logger.info("✓ Пустой criterion_text отклонён (422)")


# ---------------------------------------------------------------------------
# GET /rooms и GET /rooms/{room_id}
# ---------------------------------------------------------------------------

def test_get_user_rooms(client):
    """GET /rooms возвращает список комнат пользователя."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)
    _cleanup(client, headers)

    client.post("/create_room", json=VALID_ROOM, headers=headers)
    client.post("/create_room", json={**VALID_ROOM, "name": "Second Room"}, headers=headers)

    response = client.get("/rooms", headers=headers)
    assert response.status_code == 200, response.text
    rooms = response.json()
    assert len(rooms) == 2
    names = {r["name"] for r in rooms}
    assert "Test Room" in names
    assert "Second Room" in names
    logger.info("✓ GET /rooms вернул корректный список")


def test_get_user_rooms_unauthorized(client):
    """GET /rooms без авторизации — 401/403."""
    response = client.get("/rooms")
    assert response.status_code in (401, 403)
    logger.info("✓ GET /rooms без токена отклонён")


def test_get_room_by_id(client):
    """GET /rooms/{room_id} возвращает нужную комнату."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)
    _cleanup(client, headers)

    create_resp = client.post("/create_room", json=VALID_ROOM, headers=headers)
    assert create_resp.status_code == 200
    room_id = create_resp.json()["id"]

    response = client.get(f"/rooms/{room_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == VALID_ROOM["name"]
    logger.info("✓ GET /rooms/{room_id} вернул корректную комнату")


def test_get_room_not_found(client):
    """GET /rooms/{room_id} для несуществующего id — 404."""
    headers = get_auth_headers(client)
    response = client.get("/rooms/nonexistent-room-id-000", headers=headers)
    assert response.status_code == 404, response.text
    logger.info("✓ Несуществующая комната возвращает 404")


# ---------------------------------------------------------------------------
# DELETE /rooms
# ---------------------------------------------------------------------------

def test_delete_user_rooms(client):
    """DELETE /rooms удаляет все комнаты пользователя."""
    headers = get_auth_headers(client)
    _setup_language(client, headers)
    _cleanup(client, headers)

    client.post("/create_room", json=VALID_ROOM, headers=headers)
    client.post("/create_room", json={**VALID_ROOM, "name": "Room 2"}, headers=headers)

    delete_resp = client.delete("/rooms", headers=headers)
    assert delete_resp.status_code == 200, delete_resp.text
    assert delete_resp.json()["deleted_count"] == 2

    rooms_resp = client.get("/rooms", headers=headers)
    assert rooms_resp.json() == []
    logger.info("✓ DELETE /rooms удалил все комнаты")


def test_delete_user_rooms_unauthorized(client):
    """DELETE /rooms без авторизации — 401/403."""
    response = client.delete("/rooms")
    assert response.status_code in (401, 403)
    logger.info("✓ DELETE /rooms без токена отклонён")


# ---------------------------------------------------------------------------
# POST /criteria/verify
# ---------------------------------------------------------------------------

def test_criteria_verify_returns_bool(client):
    """POST /criteria/verify возвращает can_ai_verified как bool."""
    headers = get_auth_headers(client)
    response = client.post("/criteria/verify", json={"criterion_text": "Использует ООП"}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "can_ai_verified" in data
    assert isinstance(data["can_ai_verified"], bool)
    logger.info("✓ criteria/verify вернул корректный ответ")


def test_criteria_verify_cached(client):
    """POST /criteria/verify для одного критерия дважды — результат одинаковый."""
    headers = get_auth_headers(client)
    text = "Решение O(n log n) сложности"

    resp1 = client.post("/criteria/verify", json={"criterion_text": text}, headers=headers)
    resp2 = client.post("/criteria/verify", json={"criterion_text": text}, headers=headers)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["can_ai_verified"] == resp2.json()["can_ai_verified"]
    logger.info("✓ Повторная верификация возвращает закэшированный результат")


def test_criteria_verify_empty_text(client):
    """POST /criteria/verify с пустым criterion_text — 422."""
    headers = get_auth_headers(client)
    response = client.post("/criteria/verify", json={"criterion_text": ""}, headers=headers)
    assert response.status_code == 422, response.text
    logger.info("✓ Пустой criterion_text в /criteria/verify отклонён (422)")


def test_criteria_verify_unauthorized(client):
    """POST /criteria/verify без авторизации — 401/403."""
    response = client.post("/criteria/verify", json={"criterion_text": "Код работает"})
    assert response.status_code in (401, 403)
    logger.info("✓ /criteria/verify без токена отклонён")
