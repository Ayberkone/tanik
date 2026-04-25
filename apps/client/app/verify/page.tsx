'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'

import { IrisForm } from '@/components/iris-form'
import { buttonVariants } from '@/components/ui/button'
import { TanikApiError, api } from '@/lib/api'
import { useCaptureStore } from '@/lib/store'
import { cn } from '@/lib/utils'

function VerifyInner() {
  const search = useSearchParams()
  const seedSubjectId = search.get('subject_id') ?? ''
  const [subjectId, setSubjectId] = useState(seedSubjectId)
  const store = useCaptureStore()

  useEffect(() => {
    if (store.state === 'IDLE') store.startCapture('verify')
    return () => {
      store.reset()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const submit = async () => {
    if (!store.imageBlob || !subjectId.trim()) return
    store.beginUpload()
    try {
      store.serverProcessing()
      const result = await api.verifyIris({
        image: store.imageBlob,
        subject_id: subjectId.trim(),
      })
      store.verifySucceeded(result)
    } catch (err) {
      const e =
        err instanceof TanikApiError
          ? { code: err.body.error_code, message: err.body.message, request_id: err.body.request_id }
          : { code: 'NETWORK' as const, message: err instanceof Error ? err.message : String(err), request_id: null }
      store.failed(e)
    }
  }

  const inFlight = store.isInFlight()
  const canSubmit = store.canSubmit() && subjectId.trim().length > 0

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-12">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Verify</h1>
          <p className="text-sm text-muted-foreground">
            Match a fresh iris capture against a known subject.
          </p>
        </div>
        <Link href="/" className={cn(buttonVariants({ variant: 'ghost' }), 'h-auto py-2 text-xs')}>
          ← Home
        </Link>
      </header>

      {store.state === 'SUCCESS' && store.verifyResult ? (
        <ResultPanel result={store.verifyResult} onAnother={() => store.reset()} />
      ) : (
        <>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Subject ID</span>
            <input
              type="text"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              disabled={inFlight}
              placeholder="UUID returned by /enroll"
              className="w-full rounded-md border bg-background px-3 py-2 font-mono text-xs shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </label>

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
              {inFlight ? 'Verifying…' : 'Verify'}
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

function ResultPanel({
  result,
  onAnother,
}: {
  result: {
    matched: boolean
    hamming_distance: number
    threshold: number
    subject_id: string
    decision_at: string
  }
  onAnother: () => void
}) {
  const matched = result.matched
  return (
    <section
      className={cn(
        'rounded-lg border p-4 text-sm',
        matched
          ? 'border-emerald-200 bg-emerald-50 dark:border-emerald-900/50 dark:bg-emerald-950/30'
          : 'border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/30',
      )}
    >
      <p className={cn('font-medium', matched ? 'text-emerald-900 dark:text-emerald-200' : 'text-red-900 dark:text-red-200')}>
        {matched ? 'Match — same iris' : 'No match — different iris'}
      </p>
      <dl className={cn('mt-3 grid gap-1 text-xs', matched ? 'text-emerald-900/80 dark:text-emerald-200/80' : 'text-red-900/80 dark:text-red-200/80')}>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">hamming_distance</dt>
          <dd className="font-mono">{result.hamming_distance.toFixed(4)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">threshold</dt>
          <dd className="font-mono">{result.threshold.toFixed(4)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">subject_id</dt>
          <dd className="break-all font-mono">{result.subject_id}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-32 shrink-0">decision_at</dt>
          <dd>{result.decision_at}</dd>
        </div>
      </dl>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={onAnother}
          className={cn(buttonVariants({ variant: 'default' }), 'h-8 px-3 text-xs')}
        >
          Verify another
        </button>
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

export default function VerifyPage() {
  // useSearchParams requires Suspense in App Router.
  return (
    <Suspense fallback={null}>
      <VerifyInner />
    </Suspense>
  )
}
