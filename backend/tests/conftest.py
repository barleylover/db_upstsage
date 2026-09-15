from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repositories.change_repository import InMemoryChangeRepository  # noqa: E402
from app.services.solar_client import FakeSolarClient  # noqa: E402


@dataclass
class TestEnvironment:
    client: TestClient
    repository: InMemoryChangeRepository
    solar: FakeSolarClient


@pytest.fixture
def golden_schema() -> dict:
    return {
        "database": "app",
        "schema": "public",
        "tables": [
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "dataType": "bigint", "nullable": False},
                    {"name": "tenant_id", "dataType": "bigint", "nullable": False},
                    {"name": "status", "dataType": "varchar", "nullable": False},
                    {"name": "created_at", "dataType": "timestamp", "nullable": False},
                ],
                "primaryKeyColumns": ["id"],
            }
        ],
    }


@pytest.fixture
def golden_request(golden_schema: dict) -> dict:
    return {
        "originalRequest": "tenant_id가 42이고 status가 pending이며 2026년 9월 1일 이전에 생성된 주문만 cancelled로 변경해 주세요.",
        "schemaInput": golden_schema,
    }


@pytest.fixture
def env() -> TestEnvironment:
    repository = InMemoryChangeRepository()
    solar = FakeSolarClient()
    settings = Settings(solar_mode="fake", cors_allow_origins=["http://localhost:5173"])
    app = create_app(settings=settings, repository=repository, solar_client=solar)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield TestEnvironment(client=client, repository=repository, solar=solar)


def create_confirmed_pack(env: TestEnvironment, request_payload: dict) -> tuple[str, dict]:
    interpreted = env.client.post("/api/v1/change-specs/interpret", json=request_payload)
    assert interpreted.status_code == 201, interpreted.text
    spec_id = interpreted.json()["specId"]
    confirmed = env.client.post(f"/api/v1/change-specs/{spec_id}/confirm", json={})
    assert confirmed.status_code == 200, confirmed.text
    pack = env.client.post(f"/api/v1/change-specs/{spec_id}/sql-pack")
    assert pack.status_code == 201, pack.text
    return spec_id, pack.json()
