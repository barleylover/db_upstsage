export type DBMS =
  | 'POSTGRESQL'
  | 'MYSQL'
  | 'MARIADB'
  | 'ORACLE'
  | 'SQL_SERVER'
  | 'SQLITE'
  | 'BIGQUERY'
  | 'SNOWFLAKE'

export type Operation = 'UPDATE' | 'DELETE'
export type SpecStatus = 'DRAFT' | 'CONFIRMED' | 'SUPERSEDED'
export type Verdict = 'READY' | 'REVIEW' | 'BLOCK'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type CheckStatus = 'PASS' | 'REVIEW' | 'FAIL'
export type Severity = 'INFO' | 'WARNING' | 'CRITICAL'
export type ValueType = 'STRING' | 'NUMBER' | 'BOOLEAN' | 'TIMESTAMP'
export type RollbackStatus = 'COMPLETE' | 'TEMPLATE_REQUIRES_BACKUP_ROWS'

export interface ColumnSchema {
  name: string
  data_type: string
  nullable: boolean
}

export interface TableSchema {
  name: string
  columns: ColumnSchema[]
  primary_key_columns: string[]
}

export interface SchemaInput {
  database: string
  schema: string
  tables: TableSchema[]
}

export interface Predicate {
  column: string
  operator: string
  value: unknown
  value_type: ValueType
}

export interface Mutation {
  column: string
  value: unknown
  value_type: ValueType
}

export interface ChangeSpec {
  spec_id: string
  version: number
  status: SpecStatus
  content_hash: string
  original_request: string
  database: string
  schema: string
  target_table: string
  identity_key_columns: string[]
  operation: Operation
  predicates: Predicate[]
  mutations: Mutation[]
  expected_row_count: number | null
  assumptions: string[]
  unresolved_questions: string[]
  created_at: string
  confirmed_at: string | null
}

export interface SqlPack {
  precheck_sql: string
  backup_sql: string
  execution_sql: string
  verification_sql: string
  rollback_sql: string
  rollback_status: RollbackStatus
  spec_id: string
  spec_version: number
  content_hash: string
  revision: number
  updated_at: string
}

export interface ReviewEvidence {
  execution_plan_reviewed: boolean
  index_reviewed: boolean
  lock_reviewed: boolean
  concurrency_reviewed: boolean
}

export interface ReviewCheck {
  rule_id: string
  category: string
  status: CheckStatus
  severity: Severity
  message: string
  expected: unknown
  actual: unknown
  spec_field: string | null
  sql_artifact: string | null
  sql_location: string | null
  suggested_fix: string | null
}

export interface ReviewResult {
  spec_id: string
  spec_version: number
  content_hash: string
  sql_pack_revision: number
  verdict: Verdict
  risk_level: RiskLevel
  is_stale: boolean
  checks: ReviewCheck[]
  disclaimer: string
  reviewed_at: string
}

export interface DocumentTemplate {
  id: string
  name: string
  itemCount: number
  isDefault: boolean
  items: DocumentTemplateItem[]
}

export interface DocumentTemplateItem {
  name: string
  source: string
  value?: string
}

export interface SchemaCatalogEntry {
  id: string
  name: string
  dbms: DBMS
  database: string
  schema: string
  tableCount: number
  columnCount: number
  used: boolean
}

export interface TemplateExportPackage {
  spec?: { version: number }
  sql?: { revision: number }
  impact?: { risk: RiskLevel }
  evidence?: { checked: number; total: number }
  rollback?: { status: RollbackStatus }
  document?: { name: string }
  verdict?: { status: Verdict }
}
