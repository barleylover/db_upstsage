const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '') + '/api/v1'

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(url: string, body?: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...init,
    method: init?.method || (body !== undefined ? 'POST' : 'GET'),
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new ApiError(text || `HTTP ${res.status}`, res.status)
  }
  const text = await res.text()
  return text ? JSON.parse(text) : ({} as T)
}

export const health = () => request<{ status: string; service: string; version: string }>('/health')

export const interpretRequest = (
  original_request: string,
  schema_input: { database: string; schema: string; tables: unknown[] },
) =>
  request<InterpretChangeResponse>('/change-specs/interpret', { original_request, schema_input })

export const confirmSpec = (
  specId: string,
  payload: {
    environment?: string
    database?: string
    schema?: string
    target_table?: string
    identity_key_columns?: string[]
    operation?: string
    predicates?: Array<{ column: string; operator: string; value: unknown; value_type: string }>
    mutations?: Array<{ column: string; value: unknown; value_type: string }>
    expected_row_count?: number | null
    assumptions?: string[]
    unresolved_questions?: string[]
  },
) =>
  request<ConfirmSpecResponse>(`/change-specs/${specId}/confirm`, payload)

export const getSpec = (specId: string) =>
  request<GetSpecResponse>(`/change-specs/${specId}`)

export const createSqlPack = (specId: string) =>
  request<CreateSqlPackResponse>(`/change-specs/${specId}/sql-pack`, undefined, { method: 'POST' })

export const updateSqlArtifact = (
  specId: string,
  artifactName: string,
  sql: string,
) =>
  request<UpdateSqlArtifactResponse>(`/change-specs/${specId}/sql-pack/${artifactName}`, { sql }, { method: 'PUT' })

export const reviewSpec = (
  specId: string,
  evidence: {
    execution_plan_reviewed: boolean
    index_reviewed: boolean
    lock_reviewed: boolean
    concurrency_reviewed: boolean
  },
) =>
  request<ReviewSpecResponse>(`/change-specs/${specId}/review`, { evidence })

export const generateChangeDocument = (
  specId: string,
  templateId?: string,
) =>
  request<GenerateChangeDocumentResponse>(`/change-specs/${specId}/change-document`, { template_id: templateId })

export interface InterpretChangeResponse {
  specId: string
  version: number
  status: string
  contentHash: string
  originalRequest: string
  database: string
  schema: string
  targetTable: string
  identityKeyColumns: string[]
  operation: string
  predicates: Array<{ column: string; operator: string; value: unknown; valueType: string }>
  mutations: Array<{ column: string; value: unknown; valueType: string }>
  expectedRowCount: number | null
  assumptions: string[]
  unresolvedQuestions: string[]
  createdAt: string
  confirmedAt: string | null
}

export interface ConfirmSpecResponse {
  specId: string
  version: number
  status: string
  contentHash: string
  originalRequest: string
  database: string
  schema: string
  targetTable: string
  identityKeyColumns: string[]
  operation: string
  predicates: Array<{ column: string; operator: string; value: unknown; valueType: string }>
  mutations: Array<{ column: string; value: unknown; valueType: string }>
  expectedRowCount: number | null
  assumptions: string[]
  unresolvedQuestions: string[]
  createdAt: string
  confirmedAt: string | null
}

export interface GetSpecResponse {
  specId: string
  version: number
  status: string
  contentHash: string
  originalRequest: string
  database: string
  schema: string
  targetTable: string
  identityKeyColumns: string[]
  operation: string
  predicates: Array<{ column: string; operator: string; value: unknown; valueType: string }>
  mutations: Array<{ column: string; value: unknown; valueType: string }>
  expectedRowCount: number | null
  assumptions: string[]
  unresolvedQuestions: string[]
  createdAt: string
  confirmedAt: string | null
}

export interface CreateSqlPackResponse {
  precheckSql: string
  backupSql: string
  executionSql: string
  verificationSql: string
  rollbackSql: string
  rollbackStatus: string
  specId: string
  specVersion: number
  contentHash: string
  revision: number
  updatedAt: string
}

export interface UpdateSqlArtifactResponse {
  precheckSql: string
  backupSql: string
  executionSql: string
  verificationSql: string
  rollbackSql: string
  rollbackStatus: string
  specId: string
  specVersion: number
  contentHash: string
  revision: number
  updatedAt: string
}

export interface ReviewSpecResponse {
  specId: string
  specVersion: number
  contentHash: string
  sqlPackRevision: number
  verdict: string
  riskLevel: string
  isStale: boolean
  checks: Array<{
    ruleId: string
    category: string
    status: string
    severity: string
    message: string
    expected: unknown
    actual: unknown
    specField: string | null
    sqlArtifact: string | null
    sqlLocation: string | null
    suggestedFix: string | null
  }>
  disclaimer: string
  reviewedAt: string
}

export interface GenerateChangeDocumentResponse {
  document: string
  templateId: string
  specId: string
  specVersion: number
  generatedAt: string
}
