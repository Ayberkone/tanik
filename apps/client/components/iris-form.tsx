'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { WebcamCapture } from '@/components/webcam-capture'
import { cn } from '@/lib/utils'

export type IrisFormSource = 'camera' | 'file'

export type IrisFormProps = {
  /** Called once with the chosen image bytes (PNG from camera, original from file). */
  onImage: (blob: Blob) => void
  /** Called when an active source surfaces an error (camera permission denied, etc.). */
  onError?: (message: string) => void
  /** Currently-selected image — if set, shown as a preview thumb. */
  preview: Blob | null
  /** Disables interaction (during upload / processing). */
  disabled?: boolean
  className?: string
}

/**
 * Shared image-source picker used by both /enroll and /verify.
 * Lets the operator switch between live webcam capture and file upload
 * without duplicating the toggle, the preview pane, or the error wiring.
 *
 * Callback props (`onImage`, `onError`) live in refs so this component's
 * children — particularly `WebcamCapture` — never see callback identity
 * churn from parent re-renders. Without this, typing in a sibling input
 * tears down the camera stream every keystroke. See WebcamCapture docstring.
 */
export function IrisForm({ onImage, onError, preview, disabled, className }: IrisFormProps) {
  const [source, setSource] = useState<IrisFormSource>('camera')

  const onImageRef = useRef(onImage)
  const onErrorRef = useRef(onError)
  useEffect(() => {
    onImageRef.current = onImage
  }, [onImage])
  useEffect(() => {
    onErrorRef.current = onError
  }, [onError])

  // Object URL is derived from the upstream blob — useMemo so we don't
  // store it in state (avoids setState-in-effect). Cleanup effect revokes
  // the previous URL whenever the memoised value changes (or on unmount),
  // preventing object-URL leaks.
  const previewUrl = useMemo(
    () => (preview ? URL.createObjectURL(preview) : null),
    [preview],
  )
  useEffect(() => {
    if (!previewUrl) return
    return () => URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  const handleCapture = useCallback((blob: Blob) => {
    onImageRef.current(blob)
  }, [])

  const handleCameraError = useCallback((msg: string) => {
    onErrorRef.current?.(msg)
  }, [])

  const handleFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    onImageRef.current(file)
  }, [])

  return (
    <div className={cn('flex flex-col gap-3', className)} aria-disabled={disabled}>
      <div role="tablist" aria-label="Image source" className="inline-flex gap-1 rounded-md bg-muted p-1 text-xs">
        <button
          role="tab"
          aria-selected={source === 'camera'}
          type="button"
          disabled={disabled}
          onClick={() => setSource('camera')}
          className={cn(
            'rounded px-3 py-1 transition-colors',
            source === 'camera' ? 'bg-background shadow-sm' : 'text-muted-foreground',
          )}
        >
          Camera
        </button>
        <button
          role="tab"
          aria-selected={source === 'file'}
          type="button"
          disabled={disabled}
          onClick={() => setSource('file')}
          className={cn(
            'rounded px-3 py-1 transition-colors',
            source === 'file' ? 'bg-background shadow-sm' : 'text-muted-foreground',
          )}
        >
          Upload file
        </button>
      </div>

      {source === 'camera' ? (
        <WebcamCapture onCapture={handleCapture} onError={handleCameraError} />
      ) : (
        <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted px-6 py-12 text-sm text-muted-foreground hover:bg-muted/70">
          <span>Drop an iris image here, or click to browse</span>
          <span className="text-xs opacity-70">PNG / JPEG / BMP, max 10 MB</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/bmp"
            disabled={disabled}
            onChange={handleFile}
            className="sr-only"
          />
        </label>
      )}

      {previewUrl && (
        <figure className="rounded-md border bg-card p-2">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Selected image</p>
          {/* In-memory blob URL — next/image cannot optimize these and would
              warn about missing dimensions. Plain <img> is correct here. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Selected iris capture preview"
            className="mx-auto max-h-48 rounded"
          />
        </figure>
      )}
    </div>
  )
}
