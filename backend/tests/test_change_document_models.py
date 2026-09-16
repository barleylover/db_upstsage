from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import DocumentFieldKey, DocumentFieldSource
from app.domain.models import (
    ChangeDocumentField,
    DocumentTemplateField,
    GenerateChangeDocumentRequest,
)


def test_generate_change_document_request_defaults():
    request = GenerateChangeDocumentRequest()
    assert request.template_name == "DEFAULT"
    assert request.fields is None


def test_generate_change_document_request_preserves_fields_order_label_and_required():
    request = GenerateChangeDocumentRequest(
        template_name="CUSTOM",
        fields=[
            DocumentTemplateField(key=DocumentFieldKey.TARGET_TABLE, label="대상 테이블", required=True),
            DocumentTemplateField(key=DocumentFieldKey.EXECUTION_SQL, label="실행 SQL", required=False),
        ],
    )
    assert request.template_name == "CUSTOM"
    assert len(request.fields) == 2

    first, last = request.fields[0], request.fields[1]
    assert first.key == DocumentFieldKey.TARGET_TABLE
    assert first.label == "대상 테이블"
    assert first.required is True
    assert last.key == DocumentFieldKey.EXECUTION_SQL
    assert last.label == "실행 SQL"
    assert last.required is False


def test_generate_change_document_request_invalid_key_is_rejected():
    with pytest.raises(ValidationError):
        GenerateChangeDocumentRequest(
            fields=[DocumentTemplateField(key="not_a_real_key", label="X", required=True)]
        )
