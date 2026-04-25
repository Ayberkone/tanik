'use client'

import { useCallback, useState } from 'react'

import { cn } from '@/lib/utils'

export type FingerprintFormProps = {
  /** Called once with the chosen image bytes (uploaded file). */
  onImage: (blob: Blob) => void
  /** Called when an active source surfaces an error. */
  onError?: (message: string) => void
  /** Currently-selected image — if set, shown as a preview thumb. */
  preview: Blob | null
  /** Disables interaction (during upload / processing). */
  disabled?: boolean
  className?: string
}

/**
 * Upload-only image picker for fingerprint flows. Webcam capture is
 * deliberately NOT offered here — fingerprint matching needs ridge detail
 * that consumer webcams cannot reliably produce. A real kiosk would use a
 * dedicated capture device (Suprema, DigitalPersona, etc.) which is
 * deferred to v2 per ROADMAP.
 */
export function FingerprintForm({ onImage, preview, disabled, className }: FingerprintFormProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const setPreview = useCallback((blob: Blob | null) => {
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return blob ? URL.createObjectURL(blob) : null
    })
  }, [])

  const handleFile = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      setPreview(file)
      onImage(file)
    },
    [onImage, setPreview],
  )

  // Keep preview in sync with the controlled blob from the parent. If the
  // store resets to null (after success / failure), drop the URL too.
  if (preview === null && previewUrl !== null) {
    URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
  }

  return (
    <div className={cn('flex flex-col gap-3', className)} aria-disabled={disabled}>
      <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted px-6 py-12 text-sm text-muted-foreground hover:bg-muted/70">
        <span>Drop a fingerprint image here, or click to browse</span>
        <span className="text-xs opacity-70">PNG / JPEG / BMP, max 10 MB</span>
        <input
          type="file"
          accept="image/png,image/jpeg,image/bmp"
          disabled={disabled}
          onChange={handleFile}
          className="sr-only"
        />
      </label>

      {previewUrl && (
        <figure className="rounded-md border bg-card p-2">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Selected image</p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Selected fingerprint capture preview"
            className="mx-auto max-h-48 rounded"
          />
        </figure>
      )}
    </div>
  )
}
