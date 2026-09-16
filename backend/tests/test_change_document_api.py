from __future__ import annotations

import pytest

from app.domain.enums import DocumentFieldKey, DocumentFieldSource
from app.domain.models import (
    ChangeDocument,
    DocumentFieldKey,
    DocumentFieldSource,
    GenerateChangeDocumentRequest,
    DocumentTemplateField,
)
from tests.conftest import create_confirmed_pack, golden_request


def test_change_document_api_default_template(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    response = env.client.post(
        f"/api/v1/change-specs/{spec_id}/change-document",
        json=GenerateChangeDocumentRequest().model_dump(by_alias=True, exclude_none=True),
    )
    assert response.status_code == 201
    assert response.headers["X-Request-ID"]

    body = response.json()
    assert body["specId"] == spec_id
    assert body["templateName"] == "DEFAULT"
    assert body["specVersion"] >= 1
    assert "contentHash" in body
    assert "sqlPackRevision" in body
    assert len(body["fields"]) == 14

    keys = [item["key"] for item in body["fields"]]
    assert keys == [
        DocumentFieldKey.TITLE,
        DocumentFieldKey.ENVIRONMENT,
        DocumentFieldKey.DATABASE,
        DocumentFieldKey.SCHEMA,
        DocumentFieldKey.TARGET_TABLE,
        DocumentFieldKey.OPERATION,
        DocumentFieldKey.PREDICATES,
        DocumentFieldKey.MUTATIONS,
        DocumentFieldKey.EXPECTED_ROW_COUNT,
        DocumentFieldKey.PRECHECK_SQL,
        DocumentFieldKey.BACKUP_SQL,
        DocumentFieldKey.EXECUTION_SQL,
        DocumentFieldKey.VERIFICATION_SQL,
        DocumentFieldKey.ROLLBACK_SQL,
    ]

    execution_sql_field = next(item for item in body["fields"] if item["key"] == DocumentFieldKey.EXECUTION_SQL)
    assert execution_sql_field["source"] == DocumentFieldSource.SQL_PACK


def test_change_document_api_requested_fields(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)

    request = GenerateChangeDocumentRequest(
        template_name="CUSTOM",
        fields=[
            DocumentTemplateField(key=DocumentFieldKey.TARGET_TABLE, label="대상 테이블(custom)", required=True),
            DocumentTemplateField(key=DocumentFieldKey.EXECUTION_SQL, label="실행 SQL", required=False),
            DocumentTemplateField(key=DocumentFieldKey.OPERATION, label="작업", required=True),
        ],
    )
    response = env.client.post(
        f"/api/v1/change-specs/{spec_id}/change-document",
        json=request.model_dump(by_alias=True, exclude_none=True),
    )
    assert response.status_code == 201

    body = response.json()
    assert body["templateName"] == "CUSTOM"
    assert len(body["fields"]) == 3

    labels = {item["key"]: item["label"] for item in body["fields"]}
    required = {item["key"]: item["required"] for item in body["fields"]}
    sources = {item["key"]: item["source"] for item in body["fields"]}

    assert labels[DocumentFieldKey.TARGET_TABLE] == "대상 테이블(custom)"
    assert required[DocumentFieldKey.TARGET_TABLE] is True

    assert labels[DocumentFieldKey.EXECUTION_SQL] == "실행 SQL"
    assert required[DocumentFieldKey.EXECUTION_SQL] is False

    assert labels[DocumentFieldKey.OPERATION] == "작업"
    assert required[DocumentFieldKey.OPERATION] is True

    assert sources[DocumentFieldKey.TARGET_TABLE] == DocumentFieldSource.CHANGE_SPEC
    assert sources[DocumentFieldKey.EXECUTION_SQL] == DocumentFieldSource.SQL_PACK
    assert sources[DocumentFieldKey.OPERATION] == DocumentFieldSource.CHANGE_SPEC

    assert body["fields"][0]["key"] == DocumentFieldKey.TARGET_TABLE
    assert body["fields"][1]["key"] == DocumentFieldKey.EXECUTION_SQL
    assert body["fields"][2]["key"] == DocumentFieldKey.OPERATION


def test_change_document_api_unconfirmed_spec(env, golden_request):
    interpreted = env.client.post(
        "/api/v1/change-specs/interpret",
        json=golden_request,
    )
    assert interpreted.status_code == 201, interpreted.text
    spec_id = interpreted.json()["specId"]

    response = env.client.post(
        f"/api/v1/change-specs/{spec_id}/change-document",
        json=GenerateChangeDocumentRequest().model_dump(by_alias=True, exclude_none=True),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SPEC_NOT_CONFIRMED"


def test_change_document_api_openapi_registered():
    from app.main import create_app
    from app.repositories.change_repository import InMemoryChangeRepository
    from app.services.solar_client import FakeSolarClient
    from app.core.config import Settings
    from starlette.testclient import TestClient

    app = create_app(
        settings=Settings(solar_mode="fake", cors_allow_origins=[]),
        repository=InMemoryChangeRepository(),
        solar_client=FakeSolarClient(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert "/api/v1/change-specs/{spec_id}/change-document" in paths
    assert paths["/api/v1/change-specs/{spec_id}/change-document"]["post"]["operationId"] == "create_change_document_api_v1_change_specs__spec_id__change_document_post"
