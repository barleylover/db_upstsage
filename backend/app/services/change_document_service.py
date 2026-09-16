from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.errors import ConflictError
from app.domain.enums import (
    DocumentFieldKey,
    DocumentFieldSource,
    SpecStatus,
)
from app.domain.models import (
    ChangeDocument,
    ChangeDocumentField,
    ChangeSpec,
    DocumentTemplateField,
    GenerateChangeDocumentRequest,
    SqlPack,
)
from app.repositories.change_repository import ChangeRepository


def _default_template_fields(spec: ChangeSpec, sql_pack: SqlPack) -> list[ChangeDocumentField]:
    return [
        ChangeDocumentField(
            key=DocumentFieldKey.TITLE,
            label="변경관리 문서 제목",
            value=f"{spec.operation.value} {spec.schema}.{spec.target_table} 변경",
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.ENVIRONMENT,
            label="운영 환경",
            value=spec.environment,
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.DATABASE,
            label="데이터베이스",
            value=spec.database,
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.SCHEMA,
            label="스키마",
            value=spec.schema,
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.TARGET_TABLE,
            label="대상 테이블",
            value=spec.target_table,
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.OPERATION,
            label="작업",
            value=spec.operation.value,
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.PREDICATES,
            label="적용 대상(predicates)",
            value=[predicate.model_dump(by_alias=True, mode="json") for predicate in spec.predicates],
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.MUTATIONS,
            label="변경 내용(mutations)",
            value=[mutation.model_dump(by_alias=True, mode="json") for mutation in spec.mutations],
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.EXPECTED_ROW_COUNT,
            label="예상 영향 행 수",
            value=spec.expected_row_count,
            required=True,
            source=DocumentFieldSource.CHANGE_SPEC,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.PRECHECK_SQL,
            label="사전 확인 SQL",
            value=sql_pack.precheck_sql,
            required=True,
            source=DocumentFieldSource.SQL_PACK,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.BACKUP_SQL,
            label="백업 SQL",
            value=sql_pack.backup_sql,
            required=True,
            source=DocumentFieldSource.SQL_PACK,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.EXECUTION_SQL,
            label="실행 SQL",
            value=sql_pack.execution_sql,
            required=True,
            source=DocumentFieldSource.SQL_PACK,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.VERIFICATION_SQL,
            label="검증 SQL",
            value=sql_pack.verification_sql,
            required=True,
            source=DocumentFieldSource.SQL_PACK,
        ),
        ChangeDocumentField(
            key=DocumentFieldKey.ROLLBACK_SQL,
            label="롤백 SQL",
            value=sql_pack.rollback_sql,
            required=True,
            source=DocumentFieldSource.SQL_PACK,
        ),
    ]


def generate_change_document(
    repository: ChangeRepository,
    spec_id: str,
    request: GenerateChangeDocumentRequest,
) -> ChangeDocument:
    spec = repository.get_spec(spec_id)
    if spec.status != SpecStatus.CONFIRMED:
        raise ConflictError(
            code="SPEC_NOT_CONFIRMED",
            message="ChangeSpec is not confirmed yet.",
            details={"spec_id": spec_id, "status": spec.status},
        )

    sql_pack = repository.get_sql_pack(spec_id)

    if not request.fields:
        fields = _default_template_fields(spec, sql_pack)
    else:
        fields = _build_requested_fields(request.fields, spec, sql_pack)

    document = ChangeDocument(
        spec_id=spec.spec_id,
        spec_version=spec.version,
        content_hash=spec.content_hash,
        sql_pack_revision=sql_pack.revision,
        template_name=request.template_name,
        fields=fields,
        generated_at=datetime.now(timezone.utc),
    )

    repository.save_change_document(document)
    return document


def _build_requested_fields(
    requested_fields: list[DocumentTemplateField],
    spec: ChangeSpec,
    sql_pack: SqlPack,
) -> list[ChangeDocumentField]:
    def _value(key: DocumentFieldKey) -> Any:
        if key is DocumentFieldKey.TITLE:
            return f"{spec.operation.value} {spec.schema}.{spec.target_table} 변경"
        if key is DocumentFieldKey.ENVIRONMENT:
            return spec.environment
        if key is DocumentFieldKey.DATABASE:
            return spec.database
        if key is DocumentFieldKey.SCHEMA:
            return spec.schema
        if key is DocumentFieldKey.TARGET_TABLE:
            return spec.target_table
        if key is DocumentFieldKey.OPERATION:
            return spec.operation.value
        if key is DocumentFieldKey.PREDICATES:
            return [p.model_dump(by_alias=True, mode="json") for p in spec.predicates]
        if key is DocumentFieldKey.MUTATIONS:
            return [m.model_dump(by_alias=True, mode="json") for m in spec.mutations]
        if key is DocumentFieldKey.EXPECTED_ROW_COUNT:
            return spec.expected_row_count
        if key is DocumentFieldKey.PRECHECK_SQL:
            return sql_pack.precheck_sql
        if key is DocumentFieldKey.BACKUP_SQL:
            return sql_pack.backup_sql
        if key is DocumentFieldKey.EXECUTION_SQL:
            return sql_pack.execution_sql
        if key is DocumentFieldKey.VERIFICATION_SQL:
            return sql_pack.verification_sql
        if key is DocumentFieldKey.ROLLBACK_SQL:
            return sql_pack.rollback_sql
        raise ValueError(f"unsupported DocumentFieldKey: {key}")

    def _source(key: DocumentFieldKey) -> DocumentFieldSource:
        if key in {
            DocumentFieldKey.PRECHECK_SQL,
            DocumentFieldKey.BACKUP_SQL,
            DocumentFieldKey.EXECUTION_SQL,
            DocumentFieldKey.VERIFICATION_SQL,
            DocumentFieldKey.ROLLBACK_SQL,
        }:
            return DocumentFieldSource.SQL_PACK
        return DocumentFieldSource.CHANGE_SPEC

    result: list[ChangeDocumentField] = []
    for requested in requested_fields:
        result.append(ChangeDocumentField(
            key=requested.key,
            label=requested.label,
            value=_value(requested.key),
            required=requested.required,
            source=_source(requested.key),
        ))
    return result
