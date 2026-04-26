# TANIK in the landscape — comparison and positioning

How TANIK relates to commercial biometric systems and to other open-source iris and fingerprint efforts. The honest answer in every direction.

> This document exists for three audiences:
> - **An operator evaluating biometric options.** "Should we use TANIK or buy a commercial system?"
> - **An academic reader positioning TANIK in the literature.** "Where does this fit?"
> - **The Proline-style biometrics-industry engineer.** "What is this versus what we already build?"

---

## 1. The honest top-line

TANIK is not commercially competitive. It is not trying to be. It is a **reference implementation** that is intentionally smaller in scope than a productionised system, but built to the same architectural and honesty standards as a system intended for deployment.

The right comparison is not "TANIK vs Suprema BioStation" — it is "TANIK vs the median biometric demo project on GitHub." On that axis, TANIK is meaningfully better; on the productionised-system axis, it is meaningfully behind, and the gap is documented in `docs/threat-model.md` §6 ("What a production deployment would add").

---

## 2. TANIK vs commercial biometric systems

### Suprema (Korea), IDEMIA (France), NEC (Japan) — the major vendors

| Concern | TANIK today | Commercial vendor |
|---|---|---|
| Capture hardware | Webcam (iris); upload-only (fingerprint) | Certified NIR iris cameras (e.g. Suprema BioStation, IrisGuard); FAP-30+ fingerprint readers |
| Liveness | None today (Phase 4 adds basic) | NIR multi-spectral; capacitive sweat-pore detection; vein imaging on premium tiers |
| Matching algorithm | Worldcoin `open-iris` + SourceAFIS | Proprietary; tuned over multi-decade lifecycles; consistently top of NIST IREX / MINEX leaderboards |
| Throughput | Single Python process; no benchmarks yet | Tens to hundreds of req/s per node; horizontally scalable |
| Template storage | Plaintext SQLite | HSM-backed; ISO/IEC 24745 template protection schemes; vendor-specific encrypted formats |
| Operator surface | None today (Phase 4 adds basic) | Full RBAC, audit, multi-tenant, SDK + REST + on-device deployments |
| Compliance posture | Architectural building blocks; deployment-side work documented | KVKK / GDPR / FIPS 140-3 certifications; vendor-managed compliance overhead |
| Cost | Free (MIT) | Five-to-six figures USD per node + ongoing licensing |
| Reproducibility | Whole stack open-source; reads the same on every host | Vendor-managed binary blobs; behaviour locked by support contract |

**Where TANIK wins:** transparency, reproducibility, cost (it is free and modifiable), and education value. An engineer can read the entire matching path end-to-end in an afternoon.

**Where vendors win:** every accuracy and operational metric. Decades of tuning, certified hardware, certified compliance posture, and operational maturity that no weekend project can match.

**The honest pitch:** TANIK is not a Suprema replacement. It is what you build to *understand* what Suprema is doing well enough to evaluate them. A Proline engineer using TANIK to calibrate their expectations of an open-source / standards-based equivalent is exactly the use case.

### Worldcoin's deployment

Worldcoin (the cryptocurrency project) operates a worldwide network of "Orb" iris-capture devices using their `open-iris` pipeline — the same one TANIK uses. Their Orb hardware is custom NIR-illuminated; their backend processes hundreds of thousands of enrolments. Their operating posture is dramatically different from a kiosk system (their deployment is global, distributed, and uses their open-iris pipeline at scale that no other open-source project comes close to).

TANIK and Worldcoin's deployment share the iris matcher and nothing else.

---

## 3. TANIK vs other open-source iris recognition

### `worldcoin/open-iris` itself

TANIK *uses* `open-iris`. The relationship is not a competition: TANIK is a system *built on* `open-iris`'s pipeline. Worldcoin contributed the segmentation model, the Daugman-style normalisation, the iris code generator, and the masked Hamming distance matcher. TANIK adds: an HTTP API, request validation, persistence, the modality-agnostic seam, score fusion with fingerprint, and the honesty-discipline framework around it.

If you want to *understand* iris matching from first principles, read `open-iris` directly. If you want to see how a system *uses* iris matching as one component, read TANIK.

### CVRL OpenSourceIrisRecognition (TripletIris + ArcIris)

The University of Notre Dame's Computer Vision Research Lab maintains <https://github.com/CVRL/OpenSourceIrisRecognition>, which contains two iris matchers: **TripletIris** (triplet-loss-trained convolutional) and **ArcIris** (ArcFace-loss-trained). These are the **only two NIST IREX X-leaderboarded open-source iris recognition algorithms**, and they ranked competitively against commercial submissions (entries `ndcvrl_001` and `ndcvrl_002`; <https://pages.nist.gov/IREX10/>).

**Why TANIK uses `open-iris` instead today:**

- `open-iris` is a complete pipeline (segmentation + normalisation + encoding + matching). The CVRL repo is matchers; you'd need to bring your own segmentation.
- `open-iris` is the only one with publicly available pre-trained models via PyPI install. CVRL's repo requires more setup.
- Phase scope: CLAUDE.md forbids new ML dependencies beyond `open-iris` and SourceAFIS in the first three phases. Adding TripletIris/ArcIris would be Phase 3.5+ work.

**Why integrating TripletIris and ArcIris is captured in BACKLOG:**

The most credible Phase 5 / Phase 6 comparative study TANIK could run is a side-by-side: `open-iris` vs TripletIris vs ArcIris on the same held-out test set (ND-IRIS-0405). Three matchers behind one `BiometricEngine` interface, with measured FAR/FRR per matcher and a discussion of where they agree and disagree. That kind of NIST-style, honestly-reported comparison is what biometrics-industry engineers actually find compelling — and the CVRL algorithms are the right comparison targets because they are the only open-source algorithms NIST has independently leaderboarded.

This is captured in `BACKLOG.md` ("Notre Dame CVRL open-source iris algorithms — comparison + dual-engine angle") with the explicit note that it is post-Phase-3 work; the dataset (ND-IRIS-0405) is the prerequisite.

### Other open-source iris efforts

- **OpenCV's `iris` sample.** Educational; not a maintained matcher.
- **USIT (University of Salzburg Iris Toolkit).** A research toolkit with multiple algorithms; permission-restricted.
- Various academic GitHub repositories implementing single papers. Useful for understanding methodology; rarely production-ready.

The pattern is that open-source iris recognition is dominated by *research toolkits* (educational; not deployment-ready) and *research papers* (single algorithm; no system around it). TANIK's contribution is the *system around* a research-grade matcher — the API, validation, fusion, threat model, honesty discipline.

---

## 4. TANIK vs other open-source fingerprint

### SourceAFIS

TANIK uses SourceAFIS. Same relationship as with `open-iris` — TANIK is the system, SourceAFIS is the matcher. SourceAFIS is widely regarded as the best open-source fingerprint matcher; the alternatives are largely research-grade or wrappers around proprietary code.

SourceAFIS authors themselves benchmark against the FVC datasets and publish documented FMR / FNMR numbers. TANIK inherits this credibility without claiming it as its own work.

### NIST FIS / NBIS (NIST Biometric Image Software)

A C codebase from NIST containing fingerprint segmentation, classification, and matching components. Public domain; less actively maintained than SourceAFIS; Java/Python bindings are non-trivial. SourceAFIS is the simpler choice for new projects.

### OpenBR (Open Biometric Recognition)

A C++ framework with multiple modalities (face primary, fingerprint secondary). Cited but largely inactive. Not a current contender.

### MCC (Minutia Cylinder-Code) and related research implementations

Research-grade matchers documented in the literature. Available as research code; not as a production-ready library. Useful as a comparison target if Phase 5 wants to do a multi-matcher fingerprint study.

---

## 5. TANIK vs face-recognition-only systems

A common comparison the audience may make: *"How does this compare to FaceNet / DeepFace / face_recognition.py / X face vendor?"*

The honest answer: **it does not, on purpose.** TANIK does not include face recognition for deliberate reasons documented in `docs/architecture.md` §2:

- Face has the highest presentation-attack surface of mainstream modalities.
- The EU AI Act heavily restricts remote real-time biometric identification, of which face is the canonical example.
- Adding face would dilute the "this is a serious biometric system" credibility argument; demo face systems are everywhere and easy to dismiss.

Some deployments genuinely need face — phone unlock, social platform identity proofing — and those should use vendor solutions or specifically-tuned open-source efforts. TANIK's scope is iris + fingerprint, deliberately.

---

## 6. TANIK vs other "honest reference" projects

### `signatesinaai/iris-recognition` and similar GitHub demos

The pattern TANIK was built to push against. Quoted accuracy numbers without test sets, claimed liveness without published models, no threat model. The whole point of TANIK is to occupy this niche with a project that does not have those failure modes.

### Stanford Biometrics Group / academic system papers

System papers (a working system documented in a paper) are rare in academic biometrics — most papers are algorithm papers. The few system papers tend to be tied to specific deployments (e.g. India's Aadhaar, which is documented in the academic literature but not open-source). TANIK is the system *implementation* equivalent of those papers, with the source code available.

---

## 7. Where TANIK is genuinely positioned

The accurate framing for an outside reader:

> **TANIK is a credible, MIT-licensed reference implementation of a multi-modal biometric kiosk, built to demonstrate honest engineering practice in the biometrics domain. It is suitable for: educational use, evaluation of open-source matcher quality, and as a starting point for organisations that want to understand multi-modal fusion before commissioning a productionised system. It is not suitable for: drop-in production deployment in a high-security setting, or as a replacement for a certified vendor system.**

That sentence appears in this exact form on the README and in any outreach document, so the framing is consistent across surfaces.

---

## 8. The post-Phase-3 comparative study

When Phase 3 closes (FAR/FRR ship) and the ND-IRIS-0405 dataset is in hand, the most valuable single piece of work TANIK could publish is the **TANIK vs TripletIris vs ArcIris** comparative study described in BACKLOG. Three matchers, one held-out test set, transparent methodology, every number reproducible.

That is the artefact that turns the project from "well-engineered demo" into "useful biometric-industry contribution." This document exists in part to put that study on the road map even though it is past the current scope.

---

## References

- Worldcoin `open-iris` — <https://github.com/worldcoin/open-iris>
- CVRL OpenSourceIrisRecognition — <https://github.com/CVRL/OpenSourceIrisRecognition>
- SourceAFIS — <https://sourceafis.machinezoo.com/>
- NIST IREX X — <https://pages.nist.gov/IREX10/>
- NIST MINEX III — <https://github.com/usnistgov/minex/tree/master/minexiii>
- BACKLOG entries: "Notre Dame CVRL open-source iris algorithms — comparison + dual-engine angle"; "Fingerprint dataset gap for Phase 3 — same-finger pairs"
