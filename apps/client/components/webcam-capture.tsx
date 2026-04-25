'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

import { cn } from '@/lib/utils'

export type WebcamCaptureProps = {
  /** Called once with a PNG Blob of the current video frame. */
  onCapture: (blob: Blob) => void
  /** Called when the camera cannot be opened or stops working. */
  onError?: (message: string) => void
  /** Lens to request from the OS — `'user'` is the front-facing camera, `'environment'` is rear. */
  facingMode?: 'user' | 'environment'
  /** Capture resolution hint. Real iris hardware needs much higher; webcam is a kiosk approximation. */
  width?: number
  height?: number
  className?: string
}

type Status = 'idle' | 'requesting' | 'live' | 'denied' | 'unsupported' | 'error'

/**
 * Webcam preview + single-frame capture.
 *
 * Lifecycle invariant: every MediaStreamTrack opened in the useEffect MUST
 * be `.stop()`-ed in the cleanup return. Forgetting this causes the camera
 * LED to stay on after navigation — the #1 expected production bug for
 * kiosk hardware. See CLAUDE.md frontend section.
 */
export function WebcamCapture({
  onCapture,
  onError,
  facingMode = 'user',
  width = 640,
  height = 480,
  className,
}: WebcamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [errMsg, setErrMsg] = useState<string | null>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setStatus('unsupported')
      onError?.('Browser does not expose camera APIs (getUserMedia missing).')
      return
    }

    let cancelled = false
    setStatus('requesting')

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode, width, height }, audio: false })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        video.srcObject = stream
        // Older WebKit needs an explicit play() after setting srcObject.
        video.play().catch(() => {
          // Some browsers reject play() if user has not gestured — show a visible cue.
          setStatus('error')
          setErrMsg('Click anywhere to start the camera.')
        })
        setStatus('live')
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const name = (err as DOMException)?.name ?? ''
        if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
          setStatus('denied')
          setErrMsg('Camera permission was denied. Allow camera access and reload.')
          onError?.('Camera permission denied.')
        } else {
          setStatus('error')
          const message = err instanceof Error ? err.message : 'Could not open camera.'
          setErrMsg(message)
          onError?.(message)
        }
      })

    return () => {
      cancelled = true
      const stream = streamRef.current
      if (stream) {
        stream.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
      if (video) {
        video.srcObject = null
      }
    }
  }, [facingMode, width, height, onError])

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    if (!video || status !== 'live') return
    if (!video.videoWidth || !video.videoHeight) return

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob)
      },
      'image/png',
    )
  }, [onCapture, status])

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg border bg-muted',
        'aspect-[4/3] w-full',
        className,
      )}
      data-status={status}
    >
      <video
        ref={videoRef}
        muted
        playsInline
        autoPlay
        aria-label="Live camera preview"
        className="size-full object-cover"
      />
      {status !== 'live' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-background/85 text-center text-sm">
          {status === 'requesting' && <p>Opening camera…</p>}
          {status === 'denied' && (
            <p className="px-6 text-destructive">{errMsg}</p>
          )}
          {status === 'unsupported' && (
            <p className="px-6 text-muted-foreground">
              This browser does not expose camera APIs. Use the file upload instead.
            </p>
          )}
          {status === 'error' && (
            <p className="px-6 text-destructive">{errMsg ?? 'Camera error.'}</p>
          )}
        </div>
      )}
      {status === 'live' && (
        <button
          type="button"
          onClick={captureFrame}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-background/90 px-4 py-2 text-sm font-medium shadow ring-1 ring-border hover:bg-background"
          aria-label="Capture current frame"
        >
          Capture
        </button>
      )}
    </div>
  )
}
