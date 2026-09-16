from __future__ import annotations

import pytest

from app.core.errors import ConflictError
from app.domain.enums import DocumentFieldKey, DocumentFieldSource
from app.domain.models import (
    ChangeDocument,
    DocumentTemplateField,
    GenerateChangeDocumentRequest,
)
from app.services.change_document_service import generate_change_document
from tests.conftest import create_confirmed_pack


def test_change_document_service_default_template(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    assert isinstance(document, ChangeDocument)
    assert document.spec_id == spec_id
    assert len(document.fields) == 14
    assert document.template_name == "DEFAULT"
    assert document.spec_version >= 1
    assert document.content_hash == env.repository.get_spec(spec_id).content_hash
    assert document.sql_pack_revision == env.repository.get_sql_pack(spec_id).revision

    keys = [field.key for field in document.fields]
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

    predicates_field = next(field for field in document.fields if field.key == DocumentFieldKey.PREDICATES)
    assert isinstance(predicates_field.value, list)
    assert all(isinstance(item, dict) for item in predicates_field.value)
    assert predicates_field.source == DocumentFieldSource.CHANGE_SPEC

    mutations_field = next(field for field in document.fields if field.key == DocumentFieldKey.MUTATIONS)
    assert isinstance(mutations_field.value, list)
    assert all(isinstance(item, dict) for item in mutations_field.value)
    assert mutations_field.source == DocumentFieldSource.CHANGE_SPEC

    sql_field = next(field for field in document.fields if field.key == DocumentFieldKey.EXECUTION_SQL)
    assert isinstance(sql_field.value, str)
    assert sql_field.source == DocumentFieldSource.SQL_PACK

    retrieved = env.repository.get_change_document(spec_id)
    assert retrieved.spec_id == document.spec_id
    assert retrieved.fields == document.fields


def test_change_document_service_requested_fields(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)

    request = GenerateChangeDocumentRequest(
        template_name="CUSTOM",
        fields=[
            DocumentTemplateField(key=DocumentFieldKey.TARGET_TABLE, label="대상 테이블(custom)", required=True),
            DocumentTemplateField(key=DocumentFieldKey.EXECUTION_SQL, label="실행 SQL", required=False),
            DocumentTemplateField(key=DocumentFieldKey.OPERATION, label="작업", required=True),
        ],
    )
    document = generate_change_document(env.repository, spec_id, request)

    assert document.template_name == "CUSTOM"
    assert len(document.fields) == 3

    labels = {field.key: field.label for field in document.fields}
    required = {field.key: field.required for field in document.fields}
    sources = {field.key: field.source for field in document.fields}

    assert labels[DocumentFieldKey.TARGET_TABLE] == "대상 테이블(custom)"
    assert required[DocumentFieldKey.TARGET_TABLE] is True

    assert labels[DocumentFieldKey.EXECUTION_SQL] == "실행 SQL"
    assert required[DocumentFieldKey.EXECUTION_SQL] is False

    assert labels[DocumentFieldKey.OPERATION] == "작업"
    assert required[DocumentFieldKey.OPERATION] is True

    assert sources[DocumentFieldKey.TARGET_TABLE] == DocumentFieldSource.CHANGE_SPEC
    assert sources[DocumentFieldKey.EXECUTION_SQL] == DocumentFieldSource.SQL_PACK
    assert sources[DocumentFieldKey.OPERATION] == DocumentFieldSource.CHANGE_SPEC

    assert document.fields[0].key == DocumentFieldKey.TARGET_TABLE
    assert document.fields[1].key == DocumentFieldKey.EXECUTION_SQL
    assert document.fields[2].key == DocumentFieldKey.OPERATION


def test_change_document_service_unconfirmed_spec(env, golden_request):
    interpreted = env.client.post(
        "/api/v1/change-specs/interpret",
        json=golden_request,
    )
    assert interpreted.status_code == 201, interpreted.text
    spec_id = interpreted.json()["specId"]

    with pytest.raises(ConflictError) as exc_info:
        generate_change_document(
            env.repository,
            spec_id,
            GenerateChangeDocumentRequest(),
        )

    assert exc_info.value.code == "SPEC_NOT_CONFIRMED"
