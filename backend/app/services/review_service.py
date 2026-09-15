from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.domain.enums import (
    ArtifactName,
    CheckStatus,
    Operation,
    Operator,
    RiskLevel,
    RollbackStatus,
    Severity,
    SpecStatus,
    Verdict,
)
from app.domain.models import (
    ChangeSpec,
    Predicate,
    ReviewCheck,
    ReviewEvidence,
    ReviewResult,
    SchemaInput,
    SqlPack,
)
from app.services.sql_analyzer import analyze_sql, rollback_uses_identity_keys


DISCLAIMER = "정적 검토 통과 여부이며, 실제 실행 승인 또는 무사 실행을 보장하지 않습니다."


def _value_key(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    try:
        if not isinstance(value, str) or value.replace(".", "", 1).isdigit():
            return format(Decimal(str(value)).normalize(), "f")
    except Exception:
        pass
    return str(value)


def _predicate_key(predicate: Predicate) -> tuple[str, str, str]:
    return (predicate.column.lower(), predicate.operator.value, _value_key(predicate.value))


def _predicate_label(key: tuple[str, str, str]) -> str:
    operators = {
        Operator.EQ.value: "=",
        Operator.NEQ.value: "<>",
        Operator.LT.value: "<",
        Operator.LTE.value: "<=",
        Operator.GT.value: ">",
        Operator.GTE.value: ">=",
        Operator.IS_NULL.value: "IS NULL",
        Operator.IS_NOT_NULL.value: "IS NOT NULL",
    }
    suffix = "" if key[1] in {Operator.IS_NULL.value, Operator.IS_NOT_NULL.value} else f" {key[2]}"
    return f"{key[0]} {operators[key[1]]}{suffix}"


def _check(
    rule_id: str,
    status: CheckStatus,
    message: str,
    *,
    category: str,
    severity: Severity,
    expected: Any = None,
    actual: Any = None,
    spec_field: str | None = None,
    sql_artifact: ArtifactName | None = None,
    sql_location: str | None = None,
    suggested_fix: str | None = None,
) -> ReviewCheck:
    return ReviewCheck(
        rule_id=rule_id,
        category=category,
        status=status,
        severity=severity,
        message=message,
        expected=expected,
        actual=actual,
        spec_field=spec_field,
        sql_artifact=sql_artifact,
        sql_location=sql_location,
        suggested_fix=suggested_fix,
    )


def _risk_level(spec: ChangeSpec) -> RiskLevel:
    if spec.operation == Operation.DELETE:
        return RiskLevel.HIGH
    if spec.expected_row_count is not None and spec.expected_row_count > 1_000:
        return RiskLevel.HIGH
    predicate_columns = {predicate.column.lower() for predicate in spec.predicates}
    identity_columns = {column.lower() for column in spec.identity_key_columns}
    if spec.expected_row_count is None or spec.expected_row_count > 100:
        return RiskLevel.MEDIUM
    if not identity_columns.issubset(predicate_columns):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def review_change(
    spec: ChangeSpec,
    schema_input: SchemaInput,
    sql_pack: SqlPack,
    evidence: ReviewEvidence,
) -> ReviewResult:
    checks: list[ReviewCheck] = []
    analysis = analyze_sql(sql_pack.execution_sql)

    if analysis.parse_error or analysis.operation not in {Operation.UPDATE, Operation.DELETE}:
        checks.append(
            _check(
                "B007",
                CheckStatus.FAIL,
                "executionSql could not be parsed as a supported UPDATE or DELETE statement.",
                category="syntax_and_scope",
                severity=Severity.CRITICAL,
                expected=spec.operation.value,
                actual=analysis.parse_error or str(analysis.operation),
                sql_artifact=ArtifactName.EXECUTION_SQL,
                suggested_fix="Use one PostgreSQL UPDATE or DELETE statement within the supported scope.",
            )
        )
    else:
        checks.append(
            _check(
                "B007",
                CheckStatus.PASS,
                "executionSql is a supported PostgreSQL statement.",
                category="syntax_and_scope",
                severity=Severity.INFO,
                expected=spec.operation.value,
                actual=analysis.operation.value,
                sql_artifact=ArtifactName.EXECUTION_SQL,
            )
        )

    if analysis.operation in {Operation.UPDATE, Operation.DELETE} and not analysis.has_where:
        checks.append(
            _check(
                "B001",
                CheckStatus.FAIL,
                "UPDATE or DELETE without WHERE can affect every row in the table.",
                category="target_scope",
                severity=Severity.CRITICAL,
                expected="WHERE clause",
                actual="missing",
                spec_field="predicates",
                sql_artifact=ArtifactName.EXECUTION_SQL,
                suggested_fix="Restore every predicate from the confirmed ChangeSpec.",
            )
        )
    else:
        checks.append(
            _check(
                "B001",
                CheckStatus.PASS,
                "executionSql contains a WHERE clause.",
                category="target_scope",
                severity=Severity.INFO,
                sql_artifact=ArtifactName.EXECUTION_SQL,
            )
        )

    table_matches = analysis.target_table == spec.target_table.lower()
    checks.append(
        _check(
            "B002",
            CheckStatus.PASS if table_matches else CheckStatus.FAIL,
            "executionSql targets the confirmed table." if table_matches else "executionSql targets a different table.",
            category="target_table",
            severity=Severity.INFO if table_matches else Severity.CRITICAL,
            expected=spec.target_table,
            actual=analysis.target_table or "unknown",
            spec_field="targetTable",
            sql_artifact=ArtifactName.EXECUTION_SQL,
            suggested_fix=None if table_matches else "Change the statement to the table in the confirmed ChangeSpec.",
        )
    )

    expected_predicates = {_predicate_key(predicate) for predicate in spec.predicates}
    actual_predicates = {predicate.key for predicate in analysis.predicates}
    missing_predicates = sorted(expected_predicates - actual_predicates)
    extra_predicates = sorted(actual_predicates - expected_predicates)
    if missing_predicates:
        for missing in missing_predicates:
            label = _predicate_label(missing)
            checks.append(
                _check(
                    "B003",
                    CheckStatus.FAIL,
                    f"The confirmed condition '{label}' is missing, so unintended rows may be changed.",
                    category="predicate_consistency",
                    severity=Severity.CRITICAL,
                    expected=label,
                    actual="missing",
                    spec_field=f"predicates[{missing[0]}]",
                    sql_artifact=ArtifactName.EXECUTION_SQL,
                    sql_location="WHERE",
                    suggested_fix=f"Add '{label}' back to the executionSql WHERE clause.",
                )
            )
    else:
        checks.append(
            _check(
                "B003",
                CheckStatus.PASS,
                "All confirmed predicates are present in executionSql.",
                category="predicate_consistency",
                severity=Severity.INFO,
                sql_artifact=ArtifactName.EXECUTION_SQL,
            )
        )
    if extra_predicates:
        for extra in extra_predicates:
            label = _predicate_label(extra)
            checks.append(
                _check(
                    "B004",
                    CheckStatus.FAIL,
                    f"executionSql contains an unconfirmed target condition: '{label}'.",
                    category="predicate_consistency",
                    severity=Severity.CRITICAL,
                    expected="no additional predicate",
                    actual=label,
                    spec_field="predicates",
                    sql_artifact=ArtifactName.EXECUTION_SQL,
                    sql_location="WHERE",
                    suggested_fix="Remove the condition or confirm it as a new ChangeSpec version.",
                )
            )
    else:
        checks.append(
            _check(
                "B004",
                CheckStatus.PASS,
                "executionSql contains no additional target predicate.",
                category="predicate_consistency",
                severity=Severity.INFO,
                sql_artifact=ArtifactName.EXECUTION_SQL,
            )
        )

    expected_mutations = {mutation.column.lower(): _value_key(mutation.value) for mutation in spec.mutations}
    actual_mutations = {column: _value_key(value) for column, value in analysis.mutations.items()}
    mutation_matches = analysis.operation == spec.operation and expected_mutations == actual_mutations
    checks.append(
        _check(
            "B005",
            CheckStatus.PASS if mutation_matches else CheckStatus.FAIL,
            "Changed columns and values match the ChangeSpec."
            if mutation_matches
            else "The operation, changed columns, or values differ from the ChangeSpec.",
            category="mutation_consistency",
            severity=Severity.INFO if mutation_matches else Severity.CRITICAL,
            expected={"operation": spec.operation.value, "mutations": expected_mutations},
            actual={"operation": analysis.operation.value if analysis.operation else None, "mutations": actual_mutations},
            spec_field="operation/mutations",
            sql_artifact=ArtifactName.EXECUTION_SQL,
            suggested_fix=None if mutation_matches else "Restore the confirmed operation, columns, and values.",
        )
    )

    table_schema = next(
        (table for table in schema_input.tables if table.name.lower() == spec.target_table.lower()),
        None,
    )
    known_columns = {column.name.lower() for column in table_schema.columns} if table_schema else set()
    unknown_columns = sorted(analysis.referenced_columns - known_columns)
    schema_matches = table_schema is not None and table_matches and not unknown_columns
    checks.append(
        _check(
            "B006",
            CheckStatus.PASS if schema_matches else CheckStatus.FAIL,
            "All referenced tables and columns exist in the supplied schema."
            if schema_matches
            else "executionSql refers to a table or column outside the supplied schema.",
            category="schema",
            severity=Severity.INFO if schema_matches else Severity.CRITICAL,
            expected={"table": spec.target_table, "knownColumns": sorted(known_columns)},
            actual={"table": analysis.target_table, "unknownColumns": unknown_columns},
            sql_artifact=ArtifactName.EXECUTION_SQL,
            suggested_fix=None if schema_matches else "Use only identifiers from the supplied schema.",
        )
    )

    rollback_safe = rollback_uses_identity_keys(
        sql_pack.rollback_sql,
        spec.operation,
        spec.identity_key_columns,
    )
    checks.append(
        _check(
            "B008",
            CheckStatus.PASS if rollback_safe else CheckStatus.FAIL,
            "rollbackSql uses the confirmed identity key."
            if rollback_safe
            else "rollbackSql does not safely identify the same rows.",
            category="rollback",
            severity=Severity.INFO if rollback_safe else Severity.CRITICAL,
            expected=spec.identity_key_columns,
            actual="matched" if rollback_safe else "missing or different",
            spec_field="identityKeyColumns",
            sql_artifact=ArtifactName.ROLLBACK_SQL,
            suggested_fix=None if rollback_safe else "Join or restore rows using every confirmed identity key column.",
        )
    )

    checks.append(
        _check(
            "R001",
            CheckStatus.PASS if spec.expected_row_count is not None else CheckStatus.REVIEW,
            "Expected row count is available."
            if spec.expected_row_count is not None
            else "Expected row count has not been recorded.",
            category="evidence",
            severity=Severity.INFO if spec.expected_row_count is not None else Severity.WARNING,
            expected="non-null expectedRowCount",
            actual=spec.expected_row_count,
            spec_field="expectedRowCount",
            suggested_fix=None if spec.expected_row_count is not None else "Record the expected affected row count after precheck.",
        )
    )
    rollback_complete = sql_pack.rollback_status == RollbackStatus.COMPLETE
    checks.append(
        _check(
            "R002",
            CheckStatus.PASS if rollback_complete else CheckStatus.REVIEW,
            "Rollback is complete."
            if rollback_complete
            else "Rollback is a template that still requires saved backup rows.",
            category="rollback",
            severity=Severity.INFO if rollback_complete else Severity.WARNING,
            expected=RollbackStatus.COMPLETE.value,
            actual=sql_pack.rollback_status.value,
            sql_artifact=ArtifactName.ROLLBACK_SQL,
            suggested_fix=None if rollback_complete else "Save backupSql results and complete the rollback values before execution.",
        )
    )
    checks.append(
        _check(
            "R003",
            CheckStatus.PASS if evidence.complete else CheckStatus.REVIEW,
            "Execution plan, index, lock, and concurrency evidence is complete."
            if evidence.complete
            else "Execution plan, index, lock, or concurrency evidence is incomplete.",
            category="operational_evidence",
            severity=Severity.INFO if evidence.complete else Severity.WARNING,
            expected={"allEvidenceReviewed": True},
            actual=evidence.model_dump(by_alias=True),
            suggested_fix=None if evidence.complete else "Review the plan, indexes, lock scope, and concurrent traffic before execution.",
        )
    )
    checks.append(
        _check(
            "R004",
            CheckStatus.REVIEW if analysis.has_complex_condition else CheckStatus.PASS,
            "The condition is too complex for the current equivalence checker."
            if analysis.has_complex_condition
            else "The WHERE clause uses supported simple AND predicates.",
            category="semantic_equivalence",
            severity=Severity.WARNING if analysis.has_complex_condition else Severity.INFO,
            sql_artifact=ArtifactName.EXECUTION_SQL,
            suggested_fix="Simplify the condition or request manual review."
            if analysis.has_complex_condition
            else None,
        )
    )

    if spec.status != SpecStatus.CONFIRMED or (
        sql_pack.spec_id != spec.spec_id
        or sql_pack.spec_version != spec.version
        or sql_pack.content_hash != spec.content_hash
    ):
        checks.append(
            _check(
                "M001",
                CheckStatus.FAIL,
                "The SQL Pack does not reference the current confirmed ChangeSpec.",
                category="metadata",
                severity=Severity.CRITICAL,
                expected={"specId": spec.spec_id, "version": spec.version, "contentHash": spec.content_hash},
                actual={
                    "specId": sql_pack.spec_id,
                    "version": sql_pack.spec_version,
                    "contentHash": sql_pack.content_hash,
                },
                suggested_fix="Regenerate the SQL Pack from the current confirmed ChangeSpec.",
            )
        )

    if any(check.status == CheckStatus.FAIL for check in checks):
        verdict = Verdict.BLOCK
    elif any(check.status == CheckStatus.REVIEW for check in checks):
        verdict = Verdict.REVIEW
    else:
        verdict = Verdict.READY
    return ReviewResult(
        spec_id=spec.spec_id,
        spec_version=spec.version,
        content_hash=spec.content_hash,
        sql_pack_revision=sql_pack.revision,
        verdict=verdict,
        risk_level=_risk_level(spec),
        is_stale=False,
        checks=checks,
        disclaimer=DISCLAIMER,
        reviewed_at=datetime.now(timezone.utc),
    )
