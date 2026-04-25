'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

import { IrisForm } from '@/components/iris-form'
import { buttonVariants } from '@/components/ui/button'
import { TanikApiError, api } from '@/lib/api'
import { useCaptureStore } from '@/lib/store'
import { cn } from '@/lib/utils'

export default function EnrollPage() {
  const store = useCaptureStore()
  const [displayName, setDisplayName] = useState('')
  const [eyeSide, setEyeSide] = useState<'left' | 'right'>('left')

  // Enter CAPTURING on mount; reset on unmount so /verify starts clean.
  useEffect(() => {
    if (store.state === 'IDLE') store.startCapture('enroll')
    return () => {
      store.reset()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const submit = async () => {
    if (!store.imageBlob) return
    store.beginUpload()
    try {
      store.serverProcessing()
      const result = await api.enrollIris({
        image: store.imageBlob,
        display_name: displayName.trim() || undefined,
        eye_side: eyeSide,
      })
      store.enrollSucceeded(result)
    } catch (err) {
      const e =
        err instanceof TanikApiError
          ? { code: err.body.error_code, message: err.body.message, request_id: err.body.request_id }
          : { code: 'NETWORK' as const, message: err instanceof Error ? err.message : String(err), request_id: null }
      store.failed(e)
    }
  }

  const inFlight = store.isInFlight()
  const canSubmit = store.canSubmit() && displayName.trim().length <= 64

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-12">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Enroll</h1>
          <p className="text-sm text-muted-foreground">
            Capture or upload one iris image and create a new subject.
          </p>
        </div>
        <Link href="/" className={cn(buttonVariants({ variant: 'ghost' }), 'h-auto py-2 text-xs')}>
          ← Home
        </Link>
      </header>

      {store.state === 'SUCCESS' && store.enrollResult ? (
        <SuccessPanel result={store.enrollResult} onAnother={() => store.reset()} />
      ) : (
        <>
          <section className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm">
              <span className="mb-1 block font-medium">Display name (optional)</span>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                disabled={inFlight}
                maxLength={64}
                placeholder="Alice"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block font-medium">Eye side</span>
              <select
                value={eyeSide}
                onChange={(e) => setEyeSide(e.target.value as 'left' | 'right')}
                disabled={inFlight}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="left">left</option>
                <option value="right">right</option>
              </select>
            </label>
          </section>

          <IrisForm
            onImage={(blob) => store.imageReady(blob)}
            onError={(msg) => store.failed({ code: 'NETWORK', message: msg, request_id: null })}
            preview={store.imageBlob}
            disabled={inFlight}
          />

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={submit}
              disabled={!canSubmit || inFlight}
              className={cn(
                buttonVariants({ variant: 'default' }),
                'h-9 px-4',
                'disabled:cursor-not-allowed disabled:opacity-60',
              )}
            >
              {inFlight ? 'Enrolling…' : 'Enroll'}
            </button>
            <p className="text-xs text-muted-foreground">
              {store.state === 'CAPTURING' && !store.imageBlob && 'Capture or upload an image to continue.'}
              {store.state === 'UPLOADING' && 'Uploading image…'}
              {store.state === 'PROCESSING' && 'Server is running the iris pipeline…'}
            </p>
          </div>

          {store.state === 'FAILED' && store.error && <ErrorPanel error={store.error} onRetry={() => store.reset()} />}
        </>
      )}
    </main>
  )
}

function SuccessPanel({
  result,
  onAnother,
}: {
  result: { subject_id: string; display_name: string | null; enrolled_at: string; template_version: string }
  onAnother: () => void
}) {
  return (
    <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm dark:border-emerald-900/50 dark:bg-emerald-950/30">
      <p className="font-medium text-emerald-900 dark:text-emerald-200">Enrollment created.</p>
      <dl className="mt-3 grid gap-1 text-xs text-emerald-900/80 dark:text-emerald-200/80">
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">subject_id</dt>
          <dd className="break-all font-mono">{result.subject_id}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">display_name</dt>
          <dd>{result.display_name ?? '—'}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">enrolled_at</dt>
          <dd>{result.enrolled_at}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">template</dt>
          <dd className="font-mono">{result.template_version}</dd>
        </div>
      </dl>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={onAnother}
          className={cn(buttonVariants({ variant: 'default' }), 'h-8 px-3 text-xs')}
        >
          Enroll another
        </button>
        <Link
          href={`/verify?subject_id=${result.subject_id}`}
          className={cn(buttonVariants({ variant: 'secondary' }), 'h-8 px-3 text-xs')}
        >
          Verify this subject →
        </Link>
      </div>
    </section>
  )
}

function ErrorPanel({
  error,
  onRetry,
}: {
  error: { code: string; message: string; request_id: string | null }
  onRetry: () => void
}) {
  return (
    <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm dark:border-red-900/50 dark:bg-red-950/30">
      <p className="font-medium text-red-900 dark:text-red-200">{error.code}</p>
      <p className="mt-1 text-xs text-red-900/80 dark:text-red-200/80">{error.message}</p>
      {error.request_id && (
        <p className="mt-2 font-mono text-[10px] text-red-900/60 dark:text-red-200/60">
          request_id: {error.request_id}
        </p>
      )}
      <button
        type="button"
        onClick={onRetry}
        className={cn(buttonVariants({ variant: 'outline' }), 'mt-3 h-8 px-3 text-xs')}
      >
        Try again
      </button>
    </section>
  )
}
