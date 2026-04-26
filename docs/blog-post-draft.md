# Blog post — draft

> **Status:** draft, Phase 5 prep. Ready to publish on dev.to / personal blog / Medium / Hashnode once you (a) want to and (b) have at least the headline FAR/FRR numbers from `docs/performance.md` (or are willing to publish without them as a "what an honest reference looks like" post).
>
> **Tone:** conversational, first-person, technical-but-not-academic. Aim is engineers in the biometrics or identity space; not researchers.
>
> **Suggested title (pick one):**
> 1. *What an honest biometric kiosk looks like under the hood*
> 2. *TANIK: building a multi-modal biometric reference, with the honesty discipline turned up*
> 3. *I built an open-source iris + fingerprint kiosk — here's what's actually inside*

---

## Why I'm writing this

There's a pattern in demo biometric systems on GitHub that I find frustrating. Someone pulls in face_recognition or a random fingerprint matcher, wires it to a Flask endpoint, claims "99.9% accuracy" or "anti-spoofing built-in," and ships. The README never says where the 99.9% came from, the threat model never mentions printed photos, and the "anti-spoofing" turns out to be a vibe rather than a published model trained on a published dataset.

I work in software (full-stack, currently), but I'm trying to move toward biometric identity work. So I built **TANIK** — Turkish for *witness* — as a reference implementation that does the opposite of that pattern. Two real biometric matchers. A documented threat model. No invented numbers. Honest about what it doesn't yet do.

This post walks through what's inside.

## What it is, briefly

A multi-modal biometric kiosk. A user presents an **iris** and a **fingerprint**, the system fuses both into a single identity decision, and every claim it makes has a verification path.

```
┌──────────────────────────────┐         ┌──────────────────────────────────────┐
│  Client (Next.js, browser)   │  HTTPS  │  Inference (FastAPI, Python 3.10)    │
│  ─ Webcam capture            │ ──────► │  ─ open-iris pipeline                │
│  ─ Capture state machine     │         │  ─ SourceAFIS via JPype/JVM          │
│  ─ Per-modality forms        │ ◄────── │  ─ SQLite (templates only)           │
│                              │  JSON   │  ─ Fusion + unified verify           │
└──────────────────────────────┘         └──────────────────────────────────────┘
```

Two services, one HTTP contract. The client never runs ML, the inference node never renders UI. Same separation a real production deployment would have.

## Why iris + fingerprint, not face

Face recognition is the easy modality to add — every dependency is on PyPI, every demo project uses it. It's also the modality I deliberately skipped.

| | Iris | Fingerprint | Face |
|---|---|---|---|
| Accuracy ceiling | 1-in-millions FAR | High | High but tail-heavy |
| Presentation-attack surface | Manageable with NIR | Manageable with capacitive sensors | **Severe** — printed photos, screen replays, deepfakes |
| Regulatory weight | Special category under KVKK/GDPR | Same | Same + EU AI Act remote-ID restrictions |

If the project's whole pitch is *"this is what a serious biometric system looks like"*, adding face dilutes it. The two modalities I picked are the ones that biometrics-industry engineers actually respect; both have decades of standards behind them (ISO 19794, NIST IREX); both can hit credible accuracy numbers without a PhD-level model behind them. Worldcoin's `open-iris` for the iris side, SourceAFIS for fingerprint — both open-source, both maintained, both well-cited.

## The HTTP contract is the boundary

Every interaction between client and inference goes through `docs/api-contract.md`. Five endpoints today:

- `GET /api/v1/health`
- `POST /api/v1/iris/{enroll,verify}` — Phase 1
- `POST /api/v1/fingerprint/{enroll,verify}` — Phase 2
- `POST /api/v1/verify` — Phase 3, unified and fused

The contract is the source of truth. If FastAPI's auto-generated OpenAPI doesn't match the contract, the implementation is wrong, not the contract. Both sides have linted against this since day one and it's saved me from drift more than once.

## The interesting bit: score fusion

The most pedagogically interesting piece is **score-level fusion**. The two engines speak different languages:

| Engine | Score | Direction | Range |
|---|---|---|---|
| Iris (`open-iris`) | masked fractional Hamming distance | lower is better | `[0, 1]` (well below 0.5 in practice) |
| Fingerprint (SourceAFIS) | similarity | higher is better | `[0, ∞)` (typical strong matches: hundreds) |

To fuse them you need a common scale. The standard moves are:

1. **Min-max** to some chosen endpoints. Easy, but the choice of endpoints is itself a judgement call, and the per-modality decision threshold has no special status on the normalised scale.
2. **Z-score** against the calibration set's score distribution. Principled, but you need a calibration set you may not have yet.
3. **Logistic** fitted to the calibration set. Same constraint as (2).

I went with a fourth thing: **piecewise-linear, anchored at the per-modality operating threshold.**

```
Iris (lower=better)                Fingerprint (higher=better)
  HD=0   → 1.0                       score=0    → 0.0
  HD=thr → 0.5                       score=thr  → 0.5
  HD=ceil→ 0.0                       score=ceil → 1.0
```

The operating threshold is the only number on each engine's native scale we already trust — so we anchor to it. An engine-native score equal to its threshold maps to a normalised score of exactly `0.5`. That gives the fused decision threshold of `0.5` a clear semantic: *"both modalities are sitting right at their per-modality operating point."* Move either modality's evidence up or down from there and the fused score moves accordingly.

```python
def normalise_iris(hd: float, *, floor: float, threshold: float, ceil: float) -> float:
    if hd <= floor:    return 1.0
    if hd >= ceil:     return 0.0
    if hd <= threshold:
        return 1.0 - 0.5 * (hd - floor) / (threshold - floor)
    return 0.5 - 0.5 * (hd - threshold) / (ceil - threshold)
```

Fusion itself is a weighted sum, with weights renormalised over the modalities the request actually supplied — so a single-modality unified call cleanly equals that modality's normalised score (no halving by the absent modality's weight). That edge case is where I see most fused-system bugs in the wild.

## The honest twist

If you've read this far, you might be wondering: *"What FAR and FRR does this fused system achieve?"*

Right now: I don't know. I don't have the held-out test set yet — I'm waiting on a license for ND-IRIS-0405 and an FVC-style fingerprint dataset.

So the API responds honestly. Every unified-verify response carries:

```json
{
  "matched": true,
  "fused_score": 0.78,
  "threshold": 0.5,
  "modalities": [...],
  "calibration_status": "placeholder",
  "calibration_reference": "docs/fusion.md"
}
```

The `calibration_status: "placeholder"` field is the system telling you, in-band, that the weights and normalisation knobs powering this decision are *not* tuned. They're honest defaults, chosen so the system runs end-to-end. A downstream consumer that needs measured FAR/FRR is supposed to refuse a placeholder response.

`docs/performance.md` exists in the repo as a skeleton — every numeric cell reads `TBD`. When the dataset lands, an evaluation harness writes the file. **No number in that file has ever been hand-typed**, and that's enforced by convention. "TBD — awaiting evaluation run" is acceptable; an invented "1 in 1,000,000" is not.

The same discipline applies elsewhere:

- The Phase 4 PAD module will be documented as a *basic* defence, not "military grade." Real iris-PAD requires NIR multi-spectral hardware features that this software-only system does not have.
- Privacy claims use precise language. The system stores templates, not raw images — but **templates are personal data**, both under KVKK (Türkiye) and GDPR (EU). "Zero-knowledge" is the wrong phrase for template-only systems, and I don't use it.

This is the credibility argument. Anyone reading the repo can check that there's no `.save()` call against the upload bytes anywhere in the codebase. Anyone reading `docs/threat-model.md` finds an attack-by-attack table of what's currently defended and what isn't. Honesty is the feature.

## Architecture decisions that mattered

### Modality-agnostic engine + storage

Both engines satisfy a single Python `Protocol`:

```python
class BiometricEngine(Protocol):
    name: str
    def template_version(self) -> str: ...
    async def encode(self, image_bytes: bytes, **kwargs) -> Tuple[Optional[bytes], Optional[str]]: ...
    async def match(self, probe: bytes, gallery: bytes) -> float: ...
```

Templates cross the boundary as opaque `bytes`. Each engine owns its own serialisation format. Storage records the `template_version` so a mismatched matcher can be detected later.

The benefit: adding a third modality (face, voice, behavioural) is a one-file change at the engine layer + one row in a registry. The API and storage layers don't move.

### Threadpool everything CPU-bound

FastAPI is async. Iris segmentation is CPU-bound (Gabor convolution, ONNX segmentation). SourceAFIS matching crosses the JNI boundary into the JVM. Either would block the event loop if called inline. Both engines wrap their work in `run_in_threadpool`:

```python
async def encode(image_bytes: bytes, ...) -> ...:
    return await run_in_threadpool(_encode_sync, image_bytes, ...)
```

This is the Python production rule that catches every team learning async: "async" doesn't mean "non-blocking magic." If you call a CPU-bound function from an async handler without offloading, you've blocked the entire event loop until it returns.

### Single-JVM-per-process for the fingerprint side

JPype enforces single-JVM-per-process. That's not a limitation — it lines up exactly with FastAPI's recommended single-worker-per-pod deployment model. The JVM starts lazily on the first fingerprint request and is reused for the lifetime of the process. Subsequent requests pay no JVM startup cost.

### Strict capture state machine in the client

A Zustand store with explicit transitions:

```
IDLE → CAPTURING → UPLOADING → PROCESSING → SUCCESS | FAILED
                                                  ↓
                                                IDLE
```

Illegal transitions throw in dev (and log in production — kiosk uptime trumps strictness once you have real users). The most common kiosk failure mode is the UI letting a user double-submit or skip a state; a strict machine catches that at compile-time.

## Where it stands

Five phases on the roadmap. As of writing:

- **Phase 0** ✅ — iris pipeline spike notebook
- **Phase 1** ✅ implementation, ⏳ deploy — iris enroll/verify end-to-end
- **Phase 2** ✅ — fingerprint via SourceAFIS, modality-agnostic interface
- **Phase 3** ⏳ — unified verify shipped with placeholder calibration; measured numbers blocked on dataset acquisition
- **Phase 4** — liveness (PAD) + admin dashboard
- **Phase 5** — landing page + this blog post + outreach

## What I'd love feedback on

If you work in biometric identity — at a vendor, in research, at a national-ID program — I'd value pushback on:

- The fusion methodology. The piecewise-linear-anchored-at-threshold approach is unconventional. I think it's defensible (and I document it in `docs/fusion.md`); I'd love to know where someone in the field disagrees.
- The threat model. `docs/threat-model.md` is a working draft. The most useful thing a reviewer can do is point at an attack I haven't enumerated.
- The honesty discipline. The framing — "every claim has a verification path or a TBD label" — is worth more or less depending on whether you've worked in regulated identity. I'd love to know how it lands.

Repo: <https://github.com/Ayberkone/tanik> · MIT licensed · issues and PRs welcome.

---

*— Ayberk Baytok, building TANIK on weekends from Türkiye.*
