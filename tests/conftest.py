import pytest
from src.core.server import Server
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    server = Server(['config=testing'])
    with TestClient(server.app) as client:
        yield client