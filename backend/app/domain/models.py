from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import (
    ArtifactName,
    CheckStatus,
    DBMS,
    DocumentFieldKey,
    DocumentFieldSource,
    Operation,
    Operator,
    RiskLevel,
    RollbackStatus,
    Severity,
    SpecStatus,
    ValueType,
    Verdict,
)


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        use_enum_values=False,
    )


class ColumnSchema(APIModel):
    name: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    nullable: bool = False


class TableSchema(APIModel):
    name: str = Field(min_length=1)
    columns: list[ColumnSchema] = Field(min_length=1)
    primary_key_columns: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_columns(self) -> "TableSchema":
        names = [column.name.lower() for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("column names must be unique")
        missing = [key for key in self.primary_key_columns if key.lower() not in names]
        if missing:
            raise ValueError(f"primary key columns are missing from columns: {missing}")
        return self


class SchemaInput(APIModel):
    database: str = Field(min_length=1)
    schema: str = Field(min_length=1)
    tables: list[TableSchema] = Field(min_length=1)


class InterpretChangeRequest(APIModel):
    original_request: str = Field(min_length=1, max_length=10_000)
    schema_input: SchemaInput


class Predicate(APIModel):
    column: str = Field(min_length=1)
    operator: Operator
    value: Any | None = None
    value_type: ValueType

    @model_validator(mode="after")
    def validate_null_operator(self) -> "Predicate":
        null_operator = self.operator in {Operator.IS_NULL, Operator.IS_NOT_NULL}
        if null_operator and self.value is not None:
            raise ValueError("IS_NULL and IS_NOT_NULL predicates cannot have a value")
        if not null_operator and self.value is None:
            raise ValueError("predicate value is required")
        return self


class Mutation(APIModel):
    column: str = Field(min_length=1)
    value: Any
    value_type: ValueType


class ChangeSpecDraft(APIModel):
    dbms: DBMS = DBMS.POSTGRESQL
    environment: str = "production"
    database: str | None = None
    schema: str | None = None
    target_table: str
    identity_key_columns: list[str] = Field(min_length=1)
    operation: Operation
    predicates: list[Predicate] = Field(min_length=1)
    mutations: list[Mutation] = Field(default_factory=list)
    expected_row_count: int | None = Field(default=None, ge=0)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_operation(self) -> "ChangeSpecDraft":
        if self.operation == Operation.UPDATE and not self.mutations:
            raise ValueError("UPDATE requires at least one mutation")
        if self.operation == Operation.DELETE and self.mutations:
            raise ValueError("DELETE cannot contain mutations")
        return self


class ChangeSpec(ChangeSpecDraft):
    spec_id: str
    version: int = Field(ge=1)
    status: SpecStatus
    content_hash: str
    original_request: str
    database: str
    schema: str
    created_at: datetime
    confirmed_at: datetime | None = None


class ConfirmSpecRequest(APIModel):
    environment: str | None = None
    database: str | None = None
    schema: str | None = None
    target_table: str | None = None
    identity_key_columns: list[str] | None = None
    operation: Operation | None = None
    predicates: list[Predicate] | None = None
    mutations: list[Mutation] | None = None
    expected_row_count: int | None = Field(default=None, ge=0)
    assumptions: list[str] | None = None
    unresolved_questions: list[str] | None = None


class SqlPack(APIModel):
    precheck_sql: str
    backup_sql: str
    execution_sql: str
    verification_sql: str
    rollback_sql: str
    rollback_status: RollbackStatus
    spec_id: str
    spec_version: int
    content_hash: str
    revision: int = Field(default=1, ge=1)
    updated_at: datetime


class UpdateSqlArtifactRequest(APIModel):
    sql: str = Field(min_length=1, max_length=100_000)


class ReviewEvidence(APIModel):
    execution_plan_reviewed: bool = False
    index_reviewed: bool = False
    lock_reviewed: bool = False
    concurrency_reviewed: bool = False

    @property
    def complete(self) -> bool:
        return all(
            (
                self.execution_plan_reviewed,
                self.index_reviewed,
                self.lock_reviewed,
                self.concurrency_reviewed,
            )
        )


class ReviewRequest(APIModel):
    evidence: ReviewEvidence = Field(default_factory=ReviewEvidence)


class ReviewCheck(APIModel):
    rule_id: str
    category: str
    status: CheckStatus
    severity: Severity
    message: str
    expected: Any | None = None
    actual: Any | None = None
    spec_field: str | None = None
    sql_artifact: ArtifactName | None = None
    sql_location: str | None = None
    suggested_fix: str | None = None


class ReviewResult(APIModel):
    spec_id: str
    spec_version: int
    content_hash: str
    sql_pack_revision: int
    verdict: Verdict
    risk_level: RiskLevel
    is_stale: bool = False
    checks: list[ReviewCheck]
    disclaimer: str
    reviewed_at: datetime


class ErrorResponse(APIModel):
    code: str
    message: str
    details: Any | None = None
    request_id: str


class HealthResponse(APIModel):
    status: str
    service: str
    version: str


class SubmittedDocumentField(APIModel):
    key: DocumentFieldKey
    value: Any | None = None


class ReviewChangeDocumentRequest(APIModel):
    fields: list[SubmittedDocumentField] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "ReviewChangeDocumentRequest":
        seen: list[DocumentFieldKey] = []
        for field in self.fields:
            if field.key in seen:
                raise ValueError(f"duplicate field key: {field.key.value}")
            seen.append(field.key)
        return self


class DocumentReviewCheck(APIModel):
    rule_id: str
    status: CheckStatus
    severity: Severity
    field_key: DocumentFieldKey | None = None
    message: str
    expected: Any | None = None
    actual: Any | None = None
    suggested_fix: str | None = None


class DocumentReviewResult(APIModel):
    spec_id: str
    spec_version: int = Field(ge=1)
    content_hash: str
    sql_pack_revision: int = Field(ge=1)
    verdict: Verdict
    checks: list[DocumentReviewCheck]
    reviewed_at: datetime


class DocumentTemplateField(APIModel):
    key: DocumentFieldKey
    label: str = Field(min_length=1)
    required: bool = True


class GenerateChangeDocumentRequest(APIModel):
    template_name: str = Field(default="DEFAULT")
    fields: list[DocumentTemplateField] | None = None


class ChangeDocumentField(APIModel):
    key: DocumentFieldKey
    label: str
    value: Any | None = None
    required: bool
    source: DocumentFieldSource


class ChangeDocument(APIModel):
    spec_id: str
    spec_version: int = Field(ge=1)
    content_hash: str
    sql_pack_revision: int = Field(ge=1)
    template_name: str
    fields: list[ChangeDocumentField]
    generated_at: datetime
