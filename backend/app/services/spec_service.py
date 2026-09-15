from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.errors import ConflictError, DomainValidationError
from app.domain.enums import DBMS, SpecStatus
from app.domain.models import (
    ChangeSpec,
    ChangeSpecDraft,
    ConfirmSpecRequest,
    InterpretChangeRequest,
    SchemaInput,
)
from app.repositories.change_repository import ChangeRepository
from app.services.solar_client import SolarClient


def _normalized_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def compute_content_hash(draft: ChangeSpecDraft) -> str:
    payload = {
        "dbms": draft.dbms.value,
        "environment": draft.environment.strip().lower(),
        "database": (draft.database or "").strip().lower(),
        "schema": (draft.schema or "").strip().lower(),
        "targetTable": draft.target_table.strip().lower(),
        "identityKeyColumns": sorted(column.strip().lower() for column in draft.identity_key_columns),
        "operation": draft.operation.value,
        "predicates": sorted(
            (
                predicate.column.strip().lower(),
                predicate.operator.value,
                predicate.value_type.value,
                json.dumps(_normalized_value(predicate.value), ensure_ascii=False, sort_keys=True),
            )
            for predicate in draft.predicates
        ),
        "mutations": sorted(
            (
                mutation.column.strip().lower(),
                mutation.value_type.value,
                json.dumps(_normalized_value(mutation.value), ensure_ascii=False, sort_keys=True),
            )
            for mutation in draft.mutations
        ),
        "expectedRowCount": draft.expected_row_count,
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _find_table(schema_input: SchemaInput, table_name: str):
    for table in schema_input.tables:
        if table.name.lower() == table_name.lower():
            return table
    raise DomainValidationError(
        "UNKNOWN_TARGET_TABLE",
        "The target table does not exist in the supplied schema",
        {"targetTable": table_name},
    )


def validate_draft_against_schema(draft: ChangeSpecDraft, schema_input: SchemaInput) -> None:
    if draft.dbms != DBMS.POSTGRESQL:
        raise DomainValidationError("UNSUPPORTED_DBMS", "Only PostgreSQL is supported")
    table = _find_table(schema_input, draft.target_table)
    columns = {column.name.lower() for column in table.columns}
    used_columns = {
        *(column.lower() for column in draft.identity_key_columns),
        *(predicate.column.lower() for predicate in draft.predicates),
        *(mutation.column.lower() for mutation in draft.mutations),
    }
    missing = sorted(used_columns - columns)
    if missing:
        raise DomainValidationError(
            "UNKNOWN_COLUMN",
            "The ChangeSpec contains columns not present in the supplied schema",
            {"columns": missing},
        )


class SpecService:
    def __init__(self, repository: ChangeRepository, solar_client: SolarClient) -> None:
        self._repository = repository
        self._solar_client = solar_client

    def interpret(self, request: InterpretChangeRequest) -> ChangeSpec:
        draft = self._solar_client.interpret(request)
        draft = draft.model_copy(
            update={
                "database": draft.database or request.schema_input.database,
                "schema": draft.schema or request.schema_input.schema,
            }
        )
        validate_draft_against_schema(draft, request.schema_input)
        spec = ChangeSpec(
            **draft.model_dump(),
            spec_id=str(uuid4()),
            version=1,
            status=SpecStatus.DRAFT,
            content_hash=compute_content_hash(draft),
            original_request=request.original_request,
            created_at=datetime.now(timezone.utc),
        )
        self._repository.create_spec(spec, request.schema_input)
        return spec

    def confirm(self, spec_id: str, changes: ConfirmSpecRequest) -> ChangeSpec:
        current = self._repository.get_spec(spec_id)
        if current.status != SpecStatus.DRAFT:
            raise ConflictError(
                "SPEC_NOT_DRAFT",
                "Only a DRAFT ChangeSpec can be confirmed",
                {"status": current.status.value},
            )
        updates = {
            field_name: getattr(changes, field_name)
            for field_name in changes.model_fields_set
        }
        candidate_data = current.model_dump()
        candidate_data.update(updates)
        candidate_data.pop("spec_id", None)
        candidate_data.pop("version", None)
        candidate_data.pop("status", None)
        candidate_data.pop("content_hash", None)
        candidate_data.pop("original_request", None)
        candidate_data.pop("created_at", None)
        candidate_data.pop("confirmed_at", None)
        draft = ChangeSpecDraft.model_validate(candidate_data)
        validate_draft_against_schema(draft, self._repository.get_schema(spec_id))
        if draft.unresolved_questions:
            raise ConflictError(
                "UNRESOLVED_QUESTIONS",
                "Resolve all questions before confirming the ChangeSpec",
                {"unresolvedQuestions": draft.unresolved_questions},
            )
        new_hash = compute_content_hash(draft)
        version = current.version + (1 if new_hash != current.content_hash else 0)
        confirmed = ChangeSpec(
            **draft.model_dump(),
            spec_id=current.spec_id,
            version=version,
            status=SpecStatus.CONFIRMED,
            content_hash=new_hash,
            original_request=current.original_request,
            created_at=current.created_at,
            confirmed_at=datetime.now(timezone.utc),
        )
        self._repository.replace_spec(confirmed)
        return confirmed
