<!--
TANIK — Proline pitch deck
==========================
Marp-compatible slide deck. Render to PDF/HTML/PPTX with:
    npx @marp-team/marp-cli docs/proline-pitch-deck.md -o tanik-pitch.pdf
    npx @marp-team/marp-cli docs/proline-pitch-deck.md -o tanik-pitch.pptx
    npx @marp-team/marp-cli docs/proline-pitch-deck.md -o tanik-pitch.html

Designed for a ~15-20 minute technical talk to biometric-industry engineers.
~20 slides; each slide is one idea; speaker notes are HTML comments inside
each slide so they survive the Marp render and stay private.
-->

---
marp: true
theme: default
paginate: true
header: 'TANIK — multi-modal biometric reference'
footer: 'Ayberk Baytok · github.com/Ayberkone/tanik'
---

# TANIK
### A multi-modal biometric reference, with the honesty discipline turned up

Ayberk Baytok · 2026

<!--
Speaker notes:
- Open with the title and the project name's meaning: "Tanık" means "witness" — the one who attests something is true. The whole pitch is in that word: a system that *attests* honestly, not one that overclaims.
- Set expectations: this is a 15-20 minute walk through what the system is, what's interesting in it, what it deliberately doesn't do, and where I want feedback.
-->

---

## The problem this responds to

GitHub is full of "biometric" demo projects that:

- Quote a 99.9% accuracy number with no test set documented
- Claim "anti-spoofing" without a published model or dataset
- Store biometric images on disk because nobody made them not to
- Skip the threat model entirely

A Proline-or-IDEMIA-grade engineer can spot this in 30 seconds and dismiss the project.

<!--
Speaker notes:
- The pattern is real. Show the audience you've noticed it — they have too. Don't name names; just describe the pattern they recognise.
- This sets up the credibility argument: TANIK exists to do the opposite, deliberately.
-->

---

## What TANIK is

A multi-modal biometric kiosk. Two modalities (iris + fingerprint), one fused decision, every claim verifiable.

```
┌──────────────────────┐  HTTPS   ┌──────────────────────────────┐
│  Client (Next.js)    │ ──────►  │  Inference (FastAPI)         │
│  ─ Webcam capture    │          │  ─ open-iris pipeline        │
│  ─ State machine     │          │  ─ SourceAFIS via JPype/JVM  │
│  ─ Per-modality UI   │ ◄──────  │  ─ SQLite (templates only)   │
└──────────────────────┘   JSON   └──────────────────────────────┘
```

Open source · MIT · Python 3.10 · Next.js 16 · ~5 weekends of work

<!--
Speaker notes:
- The diagram is the foundational mental model. Two services, one HTTP contract, one direction for ML and one for UI.
- Mention that this is a personal project — not a startup, not a paper — so the audience knows the context. It's a credibility piece for moving toward biometric work.
-->

---

## Why iris + fingerprint, not face

| | Iris | Fingerprint | **Face** |
|---|---|---|---|
| Accuracy ceiling | 1-in-millions FAR | High | High but tail-heavy |
| Presentation-attack surface | Manageable with NIR | Manageable with capacitive | **Severe** |
| Regulatory weight | Special category | Same | Same + EU AI Act |

Adding face dilutes the credibility pitch. Two modalities biometric engineers actually respect.

<!--
Speaker notes:
- The "why not face" is a deliberate signal to the audience that the project is taking serious choices, not just defaulting to whatever is easiest on PyPI.
- The EU AI Act point is timely (2024 regulation, biometric ID heavily restricted) and shows you've done the regulatory homework.
-->

---

## The HTTP contract is the boundary

Five endpoints under `/api/v1`:

- `GET /health`
- `POST /iris/{enroll, verify}` — Phase 1
- `POST /fingerprint/{enroll, verify}` — Phase 2
- `POST /verify` — Phase 3, unified and fused

`docs/api-contract.md` is the source of truth. FastAPI's auto-OpenAPI must match. If they disagree, the **implementation** is wrong.

<!--
Speaker notes:
- The "contract is the source of truth" framing is unusual to spell out — most projects let the implementation drift. Call this out as a deliberate discipline.
- Mention that both client and inference read from the same contract; this is what enables the strict separation of concerns.
-->

---

## Capture state machine — illegal states throw

```
IDLE ──startCapture──► CAPTURING ──beginUpload──► UPLOADING ──serverProcessing──► PROCESSING
                          │                                                            │
                          └──reset──► IDLE                              ┌── SUCCESS    │
                                                                       └── FAILED ◄────┘
```

Single most common kiosk failure mode: illegal UI states (double-submit, missing cleanup). A strict Zustand store catches them at compile-time.

Webcam cleanup is non-negotiable: every `MediaStreamTrack` opened in a `useEffect` is `.stop()`-ed on unmount.

<!--
Speaker notes:
- Anyone who has shipped kiosk software has hit the webcam-track leak. Naming it makes the audience nod.
- The state machine point shows you take UI correctness as seriously as ML correctness.
-->

---

## Iris pipeline — Worldcoin's `open-iris`

```
Decode → Segment (ONNX) → Normalise (polar) → Encode (Gabor) → Match (HD)
```

Output: 2,048-bit binary iris code + mask of unreliable bits.

Match: masked fractional Hamming distance.
- HD = 0.0 → identical
- HD ≈ 0.5 → statistical independence
- TANIK threshold: 0.37 (configurable)

Threadpool-offloaded so FastAPI's event loop never blocks on Gabor convolution.

<!--
Speaker notes:
- This is the Daugman pipeline, which the audience will recognise. Call it that if anyone asks.
- The threadpool point is small but technically important — async-Python newcomers consistently miss it.
-->

---

## Fingerprint pipeline — SourceAFIS via JPype

```
Decode (JVM) → Detect minutiae → Build template (CBOR) → Match (similarity)
```

JVM is single-per-process (JPype enforces). Started lazily, reused for the lifetime of the inference process. Lines up with FastAPI's single-worker-per-pod model.

Threshold: 40.0 (SourceAFIS's documented FMR=0.01%). Score is open-ended; typical strong matches are in the hundreds.

<!--
Speaker notes:
- JPype + JVM is the unusual choice. Mention that the alternative was a Python fingerprint library, but SourceAFIS is much better tested and is the only credible open-source option for production-grade matching.
- The single-JVM-per-process constraint matches FastAPI's recommended deployment model — it's a constraint, not a problem.
-->

---

## Modality-agnostic engine + storage

Both engines satisfy a single Protocol:

```python
class BiometricEngine(Protocol):
    name: str
    def template_version(self) -> str: ...
    async def encode(self, image_bytes: bytes, **kwargs) -> Tuple[Optional[bytes], Optional[str]]: ...
    async def match(self, probe: bytes, gallery: bytes) -> float: ...
```

Templates cross the boundary as opaque `bytes`. Storage records the modality + template_version per subject. **Adding a third modality is a one-file change at the engine layer.**

<!--
Speaker notes:
- The seam matters. A biometric system that grows from one modality to two without a clean abstraction tends to grow ugly. The Protocol shows you thought about this from the start.
- Storage is keyed by (subject_id, modality) — one human enrolling both modalities produces two subject rows. Cross-modality linking is deferred (Phase 4 admin decision).
-->

---

## The interesting bit: score-level fusion

Two engines speak different languages:

- Iris: Hamming distance, **lower is better**, range [0, 1]
- Fingerprint: SourceAFIS similarity, **higher is better**, open-ended

Fusion needs a common scale — both onto [0, 1] where 0 = no match, 1 = perfect match.

<!--
Speaker notes:
- This is the "interesting twist" of the deck. Set it up here so the next slide can deliver the unconventional choice.
- Pause and let the audience think about how they would do this; then move on.
-->

---

## Piecewise-linear, anchored at the threshold

```
Iris (lower=better)         Fingerprint (higher=better)
  HD=0   → 1.0                score=0    → 0.0
  HD=thr → 0.5                score=thr  → 0.5
  HD=ceil→ 0.0                score=ceil → 1.0
```

The per-modality threshold is the only number on each native scale we already trust. So we **anchor to it**: engine-native threshold maps to normalised 0.5.

Fused decision threshold of 0.5 means "both modalities sitting right at their per-modality operating point."

<!--
Speaker notes:
- This is unconventional — the standard approaches are min-max, z-score, or fitted logistic. Worth explaining why this beats them in the early phase: min-max needs arbitrary endpoints; z-score and logistic both need a calibration set you may not have yet.
- The anchor at the threshold is the property that makes the fused threshold semantic clean.
-->

---

## The honest twist

Today: I don't have measured FAR/FRR. I'm waiting on a license for ND-IRIS-0405 and an FVC-style fingerprint dataset.

So the API responds honestly:

```json
{
  "matched": true,
  "fused_score": 0.78,
  "threshold": 0.5,
  "calibration_status": "placeholder",
  "calibration_reference": "docs/fusion.md"
}
```

`calibration_status: "placeholder"` is the system telling you, **in-band**, that its weights aren't tuned. A downstream consumer that needs measured FAR/FRR refuses a placeholder response.

<!--
Speaker notes:
- This is the slide that lands the credibility argument. The audience sees it and thinks "OK, this person isn't bullshitting."
- Optional: tell the story of how the placeholder field came about — it was a deliberate choice to avoid the temptation of shipping invented numbers.
-->

---

## The honesty discipline

Encoded in CLAUDE.md and enforced by convention:

- **No invented FAR/FRR.** "TBD — awaiting evaluation" beats "1 in a million" every time.
- **No overclaiming on liveness.** Phase 4 PAD is a *basic* defence. Real iris-PAD needs NIR multi-spectral hardware.
- **Accurate privacy claims.** Templates *are* personal data under KVKK/GDPR. "Zero-knowledge" is the wrong phrase.
- **Proper attribution.** Worldcoin, SourceAFIS, ND CVRL, NIST MINEX — all credited.

Every claim has a verification path. That's what differentiates a serious reference from a demo.

<!--
Speaker notes:
- The four bullets here are the load-bearing ones. Read them aloud; they are the "why TANIK is different" pitch.
- The privacy precision matters: "templates are personal data, zero-knowledge is the wrong phrase" is a phrase a Proline engineer will appreciate. It signals you've actually read the regulations.
-->

---

## Threat model — what's defended

- **Templates only, no raw image persistence.** Enforced by absence — `grep` finds no `.save()` against upload bytes.
- **MIME sniffing, not header trust.** Magic-byte validation via `filetype`.
- **Pydantic-strict request models.** Malformed payloads rejected before OpenCV sees them.
- **No telemetry, no analytics, no third-party calls.** Privacy posture is load-bearing.
- **Cross-modality lookups deliberately invisible.** A probing client cannot distinguish "exists in another modality" from "does not exist."

<!--
Speaker notes:
- These are the things that are already done, today. Each one is technically falsifiable — anyone can read the code and check.
- The "enforced by absence" framing is unusual and worth pausing on. It's a stronger claim than "we don't write images" because it can be verified by grepping.
-->

---

## Threat model — what's NOT defended (yet)

- **No liveness gate.** A printed photo of an enrolled iris currently matches. Phase 4.
- **No replay resistance.** No session nonces yet. Phase 4+.
- **No template encryption at rest.** Plaintext SQLite. Productionisation work.
- **No authentication.** Single-deployment, no users.

Documented attack-by-attack in `docs/threat-model.md` with concrete mitigation paths.

<!--
Speaker notes:
- Saying this out loud, on a slide, is the part that wins trust with biometric-industry engineers. They've all seen demos that pretend these gaps aren't there.
- The Phase 4 PAD module will close the first gap; the others are explicit productionisation work.
-->

---

## Privacy posture — KVKK + GDPR

- Biometric data is **special category** under both regimes.
- Lawful basis: **explicit consent** (KVKK Art. 6 §3, GDPR Art. 9(2)(a)).
- Data minimisation: raw images live in request-scoped memory only; never written to disk.
- Templates are stored — and templates *are* personal data. Use precise language.
- Subject rights (access, rectification, erasure, portability): admin endpoint lands in Phase 4.

`docs/privacy.md` enumerates every data category with retention + jurisdiction handling.

<!--
Speaker notes:
- For a Turkish audience, KVKK first then GDPR. For an EU audience, swap. The text is the same; the order signals familiarity with the audience's home regulator.
- The "templates are personal data" precision is repeated for emphasis — it's the most common compliance misframing.
-->

---

## Where it stands

| Phase | Status |
|---|---|
| 0 — Iris spike notebook | ✅ |
| 1 — Iris backend + minimal client | ✅ implementation; ⏳ deploy |
| 2 — Fingerprint modality | ✅ |
| 3 — Fusion, thresholds, honest metrics | ✅ #41 endpoint; ⏳ #42, #43 dataset-blocked |
| 4 — Liveness (PAD) + admin | ⏳ |
| 5 — Polish + release | ⏳ |

Phase-gate discipline: phases ship before the next starts. Scope creep killed every previous side project; this one's protected.

<!--
Speaker notes:
- The phase table is honest. Don't gloss over the deferred items.
- The "scope creep killed every previous side project" line is personal but humanising — it's a useful confession.
-->

---

## Production gap (the candid version)

| Concern | TANIK today | Production reality |
|---|---|---|
| Capture hardware | Webcam | Certified NIR iris camera, FAP-30+ fingerprint reader |
| Liveness | None (Phase 4 adds basic) | NIR multi-spectral; capacitive + sweat-pore detection |
| Template storage | Plaintext SQLite | AES-256, HSM-backed keys, ISO/IEC 24745 |
| Operator surface | None (Phase 4 adds) | OIDC + RBAC + audit trail |
| Network | Local | Private subnet, TLS terminator, WAF |

The architecture is *deliberately friendly* to those upgrades. The `BiometricEngine` Protocol means swapping `iris_engine` for a vendor SDK is one file.

<!--
Speaker notes:
- This is the slide that says "I know this isn't a production deployment, and I know what would need to change for it to be." The biometric-industry audience cares deeply that you have this calibration.
- Each row maps to a specific BACKLOG entry or a specific ROADMAP phase. None of this is hand-waved.
-->

---

## What I'd love feedback on

- **The fusion methodology.** Piecewise-linear-anchored-at-threshold is unconventional. Where does the field disagree with this in early-calibration phase?
- **The threat model.** What attack haven't I enumerated?
- **The honesty discipline.** "Every claim has a verification path or a TBD label" — does that land with engineers in regulated identity, or does it read as posturing?

Repo: github.com/Ayberkone/tanik · MIT · issues + PRs welcome

<!--
Speaker notes:
- Three concrete questions invite real engagement. "Let me know what you think" is too generic.
- Have a printed copy of OWNER-ACTIONS.md or docs/architecture.md ready to hand a Proline engineer who wants to dig in immediately.
-->

---

## References — for after the talk

- `docs/architecture.md` — top-to-bottom system walkthrough
- `docs/fusion.md` — score normalisation + fusion methodology
- `docs/threat-model.md` — full attack-by-attack table
- `docs/privacy.md` — KVKK + GDPR posture
- `docs/glossary.md` — biometrics vocabulary

External:
- Daugman (2004) — *How iris recognition works.* IEEE TCSVT.
- Ross & Jain (2003) — *Information fusion in biometrics.* PRL.
- ISO/IEC 30107 — PAD framework.
- NIST IREX X — `pages.nist.gov/IREX10/`

<!--
Speaker notes:
- Final slide is intentionally a reading list. Lets engaged listeners take it home and dig.
- Stay on this slide during Q&A so the URLs are visible.
-->
