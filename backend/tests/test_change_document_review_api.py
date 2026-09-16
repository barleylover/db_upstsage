from __future__ import annotations

import pytest

from app.domain.enums import DocumentFieldKey, Verdict
from app.domain.models import (
    GenerateChangeDocumentRequest,
    ReviewChangeDocumentRequest,
    SubmittedDocumentField,
)
from app.services.change_document_service import generate_change_document
from tests.conftest import create_confirmed_pack


def test_change_document_review_api_ready_when_submitted_matches_reference(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    create_response = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in create_response.fields
    ]
    request = ReviewChangeDocumentRequest(fields=fields)
    response = env.client.post(
        f"/api/v1/change-specs/{spec_id}/change-document/review",
        json=request.model_dump(by_alias=True, exclude_none=True),
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]

    body = response.json()
    assert body["specId"] == spec_id
    assert body["verdict"] == Verdict.READY


def test_change_document_review_api_block_when_target_table_changed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    create_response = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in create_response.fields
    ]
    for field in fields:
        if field.key is DocumentFieldKey.TARGET_TABLE:
            field.value = "orders_archived"
            break
    request = ReviewChangeDocumentRequest(fields=fields)
    response = env.client.post(
        f"/api/v1/change-specs/{spec_id}/change-document/review",
        json=request.model_dump(by_alias=True, exclude_none=True),
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]

    body = response.json()
    assert body["specId"] == spec_id
    assert body["verdict"] == Verdict.BLOCK

    rule_ids = [check["ruleId"] for check in body["checks"]]
    assert "D002" in rule_ids
