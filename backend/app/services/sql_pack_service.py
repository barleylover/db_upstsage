from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.errors import ConflictError, DomainValidationError
from app.domain.enums import ArtifactName, Operation, Operator, RollbackStatus, SpecStatus, ValueType
from app.domain.models import ChangeSpec, Mutation, Predicate, SchemaInput, SqlPack
from app.repositories.change_repository import ChangeRepository


def quote_identifier(identifier: str) -> str:
    if not identifier or "\x00" in identifier:
        raise DomainValidationError("INVALID_IDENTIFIER", "Invalid SQL identifier")
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def render_literal(value: Any, value_type: ValueType) -> str:
    if value_type in {ValueType.STRING, ValueType.TIMESTAMP}:
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"
    if value_type == ValueType.BOOLEAN:
        if not isinstance(value, bool):
            raise DomainValidationError("INVALID_LITERAL", "BOOLEAN value must be true or false")
        return "TRUE" if value else "FALSE"
    if value_type == ValueType.NUMBER:
        if isinstance(value, bool):
            raise DomainValidationError("INVALID_LITERAL", "BOOLEAN cannot be rendered as NUMBER")
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise DomainValidationError("INVALID_LITERAL", "Invalid numeric value") from exc
        if not number.is_finite():
            raise DomainValidationError("INVALID_LITERAL", "Numeric value must be finite")
        return format(number, "f")
    raise DomainValidationError("INVALID_LITERAL", f"Unsupported value type: {value_type}")


def render_predicate(predicate: Predicate) -> str:
    column = quote_identifier(predicate.column)
    operators = {
        Operator.EQ: "=",
        Operator.NEQ: "<>",
        Operator.LT: "<",
        Operator.LTE: "<=",
        Operator.GT: ">",
        Operator.GTE: ">=",
        Operator.IS_NULL: "IS NULL",
        Operator.IS_NOT_NULL: "IS NOT NULL",
    }
    operator = operators[predicate.operator]
    if predicate.operator in {Operator.IS_NULL, Operator.IS_NOT_NULL}:
        return f"{column} {operator}"
    return f"{column} {operator} {render_literal(predicate.value, predicate.value_type)}"


def _where_clause(spec: ChangeSpec) -> str:
    predicates = sorted(
        spec.predicates,
        key=lambda item: (item.column.lower(), item.operator.value, str(item.value)),
    )
    if not predicates:
        raise DomainValidationError("WHERE_REQUIRED", "At least one predicate is required")
    return " AND\n  ".join(render_predicate(predicate) for predicate in predicates)


def _where_clause_without_mutation_columns(spec: ChangeSpec) -> str:
    predicates = sorted(
        [p for p in spec.predicates if p.column.lower() not in {m.column.lower() for m in spec.mutations}],
        key=lambda item: (item.column.lower(), item.operator.value, str(item.value)),
    )
    if not predicates:
        raise DomainValidationError("WHERE_REQUIRED", "At least one predicate is required")
    return " AND\n  ".join(render_predicate(predicate) for predicate in predicates)


def _qualified_table(spec: ChangeSpec) -> str:
    return f"{quote_identifier(spec.schema)}.{quote_identifier(spec.target_table)}"


def _select_columns(spec: ChangeSpec) -> list[str]:
    ordered = [
        *spec.identity_key_columns,
        *(predicate.column for predicate in spec.predicates),
        *(mutation.column for mutation in spec.mutations),
    ]
    result: list[str] = []
    for column in ordered:
        if column.lower() not in {existing.lower() for existing in result}:
            result.append(column)
    return result


def _render_mutations(mutations: list[Mutation]) -> str:
    return ",\n  ".join(
        f"{quote_identifier(mutation.column)} = {render_literal(mutation.value, mutation.value_type)}"
        for mutation in sorted(mutations, key=lambda item: item.column.lower())
    )


def _render_rollback(spec: ChangeSpec) -> str:
    table = _qualified_table(spec)
    keys = spec.identity_key_columns
    if spec.operation == Operation.UPDATE:
        restore_columns = [mutation.column for mutation in spec.mutations]
        aliases = [*keys, *restore_columns]
        placeholders = [f"__{column}__" for column in aliases]
        assignments = ",\n  ".join(
            f"{quote_identifier(column)} = backup.{quote_identifier(column)}"
            for column in restore_columns
        )
        identity_join = " AND ".join(
            f"target.{quote_identifier(column)} = backup.{quote_identifier(column)}" for column in keys
        )
        return (
            "-- TEMPLATE: replace placeholder values with rows saved by backupSql.\n"
            f"UPDATE {table} AS target\n"
            f"SET {assignments}\n"
            f"FROM (VALUES ({', '.join(placeholders)})) AS backup"
            f"({', '.join(quote_identifier(column) for column in aliases)})\n"
            f"WHERE {identity_join};"
        )
    columns = _select_columns(spec)
    return (
        "-- TEMPLATE: insert the complete rows saved by backupSql.\n"
        f"INSERT INTO {table} ({', '.join(quote_identifier(column) for column in columns)})\n"
        f"VALUES ({', '.join(f'__{column}__' for column in columns)});"
    )


def generate_sql_pack(spec: ChangeSpec, schema_input: SchemaInput) -> SqlPack:
    if spec.status != SpecStatus.CONFIRMED:
        raise ConflictError("SPEC_NOT_CONFIRMED", "SQL Pack requires a CONFIRMED ChangeSpec")
    table_schema = next(
        (table for table in schema_input.tables if table.name.lower() == spec.target_table.lower()),
        None,
    )
    if table_schema is None:
        raise DomainValidationError("UNKNOWN_TARGET_TABLE", "Target table is not in the supplied schema")
    schema_columns = {column.name.lower() for column in table_schema.columns}
    selected_columns = _select_columns(spec)
    if any(column.lower() not in schema_columns for column in selected_columns):
        raise DomainValidationError("UNKNOWN_COLUMN", "ChangeSpec refers to an unknown column")

    table = _qualified_table(spec)
    where = _where_clause(spec)
    select_list = ", ".join(quote_identifier(column) for column in selected_columns)
    precheck = f"SELECT {select_list}\nFROM {table}\nWHERE {where};"
    backup = (
        "-- Save these rows outside the database before executing the change.\n"
        f"SELECT {select_list}\nFROM {table}\nWHERE {where};"
    )
    if spec.operation == Operation.UPDATE:
        execution = f"UPDATE {table}\nSET {_render_mutations(spec.mutations)}\nWHERE {where};"
        verification = _render_verification(spec, table)
    else:
        execution = f"DELETE FROM {table}\nWHERE {where};"
        verification = f"SELECT COUNT(*) AS remaining_rows\nFROM {table}\nWHERE {where};"

    return SqlPack(
        precheck_sql=precheck,
        backup_sql=backup,
        execution_sql=execution,
        verification_sql=verification,
        rollback_sql=_render_rollback(spec),
        rollback_status=RollbackStatus.TEMPLATE_REQUIRES_BACKUP_ROWS,
        spec_id=spec.spec_id,
        spec_version=spec.version,
        content_hash=spec.content_hash,
        revision=1,
        updated_at=datetime.now(timezone.utc),
    )


def _render_verification(spec: ChangeSpec, table: str) -> str:
    base_predicates = [p for p in spec.predicates if p.column.lower() not in {m.column.lower() for m in spec.mutations}]
    if not base_predicates:
        raise DomainValidationError("WHERE_REQUIRED", "At least one predicate is required")
    base_where = " AND\n  ".join(render_predicate(predicate) for predicate in sorted(base_predicates, key=lambda item: (item.column.lower(), item.operator.value, str(item.value))))
    postconditions = " AND\n  ".join(
        f"{quote_identifier(mutation.column)} = {render_literal(mutation.value, mutation.value_type)}"
        for mutation in sorted(spec.mutations, key=lambda item: item.column.lower())
    )
    return (
        f"SELECT {', '.join(quote_identifier(column) for column in spec.identity_key_columns)}\n"
        f"FROM {table}\nWHERE {base_where}\n  AND {postconditions};"
    )


def update_sql_artifact(
    repository: ChangeRepository,
    spec_id: str,
    artifact_name: ArtifactName,
    sql: str,
) -> SqlPack:
    pack = repository.get_sql_pack(spec_id)
    field_name = {
        ArtifactName.PRECHECK_SQL: "precheck_sql",
        ArtifactName.BACKUP_SQL: "backup_sql",
        ArtifactName.EXECUTION_SQL: "execution_sql",
        ArtifactName.VERIFICATION_SQL: "verification_sql",
        ArtifactName.ROLLBACK_SQL: "rollback_sql",
    }[artifact_name]
    updated = pack.model_copy(
        update={
            field_name: sql,
            "revision": pack.revision + 1,
            "updated_at": datetime.now(timezone.utc),
        }
    )
    repository.save_sql_pack(updated)
    repository.mark_review_stale(spec_id)
    return updated
