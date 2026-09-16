from __future__ import annotations

import pytest

from app.core.errors import ConflictError
from app.domain.enums import (
    ArtifactName,
    CheckStatus,
    DocumentFieldKey,
    DocumentFieldSource,
    Operation,
    Operator,
    Severity,
    SpecStatus,
    ValueType,
    Verdict,
)
from app.domain.models import (
    ArtifactName,
    ColumnSchema,
    ChangeDocument,
    ChangeDocumentField,
    DocumentReviewCheck,
    DocumentReviewResult,
    DocumentTemplateField,
    GenerateChangeDocumentRequest,
    Predicate,
    ReviewChangeDocumentRequest,
    SchemaInput,
    SubmittedDocumentField,
    TableSchema,
    UpdateSqlArtifactRequest,
)
from app.services.change_document_review_service import review_change_document
from app.services.change_document_service import generate_change_document
from app.services.sql_pack_service import update_sql_artifact
from tests.conftest import create_confirmed_pack, golden_request


def test_review_change_document_ready_when_submitted_matches_reference(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    request = ReviewChangeDocumentRequest(
        fields=[
            SubmittedDocumentField(key=field.key, value=field.value)
            for field in document.fields
        ],
    )
    result = review_change_document(env.repository, spec_id, request)

    assert result.spec_id == spec_id
    assert result.spec_version == document.spec_version
    assert result.content_hash == document.content_hash
    assert result.sql_pack_revision == document.sql_pack_revision
    assert result.verdict == Verdict.READY
    assert len(result.checks) == 0


def test_review_change_document_d001_block_when_required_field_missing(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
        if field.key is not DocumentFieldKey.PREDICATES
    ]
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D001" in rule_ids
    assert any(check.field_key is DocumentFieldKey.PREDICATES for check in result.checks)
    assert result.verdict == Verdict.BLOCK
    assert any(check.status is CheckStatus.FAIL and check.severity is Severity.CRITICAL for check in result.checks)


def test_review_change_document_d002_block_when_target_table_changed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    for field in submitted_fields:
        if field.key is DocumentFieldKey.TARGET_TABLE:
            field.value = "orders_archived"
            break
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D002" in rule_ids
    assert any(check.field_key is DocumentFieldKey.TARGET_TABLE for check in result.checks)
    assert result.verdict == Verdict.BLOCK


def test_review_change_document_ready_when_predicates_order_only_changed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    predicates_field = next(field for field in document.fields if field.key is DocumentFieldKey.PREDICATES)
    original_predicates = predicates_field.value

    reordered_predicates = list(reversed(original_predicates))

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    for field in submitted_fields:
        if field.key is DocumentFieldKey.PREDICATES:
            field.value = reordered_predicates
            break

    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    assert len(result.checks) == 0
    assert result.verdict == Verdict.READY


def test_review_change_document_d004_review_when_expected_row_count_changed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    for field in submitted_fields:
        if field.key is DocumentFieldKey.EXPECTED_ROW_COUNT:
            field.value = 19
            break
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D004" in rule_ids
    assert any(check.field_key is DocumentFieldKey.EXPECTED_ROW_COUNT for check in result.checks)
    assert result.verdict == Verdict.REVIEW


def test_review_change_document_d006_block_when_execution_sql_condition_removed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    execution_sql_field = next(field for field in document.fields if field.key is DocumentFieldKey.EXECUTION_SQL)
    modified_sql = execution_sql_field.value.replace("AND\n  \"tenant_id\" = 42", "")

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    for field in submitted_fields:
        if field.key is DocumentFieldKey.EXECUTION_SQL:
            field.value = modified_sql
            break
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D006" in rule_ids
    assert any(check.field_key is DocumentFieldKey.EXECUTION_SQL for check in result.checks)
    assert result.verdict == Verdict.BLOCK


def test_review_change_document_ready_when_sql_only_whitespace_comment_changed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    execution_sql_field = next(field for field in document.fields if field.key is DocumentFieldKey.EXECUTION_SQL)
    modified_sql = (
        "/* reviewer note */\n"
        + execution_sql_field.value.replace("\n", "\n    ")
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
        if field.key is not DocumentFieldKey.EXECUTION_SQL
    ]
    submitted_fields.append(SubmittedDocumentField(key=DocumentFieldKey.EXECUTION_SQL, value=modified_sql))

    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    assert not any(check.rule_id == "D006" and check.status is CheckStatus.FAIL for check in result.checks)
    assert result.verdict == Verdict.READY


def test_review_change_document_d006_block_when_second_sql_appended(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    execution_sql_field = next(field for field in document.fields if field.key is DocumentFieldKey.EXECUTION_SQL)
    appended_sql = execution_sql_field.value + "\nDELETE FROM \"public\".\"orders\" WHERE \"status\" = 'cancelled';"

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
        if field.key is not DocumentFieldKey.EXECUTION_SQL
    ]
    submitted_fields.append(SubmittedDocumentField(key=DocumentFieldKey.EXECUTION_SQL, value=appended_sql))

    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D006" in rule_ids
    assert any(check.field_key is DocumentFieldKey.EXECUTION_SQL for check in result.checks)
    assert result.verdict == Verdict.BLOCK


def test_review_change_document_d003_block_when_predicates_nested_mixed_types(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    predicates_field = next(field for field in document.fields if field.key is DocumentFieldKey.PREDICATES)
    nested_predicates = [
        {**predicates_field.value[0], "extra": {"a": 1}},
        {"column": predicates_field.value[1]["column"], "operator": predicates_field.value[1]["operator"], "value": "2026-09-01T00:00:00+09:00", "mixed": [1, "two", None]},
    ]

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
        if field.key is not DocumentFieldKey.PREDICATES
    ]
    submitted_fields.append(SubmittedDocumentField(key=DocumentFieldKey.PREDICATES, value=nested_predicates))

    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D003" in rule_ids
    assert any(check.field_key is DocumentFieldKey.PREDICATES for check in result.checks)
    assert result.verdict == Verdict.BLOCK


def test_review_change_document_d005_block_when_document_is_stale(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    update_request = UpdateSqlArtifactRequest(
        sql=env.repository.get_sql_pack(spec_id).execution_sql,
    )
    update_sql_artifact(
        env.repository,
        spec_id,
        ArtifactName.EXECUTION_SQL,
        update_request.sql,
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D005" in rule_ids
    assert result.verdict == Verdict.BLOCK


def test_review_change_document_d007_review_when_extra_field_submitted(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(
            template_name="CUSTOM",
            fields=[
                DocumentTemplateField(key=DocumentFieldKey.TARGET_TABLE, label="대상 테이블", required=True),
            ],
        ),
    )

    submitted_fields = [
        SubmittedDocumentField(key=DocumentFieldKey.TARGET_TABLE, value=document.fields[0].value),
        SubmittedDocumentField(key=DocumentFieldKey.OPERATION, value="DELETE"),
    ]
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D007" in rule_ids
    assert any(check.field_key is DocumentFieldKey.OPERATION for check in result.checks)
    assert result.verdict == Verdict.REVIEW


def test_review_change_document_d008_review_when_title_changed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    for field in submitted_fields:
        if field.key is DocumentFieldKey.TITLE:
            field.value = "다른 제목"
            break
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D008" in rule_ids
    assert any(check.field_key is DocumentFieldKey.TITLE for check in result.checks)
    assert result.verdict == Verdict.REVIEW
    assert result.verdict != Verdict.BLOCK


def test_review_change_document_d003_block_when_predicates_malformed(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    document = generate_change_document(
        env.repository,
        spec_id,
        GenerateChangeDocumentRequest(),
    )

    submitted_fields = [
        SubmittedDocumentField(key=field.key, value=field.value)
        for field in document.fields
    ]
    for field in submitted_fields:
        if field.key is DocumentFieldKey.PREDICATES:
            field.value = "not a list"
            break
    request = ReviewChangeDocumentRequest(fields=submitted_fields)
    result = review_change_document(env.repository, spec_id, request)

    rule_ids = [check.rule_id for check in result.checks]
    assert "D003" in rule_ids
    assert any(check.field_key is DocumentFieldKey.PREDICATES for check in result.checks)
    assert result.verdict == Verdict.BLOCK
