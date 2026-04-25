---
name: new-component
description: Create a new React component for the TANIK Next.js client. Tailwind + shadcn/ui + TypeScript strict + accessibility. Server component by default; webcam tracks must clean up.
---

# /new-component — Add a TANIK client component

> Applies once `apps/client/` exists (Phase 1 task #23 onward).

## 1. Decide: server or client component?

Server by default. Add `'use client'` only if the component:
- Uses hooks (`useState`, `useEffect`, `useRef`)
- Listens to events
- Uses browser APIs (webcam, localStorage, IntersectionObserver)
- Subscribes to the Zustand store

Capture-flow components are almost always client components; presentational sections (headers, cards) are usually server.

## 2. Place + name

```
apps/client/components/
  <Domain>/
    <ComponentName>.tsx
    <ComponentName>.test.tsx
```

PascalCase. Co-locate the test next to the component.

## 3. Component skeleton

```typescript
/**
 * <ComponentName> — one-line purpose.
 */
'use client'  // only if needed

import { cn } from '@/lib/utils'

interface <ComponentName>Props {
  title: string
  onSubmit?: (value: string) => void
  className?: string
}

export function <ComponentName>({ title, onSubmit, className }: <ComponentName>Props) {
  return (
    <section className={cn('flex flex-col gap-4 p-4', className)} aria-label={title}>
      <h2 className="text-lg font-medium">{title}</h2>
      {/* ... */}
    </section>
  )
}
```

Rules:

- Typed `Props` interface — never inline types on the function signature
- Semantic HTML (`<section>`, `<article>`, `<nav>`, `<header>`, `<button>`)
- ARIA labels on interactive elements
- No `any`, no inline `style={...}` for layout, no hardcoded colors

## 4. Webcam components — non-negotiable cleanup

If the component opens a `MediaStream`, the cleanup is mandatory and the #1 expected source of production bugs:

```typescript
useEffect(() => {
  let stream: MediaStream | null = null
  navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    .then((s) => {
      stream = s
      if (videoRef.current) videoRef.current.srcObject = s
    })
    .catch((e) => setError(e.message))

  return () => {
    stream?.getTracks().forEach((t) => t.stop())
    if (videoRef.current) videoRef.current.srcObject = null
  }
}, [])
```

Never skip the `.stop()`. Kiosk hardware leaks are the kind of bug that surfaces only in production.

Throttle frame submission (2-3 fps), never stream full frame rate to the backend.

## 5. State machine integration

If the component participates in the capture flow, it reads from / dispatches to the Zustand store. It does **not** carry its own duplicate state for the same concept — the store is the source of truth for `IDLE | CAPTURING | UPLOADING | PROCESSING | SUCCESS | FAILED`.

UI must not allow forbidden transitions (e.g., a Verify button is disabled unless the store is in a state that allows verify).

## 6. Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { <ComponentName> } from './<ComponentName>'

describe('<ComponentName>', () => {
  it('renders the title', () => {
    render(<<ComponentName> title="Test" />)
    expect(screen.getByRole('heading', { name: 'Test' })).toBeInTheDocument()
  })

  it('calls onSubmit when the button is clicked', () => {
    const onSubmit = vi.fn()
    render(<<ComponentName> title="x" onSubmit={onSubmit} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onSubmit).toHaveBeenCalledOnce()
  })
})
```

For webcam components, mock `navigator.mediaDevices.getUserMedia` and assert that `.stop()` is called on cleanup.

## 7. Verify

```bash
cd apps/client && pnpm test <ComponentName>
pnpm build  # at least once before commit
```

## Anti-patterns

- ❌ `'use client'` everywhere — defeats SSR; only where it's needed
- ❌ Inline styles for layout — use Tailwind utilities
- ❌ Forgetting webcam track cleanup — kiosk leak, always Critical
- ❌ Component-local state that duplicates the Zustand store
- ❌ Hardcoded API URLs — read from `process.env.NEXT_PUBLIC_API_URL`
