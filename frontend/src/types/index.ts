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
