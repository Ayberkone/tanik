# Fusion methodology — TANIK

This document describes how TANIK turns iris and fingerprint scores into a single fused decision in the unified `POST /api/v1/verify` endpoint.

> **Honesty notice — placeholder calibration.** The weights and normalisation knobs documented here are *not* tuned. They are honest defaults chosen so the system runs end-to-end. Real calibration is gated on Phase 3 dataset acquisition (ND-IRIS-0405 for iris, FVC-style same-finger pairs for fingerprint — see `BACKLOG.md`) and will land with the evaluation harness in Phase 3 task #43. Until then, every unified-verify response carries `calibration_status: "placeholder"`. A consumer that needs measured FAR/FRR must refuse a placeholder response.

---

## The two engines speak different languages

| Engine | Score | Direction | Range |
|---|---|---|---|
| Iris (Worldcoin `open-iris`) | masked fractional Hamming distance | lower = better match | `[0, 1]` (well below 0.5 in practice) |
| Fingerprint (SourceAFIS) | similarity | higher = better match | `[0, ∞)` (typical strong matches: hundreds) |

Fusion needs a common scale. We map both onto `[0, 1]` where `0 = no match`, `1 = perfect match`.

## Normalisation — piecewise-linear, anchored at the per-modality threshold

Each modality already has a documented per-modality decision threshold (see `docs/api-contract.md`):

- Iris: `TANIK_IRIS_MATCH_THRESHOLD`, default `0.37`. A Hamming distance below this is a per-modality match.
- Fingerprint: `TANIK_FINGERPRINT_MATCH_THRESHOLD`, default `40.0`. A SourceAFIS similarity at or above this is a per-modality match. SourceAFIS itself documents 40 as FMR=0.01% — see <https://sourceafis.machinezoo.com/threshold>.

We normalise so that **the engine-native threshold maps to a normalised score of exactly `0.5`**. That gives the fused decision threshold of `0.5` a clear semantic: "both modalities are sitting right at their per-modality operating point." A normalised score above `0.5` means the modality's evidence is stronger than its operating point; below `0.5` means weaker.

The shape is piecewise-linear, controlled by a floor and a ceiling per modality:

### Iris (lower-is-better, `floor → 1.0`, `ceil → 0.0`)

```
HD ≤ floor       → 1.0
floor < HD ≤ thr → 1.0 - 0.5 · (HD - floor) / (thr - floor)
thr < HD < ceil  → 0.5 - 0.5 · (HD - thr)   / (ceil - thr)
HD ≥ ceil        → 0.0
```

Defaults: `TANIK_IRIS_HD_FLOOR=0.0` (best-possible Hamming distance), `TANIK_IRIS_HD_CEIL=0.5` (statistical independence — two random iris codes converge on ~0.5).

### Fingerprint (higher-is-better, `0 → 0.0`, `ceil → 1.0`)

```
score ≤ 0          → 0.0
0 < score ≤ thr    → 0.5 · score / thr
thr < score < ceil → 0.5 + 0.5 · (score - thr) / (ceil - thr)
score ≥ ceil       → 1.0
```

Default: `TANIK_FINGERPRINT_SCORE_CEIL=200.0`. SourceAFIS scores are open-ended; 200 is a generous "strong match" anchor. Self-matches on the MINEX III validation set we use in tests routinely score in the 200-400 range, so the ceiling clamps strong matches to 1.0 rather than letting the normalised scale reflect outlier-large numbers.

## Fusion — weighted sum over present modalities

```
fused = Σ_m weight_m_relative · normalised_m

where weight_m_relative = weight_m / Σ_(modalities present in this request) weight_k
```

Weights are renormalised over **the modalities the request actually supplied**. If only iris is supplied, the iris weight effectively becomes `1.0` and the fused score equals the iris normalised score. The same holds for fingerprint-only.

Defaults: `TANIK_FUSION_IRIS_WEIGHT=0.5`, `TANIK_FUSION_FINGERPRINT_WEIGHT=0.5` — equal weighting in the absence of evidence either way. Equal weights are not a claim that the two modalities are equally informative; they are the prior we hold until calibration says otherwise.

The fused decision: `matched = (fused ≥ TANIK_FUSION_DECISION_THRESHOLD)`, default `0.5`.

## Why this shape and not a logistic / z-score

Three options were on the table:

1. **Min-max from arbitrary endpoints** — easy, but the choice of endpoints is itself a judgement call, and the per-modality threshold has no special status on the normalised scale.
2. **Z-score against the calibration set's score distribution** — principled, but requires a calibration set we do not yet have.
3. **Piecewise-linear anchored at the operating threshold** — what we picked. The operating threshold is the only number on each scale we already trust, so we anchor to it. Once calibration data is in hand, option 2 becomes available; the anchor at the threshold remains a sensible sanity check on whatever curve we fit.

## What changes when calibration ships (Phase 3 #43)

When `tests/evaluation/` produces measured FAR/FRR on the held-out test set:

- Weights move from `0.5/0.5` to whatever maximises the test-set EER (or another documented criterion).
- Normalisation may shift from piecewise-linear to a fitted logistic if the data justifies it.
- `calibration_status` in the API response flips from `placeholder` to `calibrated`.
- `docs/performance.md` will publish the test-set composition, the calibration vs. evaluation split, the resulting weights, the fused FAR/FRR, and an ROC curve.

Until then, the unified endpoint is a working architectural seam, not a tuned matcher.

## References

- Daugman, J. — original Hamming-distance methodology for iris codes. The `~0.5` independence figure for normalised iris codes is a well-replicated empirical result from his work.
- SourceAFIS threshold guide — <https://sourceafis.machinezoo.com/threshold>.
- Ross, A. & Jain, A. K. (2003) — *Information fusion in biometrics*, Pattern Recognition Letters. The standard reference for score-level fusion taxonomy (sum-rule, weighted-sum, min/max), against which our weighted-sum approach is the simplest credible option.
