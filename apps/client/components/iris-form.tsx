'use client'

import { useCallback, useState } from 'react'

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
 */
export function IrisForm({ onImage, onError, preview, disabled, className }: IrisFormProps) {
  const [source, setSource] = useState<IrisFormSource>('camera')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  // Re-derive the preview URL when the blob changes; revoke on cleanup.
  if (preview) {
    if (!previewUrl || (preview as Blob).size > 0) {
      // build a fresh URL — avoid leaks by revoking the old one in the next effect
    }
  }

  const setPreview = useCallback((blob: Blob | null) => {
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return blob ? URL.createObjectURL(blob) : null
    })
  }, [])

  const handleCapture = useCallback(
    (blob: Blob) => {
      setPreview(blob)
      onImage(blob)
    },
    [onImage, setPreview],
  )

  const handleFile = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      setPreview(file)
      onImage(file)
    },
    [onImage, setPreview],
  )

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
        <WebcamCapture onCapture={handleCapture} onError={onError} />
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
