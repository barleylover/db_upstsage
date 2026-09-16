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

export interface ChangeSpec {
  specId: string
  version: number
  status: SpecStatus
  contentHash: string
  originalRequest: string
  database: string
  schema: string
  targetTable: string
  identityKeyColumns: string[]
  operation: Operation
  predicates: Array<{ column: string; operator: string; value: unknown; valueType: ValueType }>
  mutations: Array<{ column: string; value: unknown; valueType: ValueType }>
  expectedRowCount: number | null
  assumptions: string[]
  unresolvedQuestions: string[]
  createdAt: string
  confirmedAt: string | null
}

export interface ReviewResult {
  specId: string
  specVersion: number
  contentHash: string
  sqlPackRevision: number
  verdict: Verdict
  riskLevel: RiskLevel
  isStale: boolean
  checks: ReviewCheck[]
  disclaimer: string
  reviewedAt: string
}

export interface ReviewCheck {
  ruleId: string
  category: string
  status: CheckStatus
  severity: Severity
  message: string
  expected: unknown
  actual: unknown
  specField: string | null
  sqlArtifact: string | null
  sqlLocation: string | null
  suggestedFix: string | null
}
