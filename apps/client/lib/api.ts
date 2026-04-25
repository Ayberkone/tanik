// Thin client for the TANIK inference service. The contract lives in
// docs/api-contract.md — every function below mirrors a section there.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export type Health = {
  status: 'ok'
  iris_engine: string
  version: string
}

export type ApiError = {
  request_id: string
  error_code:
    | 'INVALID_IMAGE'
    | 'SUBJECT_NOT_FOUND'
    | 'PAYLOAD_TOO_LARGE'
    | 'UNSUPPORTED_MEDIA_TYPE'
    | 'VALIDATION_ERROR'
    | 'PIPELINE_FAILURE'
    | 'PAD_FAILURE'
  message: string
  details?: unknown
}

export class TanikApiError extends Error {
  constructor(public readonly body: ApiError, public readonly status: number) {
    super(body.message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init)
  const text = await res.text()
  const body = text ? JSON.parse(text) : null
  if (!res.ok) {
    throw new TanikApiError(body as ApiError, res.status)
  }
  return body as T
}

export const api = {
  apiBase: API_BASE,
  health: () => request<Health>('/api/v1/health'),
}
