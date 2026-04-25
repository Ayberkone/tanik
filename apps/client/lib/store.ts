import { create } from 'zustand'

import type { ApiError, EnrollResult, VerifyResult } from './api'

export const CAPTURE_STATES = [
  'IDLE',
  'CAPTURING',
  'UPLOADING',
  'PROCESSING',
  'SUCCESS',
  'FAILED',
] as const
export type CaptureState = (typeof CAPTURE_STATES)[number]

export type Flow = 'enroll' | 'verify'

export type { EnrollResult, VerifyResult }

export type CaptureError = {
  code: ApiError['error_code'] | 'NETWORK' | 'INTERNAL'
  message: string
  request_id: string | null
}

// Allowed transitions. Anything not listed is a programmer error and the
// store throws on it (in dev). The capture flow is strict by design — the
// UI must not let a user into PROCESSING without a captured image, etc.
const ALLOWED: Record<CaptureState, ReadonlyArray<CaptureState>> = {
  IDLE: ['CAPTURING'],
  CAPTURING: ['UPLOADING', 'IDLE'],
  UPLOADING: ['PROCESSING', 'FAILED'],
  PROCESSING: ['SUCCESS', 'FAILED'],
  SUCCESS: ['IDLE'],
  FAILED: ['IDLE'],
}

interface CaptureStore {
  state: CaptureState
  flow: Flow | null
  imageBlob: Blob | null
  enrollResult: EnrollResult | null
  verifyResult: VerifyResult | null
  verifyAgainstSubjectId: string | null
  error: CaptureError | null

  // Actions — each checks the transition and throws in dev on illegal moves.
  startCapture: (flow: Flow, opts?: { verifyAgainstSubjectId?: string }) => void
  imageReady: (blob: Blob) => void
  beginUpload: () => void
  serverProcessing: () => void
  enrollSucceeded: (r: EnrollResult) => void
  verifySucceeded: (r: VerifyResult) => void
  failed: (err: CaptureError) => void
  reset: () => void

  // Selector helpers
  canCapture: () => boolean
  canSubmit: () => boolean
  isInFlight: () => boolean
}

function assertTransition(from: CaptureState, to: CaptureState): void {
  if (!ALLOWED[from].includes(to)) {
    const msg = `Illegal capture-state transition: ${from} → ${to}. Allowed: ${ALLOWED[from].join(', ') || '(none)'}`
    if (process.env.NODE_ENV !== 'production') {
      throw new Error(msg)
    } else {
      // In production, log but do not throw — kiosk uptime trumps strict typing.
      console.error(msg)
    }
  }
}

export const useCaptureStore = create<CaptureStore>((set, get) => ({
  state: 'IDLE',
  flow: null,
  imageBlob: null,
  enrollResult: null,
  verifyResult: null,
  verifyAgainstSubjectId: null,
  error: null,

  startCapture: (flow, opts) => {
    assertTransition(get().state, 'CAPTURING')
    set({
      state: 'CAPTURING',
      flow,
      imageBlob: null,
      enrollResult: null,
      verifyResult: null,
      verifyAgainstSubjectId: opts?.verifyAgainstSubjectId ?? null,
      error: null,
    })
  },

  imageReady: (blob) => {
    // Stays in CAPTURING — image is held, ready for the user to confirm submit.
    if (get().state !== 'CAPTURING') {
      assertTransition(get().state, 'CAPTURING')
    }
    set({ imageBlob: blob })
  },

  beginUpload: () => {
    assertTransition(get().state, 'UPLOADING')
    set({ state: 'UPLOADING' })
  },

  serverProcessing: () => {
    assertTransition(get().state, 'PROCESSING')
    set({ state: 'PROCESSING' })
  },

  enrollSucceeded: (r) => {
    assertTransition(get().state, 'SUCCESS')
    set({ state: 'SUCCESS', enrollResult: r })
  },

  verifySucceeded: (r) => {
    assertTransition(get().state, 'SUCCESS')
    set({ state: 'SUCCESS', verifyResult: r })
  },

  failed: (err) => {
    assertTransition(get().state, 'FAILED')
    set({ state: 'FAILED', error: err })
  },

  reset: () => {
    if (get().state !== 'IDLE') {
      assertTransition(get().state, 'IDLE')
    }
    set({
      state: 'IDLE',
      flow: null,
      imageBlob: null,
      enrollResult: null,
      verifyResult: null,
      verifyAgainstSubjectId: null,
      error: null,
    })
  },

  canCapture: () => get().state === 'CAPTURING' && get().imageBlob === null,
  canSubmit: () => get().state === 'CAPTURING' && get().imageBlob !== null,
  isInFlight: () => {
    const s = get().state
    return s === 'UPLOADING' || s === 'PROCESSING'
  },
}))
