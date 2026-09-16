const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

export const interpretRequest = (original_request: string, schema_input: { database: string; schema: string; tables: unknown[] }) =>
  request('/change-specs/interpret', { original_request, schema_input })

export const confirmSpec = (specId: string, payload: Record<string, unknown>) =>
  request(`/change-specs/${specId}/confirm`, payload)

export const getSpec = (specId: string) =>
  request(`/change-specs/${specId}`)

export const createSqlPack = (specId: string) =>
  request(`/change-specs/${specId}/sql-pack`)

export const updateSqlArtifact = (specId: string, artifactName: string, sql: string) =>
  request(`/change-specs/${specId}/sql-pack/${artifactName}`, { sql }, { method: 'PUT' })

export const reviewSpec = (
  specId: string,
  evidence: {
    execution_plan_reviewed: boolean
    index_reviewed: boolean
    lock_reviewed: boolean
    concurrency_reviewed: boolean
  },
) =>
  request(`/change-specs/${specId}/review`, { evidence })
