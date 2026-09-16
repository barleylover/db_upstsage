from __future__ import annotations

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.domain.enums import DocumentFieldKey, CheckStatus, Severity, Verdict
from app.domain.models import (
    DocumentReviewCheck,
    DocumentReviewResult,
    ReviewChangeDocumentRequest,
    SubmittedDocumentField,
)


def test_review_change_document_request_preserves_order_and_value():
    request = ReviewChangeDocumentRequest(
        fields=[
            SubmittedDocumentField(key=DocumentFieldKey.TITLE, value="title value"),
            SubmittedDocumentField(key=DocumentFieldKey.OPERATION, value="UPDATE"),
            SubmittedDocumentField(key=DocumentFieldKey.EXECUTION_SQL, value=None),
        ],
    )
    assert len(request.fields) == 3
    assert request.fields[0].key == DocumentFieldKey.TITLE
    assert request.fields[0].value == "title value"
    assert request.fields[1].key == DocumentFieldKey.OPERATION
    assert request.fields[1].value == "UPDATE"
    assert request.fields[2].key == DocumentFieldKey.EXECUTION_SQL
    assert request.fields[2].value is None


def test_review_change_document_request_empty_fields_is_rejected():
    with pytest.raises(ValidationError):
        ReviewChangeDocumentRequest(fields=[])


def test_review_change_document_request_duplicate_key_is_rejected():
    with pytest.raises(ValidationError):
        ReviewChangeDocumentRequest(
            fields=[
                SubmittedDocumentField(key=DocumentFieldKey.TITLE, value="title value"),
                SubmittedDocumentField(key=DocumentFieldKey.TITLE, value="another value"),
            ]
        )


def test_document_review_result_camel_case_serialization():
    now = datetime.now(timezone.utc)
    result = DocumentReviewResult(
        spec_id="s1",
        spec_version=2,
        content_hash="fe0dfc46e0b7e1931496d4b8f5652393e1ff1b51e540f686cd54b4fb68b67d48",
        sql_pack_revision=1,
        verdict=Verdict.READY,
        checks=[
            DocumentReviewCheck(
                rule_id="RULE_001",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                field_key=DocumentFieldKey.TITLE,
                message="title matches spec",
                expected="title value",
                actual="title value",
                suggested_fix=None,
            ),
        ],
        reviewed_at=now,
    )
    dumped = result.model_dump(by_alias=True, mode="json")
    assert dumped["specId"] == "s1"
    assert dumped["specVersion"] == 2
    assert dumped["contentHash"] == "fe0dfc46e0b7e1931496d4b8f5652393e1ff1b51e540f686cd54b4fb68b67d48"
    assert dumped["sqlPackRevision"] == 1
    assert dumped["verdict"] == "READY"
    check = dumped["checks"][0]
    assert check["ruleId"] == "RULE_001"
    assert check["fieldKey"] == "title"
    assert "reviewedAt" in dumped
