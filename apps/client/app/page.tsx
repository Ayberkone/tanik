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

const FLOWS = [
  {
    href: '/enroll',
    label: 'Enroll iris',
    desc: 'Capture or upload an iris image and create a new subject.',
    variant: 'default' as const,
  },
  {
    href: '/verify',
    label: 'Verify iris',
    desc: 'Match a fresh iris capture against an enrolled subject.',
    variant: 'secondary' as const,
  },
  {
    href: '/fingerprint/enroll',
    label: 'Enroll fingerprint',
    desc: 'Upload a fingerprint image and create a new subject.',
    variant: 'default' as const,
  },
  {
    href: '/fingerprint/verify',
    label: 'Verify fingerprint',
    desc: 'Match a fresh fingerprint capture against an enrolled subject.',
    variant: 'secondary' as const,
  },
]

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
        {FLOWS.map((flow) => (
          <Link
            key={flow.href}
            href={flow.href}
            className={cn(
              buttonVariants({ variant: flow.variant }),
              'h-auto items-start justify-start py-4',
            )}
          >
            <span className="flex flex-col items-start gap-1">
              <span className="text-base font-medium">{flow.label}</span>
              <span className="text-xs font-normal opacity-80">{flow.desc}</span>
            </span>
          </Link>
        ))}
      </section>
    </main>
  )
}
