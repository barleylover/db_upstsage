from enum import Enum


class DBMS(str, Enum):
    POSTGRESQL = "POSTGRESQL"


class Operation(str, Enum):
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SpecStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"


class Operator(str, Enum):
    EQ = "EQ"
    NEQ = "NEQ"
    LT = "LT"
    LTE = "LTE"
    GT = "GT"
    GTE = "GTE"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"


class ValueType(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"


class RollbackStatus(str, Enum):
    COMPLETE = "COMPLETE"
    TEMPLATE_REQUIRES_BACKUP_ROWS = "TEMPLATE_REQUIRES_BACKUP_ROWS"


class Verdict(str, Enum):
    READY = "READY"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CheckStatus(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ArtifactName(str, Enum):
    PRECHECK_SQL = "precheckSql"
    BACKUP_SQL = "backupSql"
    EXECUTION_SQL = "executionSql"
    VERIFICATION_SQL = "verificationSql"
    ROLLBACK_SQL = "rollbackSql"
