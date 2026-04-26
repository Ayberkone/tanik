# TANIK — presentation attack detection (PAD) plan (skeleton, Phase 4)

This document describes the planned PAD ("liveness") gate for Phase 4 — *what* it will do, *what it will not do*, and the public datasets and approaches under consideration. It exists today (Phase 3) as a skeleton so that the threat model in `docs/threat-model.md` and the API contract in `docs/api-contract.md` (which already reserves the `PAD_FAILURE` error code) have a forward-pointing reference.

> **Status:** skeleton. The exact model + dataset choice is still open and will be decided during Phase 4. This document captures the framework so the implementation slots into a known shape.

---

## 1. What PAD is, briefly

A **presentation attack** is any attempt to spoof a biometric system by presenting an artefact instead of a live human — the canonical examples being a printed photo of an iris, a high-resolution screen replay, a silicone fingerprint cast, or a contact lens with an iris pattern printed on it.

**PAD** ("presentation attack detection," sometimes called "liveness") is the gate that runs *before* the biometric pipeline and answers "is this presentation from a live, unaltered human?" If PAD fails, the biometric pipeline does not run and the system returns a structured rejection.

The terminology, error rates, and reporting requirements are codified in **ISO/IEC 30107**:

- **APCER** (Attack Presentation Classification Error Rate): the proportion of attacks the PAD let through. Lower is better.
- **BPCER** (Bona-fide Presentation Classification Error Rate): the proportion of legitimate users the PAD wrongly rejected. Lower is better.

Like FAR and FRR, APCER and BPCER trade off; the operating point depends on whether the deployment cares more about preventing spoofs (lean APCER-low, accept some BPCER) or about not annoying users (lean BPCER-low, accept some APCER).

## 2. Scope of v1 PAD

The Phase 4 PAD module will be a **basic image-domain detector**. Concretely:

- It will examine the same image that the iris pipeline (or fingerprint pipeline) is about to process.
- It will look for cues that distinguish a live presentation from a printed photo, screen replay, or simple contact lens — moiré patterns, colour artefacts, focus inconsistencies, specular reflections in unrealistic positions.
- It will produce a single PAD score in `[0, 1]` and a binary pass/fail against a configurable threshold.

**What v1 PAD will NOT do — call this in plain language:**

- It will not stop a determined attacker with **NIR-capable replay equipment**. Real iris-PAD relies on multi-spectral NIR features that are not available from a regular RGB webcam.
- It will not stop **realistic patterned contact lenses** that mimic iris texture. State-of-the-art iris-PAD against this attack uses domain-specific deep learning trained on dedicated datasets (NDIris3D, LivDet-Iris, CASIA-Iris-Fake) plus, ideally, NIR sensors.
- It will not stop **gummy or silicone fingerprint** spoofs in software alone. State-of-the-art fingerprint-PAD for high-quality spoofs is hardware-based: capacitive sensing, sweat-pore detection, ultrasonic fingerprint scanning. Software-only fingerprint-PAD against good spoofs has APCER in the high single digits at best.

This is a **basic defence**, not "military grade." The honesty discipline (CLAUDE.md, README, `docs/threat-model.md`) requires saying so explicitly.

## 3. Candidate datasets (open / academically licensable)

For training and/or evaluation. Selection happens in Phase 4 once licensing is verified.

| Dataset | Modality | Bona-fide / attack types | License | Notes |
|---|---|---|---|---|
| **NDIris3D** | Iris | Live + 3D-printed iris attacks | ND CVRL — same license route as ND-IRIS-0405 | Strong candidate; same institutional license process as `docs/nd-iris-0405-access.md` |
| **CASIA-Iris-Fake** | Iris | Live + printed-photo + contact-lens attacks | CASIA — request-based | Older but well-cited |
| **LivDet-Iris** (annual competition series) | Iris | Mixed attack types per year (LivDet-Iris-2017 / 2020 / 2023) | Per-edition | Useful as a *test* set even if we train on something else |
| **LivDet-Fingerprint** (annual competition series) | Fingerprint | Gummy / silicone / latex spoofs across multiple sensors | Per-edition | If Phase 4 includes fingerprint-PAD; software-only constraints noted above |

Phase 4 must verify the license terms at acquisition time and document the chosen dataset(s) in `docs/datasets.md`, the same way Phase 2 documented MINEX III.

## 4. Candidate approaches

In rough order of complexity vs. effectiveness:

1. **Image quality + colour-space heuristics.** Cheap; catches the most naive attacks (very obvious printed photos, low-quality screen replays). Will not generalise to high-quality attacks. Useful as a fast first-pass filter even alongside a learned model.
2. **A small CNN trained on a public PAD dataset.** The most likely v1 choice — a MobileNet-class classifier trained on NDIris3D or CASIA-Iris-Fake, exported to ONNX, run inline on the inference host. Documented APCER/BPCER on the training set's held-out split goes in `docs/performance.md` alongside the FAR/FRR numbers.
3. **A fine-tuned vision foundation model.** Higher accuracy ceiling, larger compute footprint per inference. Probably overkill for v1; consider if v1 misses real attacks that the training set didn't cover.
4. **Frequency-domain analysis** (FFT artefacts from screen pixel grids, moiré detection). Good complement to learning-based approaches; cheap.

The architectural slot for the PAD model is independent of the choice — it lives behind a single function call inside the route handler, before `engine.encode(...)` is invoked.

## 5. API surface

The error code is already reserved (`apps/inference/tanik_inference/errors.py`):

```python
class ErrorCode(str, Enum):
    ...
    PAD_FAILURE = "PAD_FAILURE"
```

The API contract reservation is in `docs/api-contract.md`:

> | 503 | `PAD_FAILURE` | Reserved for Phase 4. Not emitted in v1 |

When Phase 4 lands, the response shape on a PAD failure will be:

```json
{
  "request_id": "...",
  "error_code": "PAD_FAILURE",
  "message": "Presentation attack detected; biometric pipeline not run.",
  "details": {
    "pad_score": 0.91,
    "threshold": 0.5,
    "modality": "iris"
  }
}
```

`pad_score` is the model's attack probability (`0` = bona-fide, `1` = attack); `threshold` is server-configured (env var, e.g. `TANIK_IRIS_PAD_THRESHOLD`).

For successful (bona-fide) verifications, the verify response will gain an optional `pad` block:

```json
{
  ...,
  "pad": {
    "score": 0.04,
    "threshold": 0.5
  }
}
```

— so an operator dashboard can surface aggregate PAD scores over time.

## 6. Evaluation reporting

`docs/performance.md` (Phase 3 #43) will publish FAR and FRR for the biometric matching. When Phase 4 PAD lands, the same document gains:

- **APCER** on the held-out PAD test set (per attack type if the dataset distinguishes them).
- **BPCER** on the bona-fide split.
- A short ROC-style curve for PAD threshold selection.
- A statement of the dataset(s), the train/test split, and the model architecture.

Like the matching numbers, **no PAD numbers appear anywhere until they have been measured.** "TBD — awaiting Phase 4 evaluation" is acceptable; an invented APCER is not.

## 7. The honest scope statement (for the README and outreach material)

When Phase 4 ships, the README and `docs/architecture.md` will gain a one-paragraph version of the following:

> TANIK includes a basic presentation-attack detector trained on \[dataset(s)]. It defends against printed-photo and screen-replay attacks of the kind that catch most demo biometric systems. It does *not* defend against NIR-capable replay equipment, realistic patterned contact lenses, or high-quality silicone fingerprint spoofs — defending against those requires multi-spectral NIR sensors (for iris) or capacitive / sweat-pore sensing hardware (for fingerprint), neither of which this software-only system has. APCER and BPCER on \[test set] are reported in `docs/performance.md`.

Saying this in plain language is more credible than saying "PAD-protected" without qualification.

## 8. References

- ISO/IEC 30107-1 (Framework), 30107-2 (Data formats), 30107-3 (Testing and reporting). The standard reference for PAD terminology and error rates.
- Czajka, A. & Bowyer, K. (2018). *Presentation attack detection for iris recognition: An assessment of the state-of-the-art.* ACM Computing Surveys.
- Marcel, S., Nixon, M.S., Fierrez, J., Evans, N. (eds.) (2019). *Handbook of Biometric Anti-Spoofing.* Springer. The single most useful reference for both the iris and fingerprint sides; covers attack taxonomies, datasets, and defence approaches comprehensively.
- LivDet competitions: <https://livdet.org/>. Per-edition results give a realistic upper bound on what software-only PAD achieves.
