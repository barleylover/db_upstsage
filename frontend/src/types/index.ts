export type DBMS = 
  | 'POSTGRESQL'
  | 'MYSQL'
  | 'MARIADB'
  | 'ORACLE'
  | 'SQL_SERVER'
  | 'SQLITE'
  | 'BIGQUERY'
  | 'SNOWFLAKE'

export type ValueType = 'STRING' | 'NUMBER' | 'BOOLEAN' | 'TIMESTAMP'

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

export interface SchemaCatalogEntry {
  id: string
  name: string
  dbms: DBMS
  database: string
  schema: string
  tables: TableSchema[]
  updatedAt: string
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
