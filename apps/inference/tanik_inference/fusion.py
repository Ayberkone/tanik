"""Score normalisation + weighted-sum fusion.

Each engine reports a score in its own native scale (iris: fractional Hamming
distance, lower is better; fingerprint: SourceAFIS similarity, higher is
better, open-ended). To fuse them we map both onto a common ``[0, 1]`` scale
where ``0 = no match`` and ``1 = perfect match``.

The normalisation is **piecewise-linear, anchored at the per-modality
operating threshold**: an engine-native score equal to its threshold maps to
a normalised score of exactly ``0.5``. This makes the fused decision
threshold of ``0.5`` mean "both modalities sitting right at their per-modality
operating point" — and the fused score moves up or down from there as either
modality's evidence strengthens or weakens. The shape:

* Iris (``score = HD``, lower is better):
    HD ≤ floor → 1.0
    HD = threshold → 0.5  (linear between floor and threshold)
    HD ≥ ceil → 0.0       (linear between threshold and ceil)

* Fingerprint (``score`` higher is better):
    score ≤ 0 → 0.0
    score = threshold → 0.5  (linear between 0 and threshold)
    score ≥ ceil → 1.0       (linear between threshold and ceil)

The floors and ceilings are configured via environment (see ``config.py``);
their default values are documented in ``docs/fusion.md`` as placeholders
that will be re-derived from a calibration set in Phase 3 #43. They are
*not* tuned numbers and must not be reported as such.

Fusion is a weighted sum across whichever modalities the request actually
supplied, with weights renormalised over the present modalities (so a
single-modality unified call reduces cleanly to that modality's normalised
score).
"""

from typing import Dict


def normalise_iris(hd: float, *, floor: float, threshold: float, ceil: float) -> float:
    if not (floor < threshold < ceil):
        raise ValueError(
            f"iris normalisation requires floor < threshold < ceil; got "
            f"floor={floor}, threshold={threshold}, ceil={ceil}"
        )
    if hd <= floor:
        return 1.0
    if hd >= ceil:
        return 0.0
    if hd <= threshold:
        return 1.0 - 0.5 * (hd - floor) / (threshold - floor)
    return 0.5 - 0.5 * (hd - threshold) / (ceil - threshold)


def normalise_fingerprint(score: float, *, threshold: float, ceil: float) -> float:
    if not (0 < threshold < ceil):
        raise ValueError(
            f"fingerprint normalisation requires 0 < threshold < ceil; got "
            f"threshold={threshold}, ceil={ceil}"
        )
    if score <= 0:
        return 0.0
    if score >= ceil:
        return 1.0
    if score <= threshold:
        return 0.5 * score / threshold
    return 0.5 + 0.5 * (score - threshold) / (ceil - threshold)


def fuse(normalised_scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """Weighted sum across the modalities present in ``normalised_scores``.

    Weights are renormalised over present modalities, so a single-modality
    call falls through to that modality's normalised score and does not get
    halved by the absent modality's weight.
    """
    if not normalised_scores:
        raise ValueError("fuse() requires at least one modality")
    relevant = {m: weights[m] for m in normalised_scores if m in weights}
    total = sum(relevant.values())
    if total <= 0:
        raise ValueError(f"sum of relevant weights must be positive; got {relevant}")
    return sum(normalised_scores[m] * (relevant[m] / total) for m in normalised_scores)
