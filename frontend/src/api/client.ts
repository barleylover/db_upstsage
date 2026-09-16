const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')

const API_PREFIX = '/api/v1'

function apiUrl(path: string) {
  const normalized = path.startsWith('/') ? path : `/${path}`
  // `/health` lives at the server root; every other endpoint is under /api/v1.
  if (normalized === '/health') return `${BASE}${normalized}`
  return `${BASE}${API_PREFIX}${normalized}`
}

export class ApiError extends Error {
  constructor(message: string, public status: number, public code: string | null = null, public details: unknown = null) {
    super(message)
    this.name = 'ApiError'
  }

  static fromResponse(body: unknown, status: number): ApiError {
    if (body && typeof body === 'object') {
      const obj = body as Record<string, unknown>
      const message =
        typeof obj.message === 'string'
          ? obj.message
          : typeof obj.detail === 'string'
            ? obj.detail
            : `HTTP ${status}`
      const code = typeof obj.code === 'string' ? obj.code : null
      const details = obj.details ?? null
      return new ApiError(message, status, code, details)
    }
    return new ApiError(String(body), status)
  }
}

async function request<T>(url: string, body?: unknown, init?: RequestInit): Promise<T> {
  const method = init?.method || (body !== undefined ? 'POST' : 'GET')
  const res = await fetch(apiUrl(url), {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    let body: unknown = {}
    try {
      body = text ? JSON.parse(text) : {}
    } catch {
      body = text
    }
    throw ApiError.fromResponse(body, res.status)
  }
  const text = await res.text()
  if (!text) return {} as T
  try {
    return JSON.parse(text) as T
  } catch {
    throw new ApiError('Invalid JSON response', res.status)
  }
}

export const health = () => request<{ status: string; service: string; version: string }>('/health')

export const interpretRequest = (
  originalRequest: string,
  schemaInput: { database: string; schema: string; tables: unknown[] },
) => request<ChangeSpec>('/change-specs/interpret', { originalRequest: originalRequest, schemaInput })

export const confirmSpec = (
  specId: string,
  payload: {
    environment?: string
    database?: string
    schema?: string
    targetTable?: string
    identityKeyColumns?: string[]
    operation?: string
    predicates?: Array<{ column: string; operator: string; value: unknown; valueType: string }>
    mutations?: Array<{ column: string; value: unknown; valueType: string }>
    expectedRowCount?: number | null
    assumptions?: string[]
    unresolvedQuestions?: string[]
  },
) => request<ChangeSpec>(`/change-specs/${specId}/confirm`, payload)

export const getSpec = (specId: string) => request<ChangeSpec>(`/change-specs/${specId}`)

export const createSqlPack = (specId: string) => request<SqlPack>(`/change-specs/${specId}/sql-pack`, undefined, { method: 'POST' })

export const updateSqlArtifact = (
  specId: string,
  artifactName: string,
  sql: string,
) => request<SqlPack>(`/change-specs/${specId}/sql-pack/${artifactName}`, { sql }, { method: 'PUT' })

export const reviewSpec = (
  specId: string,
  evidence: {
    executionPlanReviewed: boolean
    indexReviewed: boolean
    lockReviewed: boolean
    concurrencyReviewed: boolean
  },
) => request<ReviewResult>(`/change-specs/${specId}/review`, { evidence })

export const generateChangeDocument = (
  specId: string,
  templateName?: string,
  fields?: Array<{ key: string; label: string; required: boolean }>,
) =>
  request<ChangeDocument>(`/change-specs/${specId}/change-document`, { templateName, fields })

export interface ChangeSpec {
  specId: string
  version: number
  status: string
  contentHash: string
  originalRequest: string
  dbms: string
  environment: string
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

export interface SqlPack {
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

export interface ReviewResult {
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

export interface ChangeDocument {
  specId: string
  specVersion: number
  contentHash: string
  sqlPackRevision: number
  templateName: string
  fields: Array<{
    key: string
    label: string
    value: unknown
    required: boolean
    source: string
  }>
  generatedAt: string
}
