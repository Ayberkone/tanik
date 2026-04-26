// Thin client for the TANIK inference service. The contract lives in
// docs/api-contract.md — every function below mirrors a section there.

// NEXT_PUBLIC_API_BASE_URL is baked into the browser bundle at build time —
// it MUST be the URL the user's browser can reach (e.g. https://api.example.com).
//
// INTERNAL_API_BASE_URL (server-only, no NEXT_PUBLIC_ prefix) overrides the
// URL for SSR / server-action fetches. In Docker Compose this lets the Next
// container call http://inference:8000 over the internal bridge network
// while the browser bundle still uses the host-routable URL. If unset on
// the server, falls back to the public URL.
const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const INTERNAL_BASE =
  typeof window === 'undefined' ? process.env.INTERNAL_API_BASE_URL ?? PUBLIC_BASE : PUBLIC_BASE

const API_BASE = INTERNAL_BASE

export type Health = {
  status: 'ok'
  iris_engine: string
  fingerprint_engine: string
  calibration_status: 'placeholder' | 'calibrated'
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

// Per-operation timeouts. Render's free tier sleeps after 15 min of
// inactivity and cold-starts in ~30 s, on top of which the iris pipeline
// adds 3-5 s of CPU work. So enroll/verify use 60 s; health is supposed
// to be cheap so it gets 15 s (long enough to forgive a one-off cold
// start, short enough that a genuinely-down backend doesn't block the
// home page render forever).
const TIMEOUT_HEALTH_MS = 15_000
const TIMEOUT_PIPELINE_MS = 60_000

type RequestOpts = RequestInit & { timeoutMs?: number }

async function request<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { timeoutMs = TIMEOUT_PIPELINE_MS, signal: callerSignal, ...init } = opts
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort(), timeoutMs)
  // If the caller passed their own signal (e.g. React StrictMode unmounts), abort our
  // request when theirs fires too.
  const onCallerAbort = () => ctl.abort()
  callerSignal?.addEventListener('abort', onCallerAbort)
  try {
    const res = await fetch(`${API_BASE}${path}`, { ...init, signal: ctl.signal })
    const text = await res.text()
    const body = text ? JSON.parse(text) : null
    if (!res.ok) {
      throw new TanikApiError(body as ApiError, res.status)
    }
    return body as T
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error(
        `Request timed out after ${Math.round(timeoutMs / 1000)} s. ` +
          'The backend may be cold-starting (Render free tier sleeps after ' +
          '15 min of inactivity and takes ~30 s to wake up). Try again in a moment.',
      )
    }
    throw err
  } finally {
    clearTimeout(timer)
    callerSignal?.removeEventListener('abort', onCallerAbort)
  }
}

// ---- Iris ----------------------------------------------------------------

export type EyeSide = 'left' | 'right'

export type IrisEnrollPayload = {
  image: Blob
  display_name?: string
  eye_side?: EyeSide
}

export type IrisEnrollResult = {
  request_id: string
  subject_id: string
  display_name: string | null
  eye_side: EyeSide
  enrolled_at: string
  modality: 'iris'
  template_version: string
}

export type IrisVerifyPayload = {
  image: Blob
  subject_id: string
  eye_side?: EyeSide
}

export type IrisVerifyResult = {
  request_id: string
  subject_id: string
  modality: 'iris'
  matched: boolean
  hamming_distance: number
  threshold: number
  decision_at: string
}

// ---- Fingerprint ---------------------------------------------------------

export const FINGER_POSITIONS = [
  'right_thumb',
  'right_index',
  'right_middle',
  'right_ring',
  'right_little',
  'left_thumb',
  'left_index',
  'left_middle',
  'left_ring',
  'left_little',
] as const
export type FingerPosition = (typeof FINGER_POSITIONS)[number]

export type FingerprintEnrollPayload = {
  image: Blob
  display_name?: string
  finger_position?: FingerPosition
}

export type FingerprintEnrollResult = {
  request_id: string
  subject_id: string
  display_name: string | null
  finger_position: FingerPosition
  enrolled_at: string
  modality: 'fingerprint'
  template_version: string
}

export type FingerprintVerifyPayload = {
  image: Blob
  subject_id: string
  finger_position?: FingerPosition
}

export type FingerprintVerifyResult = {
  request_id: string
  subject_id: string
  modality: 'fingerprint'
  matched: boolean
  similarity_score: number
  threshold: number
  decision_at: string
}

// ---- Discriminated unions ------------------------------------------------

export type EnrollResult = IrisEnrollResult | FingerprintEnrollResult
export type VerifyResult = IrisVerifyResult | FingerprintVerifyResult

// Backwards-compat aliases — the original iris types were exported under
// these names. Pages that already imported them keep working.
export type EnrollPayload = IrisEnrollPayload
export type VerifyPayload = IrisVerifyPayload

// ---- Form builders -------------------------------------------------------

function buildIrisEnrollForm(p: IrisEnrollPayload): FormData {
  const fd = new FormData()
  fd.append('image', p.image, 'capture.png')
  if (p.display_name) fd.append('display_name', p.display_name)
  fd.append('eye_side', p.eye_side ?? 'left')
  return fd
}

function buildIrisVerifyForm(p: IrisVerifyPayload): FormData {
  const fd = new FormData()
  fd.append('image', p.image, 'capture.png')
  fd.append('subject_id', p.subject_id)
  if (p.eye_side) fd.append('eye_side', p.eye_side)
  return fd
}

function buildFingerprintEnrollForm(p: FingerprintEnrollPayload): FormData {
  const fd = new FormData()
  fd.append('image', p.image, 'capture.png')
  if (p.display_name) fd.append('display_name', p.display_name)
  fd.append('finger_position', p.finger_position ?? 'right_index')
  return fd
}

function buildFingerprintVerifyForm(p: FingerprintVerifyPayload): FormData {
  const fd = new FormData()
  fd.append('image', p.image, 'capture.png')
  fd.append('subject_id', p.subject_id)
  if (p.finger_position) fd.append('finger_position', p.finger_position)
  return fd
}

export const api = {
  apiBase: API_BASE,
  health: () => request<Health>('/api/v1/health', { timeoutMs: TIMEOUT_HEALTH_MS }),
  enrollIris: (p: IrisEnrollPayload) =>
    request<IrisEnrollResult>('/api/v1/iris/enroll', {
      method: 'POST',
      body: buildIrisEnrollForm(p),
    }),
  verifyIris: (p: IrisVerifyPayload) =>
    request<IrisVerifyResult>('/api/v1/iris/verify', {
      method: 'POST',
      body: buildIrisVerifyForm(p),
    }),
  enrollFingerprint: (p: FingerprintEnrollPayload) =>
    request<FingerprintEnrollResult>('/api/v1/fingerprint/enroll', {
      method: 'POST',
      body: buildFingerprintEnrollForm(p),
    }),
  verifyFingerprint: (p: FingerprintVerifyPayload) =>
    request<FingerprintVerifyResult>('/api/v1/fingerprint/verify', {
      method: 'POST',
      body: buildFingerprintVerifyForm(p),
    }),
}
