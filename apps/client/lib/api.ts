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

export type EnrollPayload = {
  image: Blob
  display_name?: string
  eye_side?: 'left' | 'right'
}

export type EnrollResult = {
  request_id: string
  subject_id: string
  display_name: string | null
  eye_side: 'left' | 'right'
  enrolled_at: string
  modality: 'iris'
  template_version: string
}

export type VerifyPayload = {
  image: Blob
  subject_id: string
  eye_side?: 'left' | 'right'
}

export type VerifyResult = {
  request_id: string
  subject_id: string
  modality: 'iris'
  matched: boolean
  hamming_distance: number
  threshold: number
  decision_at: string
}

function buildEnrollForm(p: EnrollPayload): FormData {
  const fd = new FormData()
  fd.append('image', p.image, 'capture.png')
  if (p.display_name) fd.append('display_name', p.display_name)
  fd.append('eye_side', p.eye_side ?? 'left')
  return fd
}

function buildVerifyForm(p: VerifyPayload): FormData {
  const fd = new FormData()
  fd.append('image', p.image, 'capture.png')
  fd.append('subject_id', p.subject_id)
  if (p.eye_side) fd.append('eye_side', p.eye_side)
  return fd
}

export const api = {
  apiBase: API_BASE,
  health: () => request<Health>('/api/v1/health'),
  enrollIris: (p: EnrollPayload) =>
    request<EnrollResult>('/api/v1/iris/enroll', { method: 'POST', body: buildEnrollForm(p) }),
  verifyIris: (p: VerifyPayload) =>
    request<VerifyResult>('/api/v1/iris/verify', { method: 'POST', body: buildVerifyForm(p) }),
}
