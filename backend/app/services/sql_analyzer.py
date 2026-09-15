from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from app.domain.enums import Operation, Operator


@dataclass(frozen=True, slots=True)
class CanonicalPredicate:
    column: str
    operator: Operator
    value: Any | None
    sql: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.column.lower(), self.operator.value, _value_key(self.value))


@dataclass(frozen=True, slots=True)
class SqlAnalysis:
    sql: str
    operation: Operation | None = None
    target_table: str | None = None
    has_where: bool = False
    predicates: tuple[CanonicalPredicate, ...] = ()
    mutations: dict[str, Any] = field(default_factory=dict)
    referenced_columns: frozenset[str] = frozenset()
    has_complex_condition: bool = False
    parse_error: str | None = None


def _value_key(value: Any | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def _unwrap(node: exp.Expression) -> exp.Expression:
    while isinstance(node, (exp.Paren, exp.Cast)):
        node = node.this
    return node


def _literal_value(node: exp.Expression) -> Any:
    node = _unwrap(node)
    if isinstance(node, exp.Literal):
        if node.is_string:
            return node.this
        try:
            return Decimal(node.this)
        except InvalidOperation:
            return node.this
    if isinstance(node, exp.Boolean):
        return str(node.this).lower() == "true"
    if isinstance(node, exp.Null):
        return None
    if isinstance(node, exp.Neg):
        value = _literal_value(node.this)
        return -value if isinstance(value, Decimal) else f"-{value}"
    return node.sql(dialect="postgres", normalize=True)


def _flatten_and(node: exp.Expression) -> list[exp.Expression]:
    node = _unwrap(node)
    if isinstance(node, exp.And):
        return [*_flatten_and(node.left), *_flatten_and(node.right)]
    return [node]


def _is_simple_not_null(node: exp.Expression) -> bool:
    return (
        isinstance(node, exp.Not)
        and isinstance(_unwrap(node.this), exp.Is)
        and isinstance(_unwrap(node.this).expression, exp.Null)
    )


def _contains_complex_condition(node: exp.Expression) -> bool:
    for item in node.walk():
        if isinstance(item, (exp.Or, exp.Subquery, exp.Select, exp.Exists, exp.Join)):
            return True
        if isinstance(item, exp.Not) and not _is_simple_not_null(item):
            return True
        if isinstance(item, exp.Func):
            return True
    return False


def _comparison_to_predicate(node: exp.Expression) -> CanonicalPredicate | None:
    node = _unwrap(node)
    if _is_simple_not_null(node):
        is_expression = _unwrap(node.this)
        column = _unwrap(is_expression.this)
        if isinstance(column, exp.Column):
            return CanonicalPredicate(
                column=column.name.lower(),
                operator=Operator.IS_NOT_NULL,
                value=None,
                sql=node.sql(dialect="postgres"),
            )
        return None
    if isinstance(node, exp.Is) and isinstance(_unwrap(node.expression), exp.Null):
        column = _unwrap(node.this)
        if isinstance(column, exp.Column):
            return CanonicalPredicate(
                column=column.name.lower(),
                operator=Operator.IS_NULL,
                value=None,
                sql=node.sql(dialect="postgres"),
            )
        return None
    operation_map: list[tuple[type[exp.Expression], Operator]] = [
        (exp.EQ, Operator.EQ),
        (exp.NEQ, Operator.NEQ),
        (exp.LT, Operator.LT),
        (exp.LTE, Operator.LTE),
        (exp.GT, Operator.GT),
        (exp.GTE, Operator.GTE),
    ]
    operator = next((value for kind, value in operation_map if isinstance(node, kind)), None)
    if operator is None:
        return None
    left = _unwrap(node.left)
    right = _unwrap(node.right)
    if isinstance(left, exp.Column):
        return CanonicalPredicate(
            column=left.name.lower(),
            operator=operator,
            value=_literal_value(right),
            sql=node.sql(dialect="postgres"),
        )
    return None


def analyze_sql(sql: str) -> SqlAnalysis:
    try:
        parsed = parse_one(sql, read="postgres")
    except (ParseError, ValueError) as exc:
        return SqlAnalysis(sql=sql, parse_error=str(exc))

    operation: Operation | None = None
    target_table: str | None = None
    mutations: dict[str, Any] = {}
    if isinstance(parsed, exp.Update):
        operation = Operation.UPDATE
        if isinstance(parsed.this, exp.Table):
            target_table = parsed.this.name.lower()
        for assignment in parsed.expressions:
            if isinstance(assignment, exp.EQ):
                column = _unwrap(assignment.left)
                if isinstance(column, exp.Column):
                    mutations[column.name.lower()] = _literal_value(assignment.right)
    elif isinstance(parsed, exp.Delete):
        operation = Operation.DELETE
        if isinstance(parsed.this, exp.Table):
            target_table = parsed.this.name.lower()

    where = parsed.args.get("where")
    where_expression = where.this if isinstance(where, exp.Where) else None
    predicates: list[CanonicalPredicate] = []
    complex_condition = False
    if where_expression is not None:
        complex_condition = _contains_complex_condition(where_expression)
        for item in _flatten_and(where_expression):
            predicate = _comparison_to_predicate(item)
            if predicate is None:
                complex_condition = True
            else:
                predicates.append(predicate)
    columns = frozenset(column.name.lower() for column in parsed.find_all(exp.Column))
    return SqlAnalysis(
        sql=sql,
        operation=operation,
        target_table=target_table,
        has_where=where_expression is not None,
        predicates=tuple(sorted(predicates, key=lambda item: item.key)),
        mutations=mutations,
        referenced_columns=columns,
        has_complex_condition=complex_condition,
    )


def rollback_uses_identity_keys(sql: str, operation: Operation, keys: list[str]) -> bool:
    try:
        parsed = parse_one(sql, read="postgres")
    except (ParseError, ValueError):
        return False
    expected = {key.lower() for key in keys}
    if operation == Operation.UPDATE and isinstance(parsed, exp.Update):
        where = parsed.args.get("where")
        if not isinstance(where, exp.Where):
            return False
        matched: set[str] = set()
        for equality in where.find_all(exp.EQ):
            left, right = _unwrap(equality.left), _unwrap(equality.right)
            if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                if left.name.lower() == right.name.lower() and left.name.lower() in expected:
                    matched.add(left.name.lower())
        return matched == expected
    if operation == Operation.DELETE and isinstance(parsed, exp.Insert):
        schema = parsed.this
        if isinstance(schema, exp.Schema):
            columns = {column.name.lower() for column in schema.expressions if isinstance(column, exp.Identifier)}
            return expected.issubset(columns)
    return False
