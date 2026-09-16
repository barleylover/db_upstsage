from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

import sqlglot

from app.domain.enums import (
    CheckStatus,
    DocumentFieldKey,
    Severity,
    Verdict,
)
from app.domain.models import (
    ChangeSpec,
    DocumentReviewCheck,
    DocumentReviewResult,
    ReviewChangeDocumentRequest,
    SqlPack,
)
from app.repositories.change_repository import ChangeRepository


SQL_ARTIFACT_KEYS = {
    DocumentFieldKey.PRECHECK_SQL,
    DocumentFieldKey.BACKUP_SQL,
    DocumentFieldKey.EXECUTION_SQL,
    DocumentFieldKey.VERIFICATION_SQL,
    DocumentFieldKey.ROLLBACK_SQL,
}

BASIC_FIELD_KEYS = {
    DocumentFieldKey.ENVIRONMENT,
    DocumentFieldKey.DATABASE,
    DocumentFieldKey.SCHEMA,
    DocumentFieldKey.TARGET_TABLE,
    DocumentFieldKey.OPERATION,
}

PREDICATE_OR_MUTATION_KEYS = {
    DocumentFieldKey.PREDICATES,
    DocumentFieldKey.MUTATIONS,
}


def _normalize_sql(sql_text: str | None) -> str | None:
    if sql_text is None:
        return None
    try:
        parsed = sqlglot.parse(sql_text, read="postgres")
        if not isinstance(parsed, list):
            return None
        statements = [statement for statement in parsed if statement is not None]
        if len(statements) != 1:
            return None
        return statements[0].sql(dialect="postgres", pretty=False, normalize=True, comments=False)
    except Exception:
        return None


def _sql_values_equal(actual: str, submitted: str) -> bool:
    norm_actual = _normalize_sql(actual)
    norm_submitted = _normalize_sql(submitted)
    if norm_actual is None or norm_submitted is None:
        return False
    def _strip(value: str) -> str:
        value = value.strip()
        if value.endswith(";"):
            value = value[:-1].strip()
        return value
    return _strip(norm_actual) == _strip(norm_submitted)


def _model_list_equal(left: list[Any], right: list[Any]) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    if len(left) != len(right):
        return False
    if not all(isinstance(item, dict) for item in left) or not all(isinstance(item, dict) for item in right):
        return False

    def _json_key(item: dict[str, Any]) -> str:
        return json.dumps(item, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))

    left_keys = sorted(_json_key(item) for item in left)
    right_keys = sorted(_json_key(item) for item in right)
    return left_keys == right_keys


def _value_for_field(spec: ChangeSpec, sql_pack: SqlPack, field_key: DocumentFieldKey) -> Any:
    if field_key in BASIC_FIELD_KEYS | {
        DocumentFieldKey.TITLE,
        DocumentFieldKey.PREDICATES,
        DocumentFieldKey.MUTATIONS,
        DocumentFieldKey.EXPECTED_ROW_COUNT,
    }:
        if field_key is DocumentFieldKey.TITLE:
            return f"{spec.operation.value} {spec.schema}.{spec.target_table} 변경"
        if field_key is DocumentFieldKey.ENVIRONMENT:
            return spec.environment
        if field_key is DocumentFieldKey.DATABASE:
            return spec.database
        if field_key is DocumentFieldKey.SCHEMA:
            return spec.schema
        if field_key is DocumentFieldKey.TARGET_TABLE:
            return spec.target_table
        if field_key is DocumentFieldKey.OPERATION:
            return spec.operation.value
        if field_key is DocumentFieldKey.PREDICATES:
            return [
                predicate.model_dump(by_alias=True, mode="json")
                for predicate in spec.predicates
            ]
        if field_key is DocumentFieldKey.MUTATIONS:
            return [
                mutation.model_dump(by_alias=True, mode="json")
                for mutation in spec.mutations
            ]
        if field_key is DocumentFieldKey.EXPECTED_ROW_COUNT:
            return spec.expected_row_count
    if field_key in SQL_ARTIFACT_KEYS:
        if field_key is DocumentFieldKey.PRECHECK_SQL:
            return sql_pack.precheck_sql
        if field_key is DocumentFieldKey.BACKUP_SQL:
            return sql_pack.backup_sql
        if field_key is DocumentFieldKey.EXECUTION_SQL:
            return sql_pack.execution_sql
        if field_key is DocumentFieldKey.VERIFICATION_SQL:
            return sql_pack.verification_sql
        if field_key is DocumentFieldKey.ROLLBACK_SQL:
            return sql_pack.rollback_sql
    return None


def review_change_document(
    repository: ChangeRepository,
    spec_id: str,
    request: ReviewChangeDocumentRequest,
) -> DocumentReviewResult:
    spec = repository.get_spec(spec_id)
    sql_pack = repository.get_sql_pack(spec_id)
    document = repository.get_change_document(spec_id)

    checks: list[DocumentReviewCheck] = []
    has_fail = False
    has_review = False

    try:
        submitted_by_key = {field.key: field.value for field in request.fields}
    except Exception as exc:
        raise ValueError(f"invalid request fields: {exc}") from exc

    # D001: required fields missing
    for field in document.fields:
        if not field.required:
            continue
        if field.key not in submitted_by_key:
            checks.append(DocumentReviewCheck(
                rule_id="D001",
                status=CheckStatus.FAIL,
                severity=Severity.CRITICAL,
                field_key=field.key,
                message=f"필수 필드 '{field.key.value}'가 제출되지 않았습니다.",
                expected="누락 없음",
                actual="누락",
                suggested_fix=f"'{field.key.value}' 필드를 추가해 주세요.",
            ))
            has_fail = True

    # D002/D003/D004/D006/D008: field-level comparison
    for field in document.fields:
        key = field.key
        if key not in submitted_by_key:
            continue

        submitted_value = submitted_by_key[key]

        if key in BASIC_FIELD_KEYS:
            expected_value = _value_for_field(spec, sql_pack, key)
            if submitted_value != expected_value:
                checks.append(DocumentReviewCheck(
                    rule_id="D002",
                    status=CheckStatus.FAIL,
                    severity=Severity.CRITICAL,
                    field_key=key,
                    message=f"기본 대상 정보가 일치하지 않습니다.",
                    expected=expected_value,
                    actual=submitted_value,
                    suggested_fix=f"'{key.value}' 값을 기준과 동일하게 맞춰 주세요.",
                ))
                has_fail = True
        elif key in PREDICATE_OR_MUTATION_KEYS:
            expected_value = _value_for_field(spec, sql_pack, key)
            if not _model_list_equal(expected_value, submitted_value):
                checks.append(DocumentReviewCheck(
                    rule_id="D003",
                    status=CheckStatus.FAIL,
                    severity=Severity.CRITICAL,
                    field_key=key,
                    message=f"'{key.value}' 내용이 기준과 일치하지 않습니다.",
                    expected=expected_value,
                    actual=submitted_value,
                    suggested_fix=f"목록의 순서·key 순서와 무관하게 동일하도록 맞춰 주세요.",
                ))
                has_fail = True
        elif key is DocumentFieldKey.EXPECTED_ROW_COUNT:
            expected_value = _value_for_field(spec, sql_pack, key)
            if submitted_value != expected_value:
                checks.append(DocumentReviewCheck(
                    rule_id="D004",
                    status=CheckStatus.REVIEW,
                    severity=Severity.WARNING,
                    field_key=key,
                    message="예상 영향 행 수가 기준과 다릅니다.",
                    expected=expected_value,
                    actual=submitted_value,
                    suggested_fix="실행 전 최종 확인이 필요합니다.",
                ))
                has_review = True
        elif key in SQL_ARTIFACT_KEYS:
            expected_value = _value_for_field(spec, sql_pack, key)
            if not _sql_values_equal(expected_value, submitted_value):
                checks.append(DocumentReviewCheck(
                    rule_id="D006",
                    status=CheckStatus.FAIL,
                    severity=Severity.CRITICAL,
                    field_key=key,
                    message=f"'{key.value}'의 SQL 내용이 기준과 일치하지 않습니다.",
                    expected=expected_value,
                    actual=submitted_value,
                    suggested_fix="공백·줄바꿈·들여쓰기·주석 차이는 허용되나 SQL 구조나 조건이 바뀌면 안 됩니다.",
                ))
                has_fail = True
        elif key is DocumentFieldKey.TITLE:
            expected_value = _value_for_field(spec, sql_pack, key)
            if submitted_value != expected_value:
                checks.append(DocumentReviewCheck(
                    rule_id="D008",
                    status=CheckStatus.REVIEW,
                    severity=Severity.WARNING,
                    field_key=key,
                    message="문서 제목이 기준과 다릅니다.",
                    expected=expected_value,
                    actual=submitted_value,
                    suggested_fix="제목이 변경 의도와 일치하는지 확인해 주세요.",
                ))
                has_review = True

    # D007: extra fields
    template_keys = {field.key for field in document.fields}
    for submitted_key in submitted_by_key:
        if submitted_key not in template_keys:
            checks.append(DocumentReviewCheck(
                rule_id="D007",
                status=CheckStatus.REVIEW,
                severity=Severity.WARNING,
                field_key=submitted_key,
                message=f"기준 템플릿에 없는 필드가 제출되었습니다.",
                expected="없음",
                actual=submitted_key.value,
                suggested_fix="이 필드가 변경 의도와 맞는지 검토해 주세요.",
            ))
            has_review = True

    # D005: stale document
    if (
        document.spec_version != spec.version
        or document.content_hash != spec.content_hash
        or document.sql_pack_revision != sql_pack.revision
    ):
        checks.append(DocumentReviewCheck(
            rule_id="D005",
            status=CheckStatus.FAIL,
            severity=Severity.CRITICAL,
            field_key=None,
            message="기준 문서가 현재 변경관리 대상보다 오래되었습니다.",
            expected={
                "specVersion": spec.version,
                "contentHash": spec.content_hash,
                "sqlPackRevision": sql_pack.revision,
            },
            actual={
                "specVersion": document.spec_version,
                "contentHash": document.content_hash,
                "sqlPackRevision": document.sql_pack_revision,
            },
            suggested_fix="최신 변경관리 문서로 다시 검토한 뒤 재제출해 주세요.",
        ))
        has_fail = True

    if has_fail:
        verdict = Verdict.BLOCK
    elif has_review:
        verdict = Verdict.REVIEW
    else:
        verdict = Verdict.READY

    return DocumentReviewResult(
        spec_id=spec_id,
        spec_version=spec.version,
        content_hash=spec.content_hash,
        sql_pack_revision=sql_pack.revision,
        verdict=verdict,
        checks=checks,
        reviewed_at=datetime.now(timezone.utc),
    )
