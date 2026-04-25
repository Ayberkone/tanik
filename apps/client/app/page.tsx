import Link from 'next/link'

import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { api, TanikApiError } from '@/lib/api'

type HealthStatus =
  | { kind: 'ok'; iris_engine: string; version: string }
  | { kind: 'down'; reason: string }

async function getHealth(): Promise<HealthStatus> {
  try {
    const h = await api.health()
    return { kind: 'ok', iris_engine: h.iris_engine, version: h.version }
  } catch (err) {
    const reason =
      err instanceof TanikApiError
        ? `${err.status} ${err.body.error_code}: ${err.body.message}`
        : err instanceof Error
        ? err.message
        : 'unknown error'
    return { kind: 'down', reason }
  }
}

export const dynamic = 'force-dynamic'

export default async function Home() {
  const health = await getHealth()
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-8 px-6 py-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">TANIK</h1>
        <p className="text-sm text-muted-foreground">
          Multi-modal biometric authentication kiosk — iris + fingerprint, fused into one
          decision. This is the operator surface for enrollment and verification.
        </p>
      </header>

      <section
        aria-label="Inference service status"
        className="rounded-lg border bg-card p-4"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-0.5">
            <p className="text-sm font-medium">Inference service</p>
            {health.kind === 'ok' ? (
              <p className="text-xs text-muted-foreground">
                {health.iris_engine} · backend v{health.version}
              </p>
            ) : (
              <p className="text-xs text-destructive">unreachable — {health.reason}</p>
            )}
          </div>
          <span
            aria-label={health.kind === 'ok' ? 'healthy' : 'down'}
            className={`inline-block size-2.5 rounded-full ${
              health.kind === 'ok' ? 'bg-emerald-500' : 'bg-red-500'
            }`}
          />
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          API base: <code className="rounded bg-muted px-1 py-0.5">{api.apiBase}</code>
        </p>
      </section>

      <section className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/enroll"
          className={cn(
            buttonVariants({ variant: 'default' }),
            'h-auto items-start justify-start py-4'
          )}
        >
          <span className="flex flex-col items-start gap-1">
            <span className="text-base font-medium">Enroll</span>
            <span className="text-xs font-normal opacity-80">
              Capture an iris and create a new subject.
            </span>
          </span>
        </Link>
        <Link
          href="/verify"
          className={cn(
            buttonVariants({ variant: 'secondary' }),
            'h-auto items-start justify-start py-4'
          )}
        >
          <span className="flex flex-col items-start gap-1">
            <span className="text-base font-medium">Verify</span>
            <span className="text-xs font-normal opacity-80">
              Match a fresh capture against an enrolled subject.
            </span>
          </span>
        </Link>
      </section>
    </main>
  )
}
