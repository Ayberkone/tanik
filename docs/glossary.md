# Glossary — biometrics terms used in TANIK

A working vocabulary for anyone reading the TANIK code or docs. Listed by category, alphabetical inside each section. Where a term has both a precise standards definition and a common informal usage, both are noted.

This document is **not** academic. It is a practical glossary aimed at someone who is software-fluent but new to biometrics — the audience the project is built for.

---

## Modalities and capture

**Behavioural biometric.** A biometric based on how a person *acts* rather than how they look — keystroke dynamics, gait, signature dynamics. Out of TANIK's scope.

**Bona-fide presentation.** ISO/IEC 30107 term for a legitimate biometric presentation by the actual person. The opposite of a *presentation attack*.

**Capacitive sensor.** A fingerprint sensor that measures the electrical capacitance of the ridge-and-valley pattern. Common in modern phones; meaningfully harder to spoof than optical sensors.

**Enrolment.** The first time a person presents to the system; the resulting template is stored as the *gallery* for future verifications.

**FAP (Fingerprint Acquisition Profile).** NIST scale describing the resolution and area covered by a fingerprint sensor. FAP30 (single-finger plain capture) and FAP60 (single-finger or palm with rolled-print capability) are the common kiosk-grade tiers.

**Gallery.** The stored template a probe is compared against. In TANIK, the gallery for `verify` is the row in `subjects` selected by `subject_id`.

**Modality.** One specific biometric channel (iris, fingerprint, face, voice). TANIK ships with two modalities; the engine layer is modality-agnostic so a third would not require API changes.

**NIR (near-infrared).** Light just outside the visible spectrum (~700–1000 nm). Iris recognition uses NIR illumination because iris texture is much sharper under NIR than under visible light, and because melanin in the iris is largely transparent to NIR — meaning a brown iris and a blue iris look comparably texture-rich. Webcam-based iris recognition (which TANIK supports today) gives up most of this advantage.

**Optical sensor.** A fingerprint sensor that captures a regular optical image of the finger. Cheaper than capacitive but easier to spoof with a printed pattern.

**Plain impression.** A fingerprint capture where the finger is simply placed on the sensor. Contrast with *rolled* (the finger is rolled side to side to capture more area) and *latent* (a fingerprint left at a crime scene; not a deliberate capture).

**Presentation attack.** Any attempt to spoof a biometric system by presenting an artefact — printed photo, screen replay, silicone fingerprint cast, contact lens with a printed iris pattern.

**Probe.** The fresh capture being compared against the gallery. In TANIK's `verify` endpoints, the uploaded image is the probe.

**Template.** The compact, matcher-readable representation of a biometric capture. For iris: the binary iris code (~2,048 bits) plus a mask of the unreliable bits. For fingerprint: a list of minutiae locations and orientations. **Templates are personal data** under KVKK and GDPR — see `docs/privacy.md`.

## Iris-specific

**Daugman, John.** The Cambridge researcher whose 1993 paper *"High confidence visual recognition of persons by a test of statistical independence"* defined the modern iris-recognition pipeline. The iris code, masked Hamming distance, and the use of Gabor filters all come from his work.

**Daugman normalisation.** Mapping the annular iris region (between pupil and limbus) onto a polar-coordinate rectangle so that all subsequent operations work on a fixed-shape matrix regardless of pupil dilation, rotation, etc.

**Gabor filter.** A bandpass filter that responds to sinusoidal patterns at a specific orientation and frequency. A bank of Gabor filters at multiple orientations and scales is what extracts the binary iris code from the normalised iris image.

**Hamming distance (HD).** The proportion of bits that differ between two binary strings. In iris recognition, the *fractional Hamming distance* is the proportion that differ ignoring the masked bits. HD = 0 means "every comparable bit identical." HD ≈ 0.5 is statistical independence — what two unrelated iris codes converge to.

**Iris code.** The binary template produced by Gabor filtering of the normalised iris image. In `open-iris`, the code is roughly 2,048 bits long, paired with a mask of the same length flagging unreliable bits (eyelids, eyelashes, specular reflections).

**Limbus.** The boundary between the iris and the white sclera. The outer edge of the iris.

**Segmentation.** The process of finding the iris and pupil boundaries in the input image. In `open-iris`, this is done by an ONNX-exported neural network.

## Fingerprint-specific

**Bifurcation.** A minutia where a ridge splits into two. One of the two minutia types matchers care about.

**ISO/IEC 19794-2.** The international standard for fingerprint minutiae template format. Defines a binary record format that is supposed to be interoperable across vendors — though in practice, vendor-specific extensions and quality differences mean genuine interoperability is rarer than the spec implies. SourceAFIS supports it; TANIK uses native CBOR templates internally for fidelity (BACKLOG entry covers ISO export).

**Latent print.** A fingerprint left on a surface (a glass, a doorknob) and lifted later. Different image properties from a deliberate capture; out of TANIK's scope.

**Minutia (plural minutiae).** A small distinctive feature in a fingerprint — a ridge ending or a bifurcation. Modern fingerprint matchers compare two templates by aligning their minutiae and scoring the correspondence.

**Ridge ending.** A minutia where a ridge stops. The other minutia type matchers track.

**Sweat-pore detection.** A liveness signal: real fingers have visible pores along the ridges, while silicone casts typically don't. State-of-the-art software fingerprint-PAD looks for this.

## Performance and evaluation

**APCER (Attack Presentation Classification Error Rate).** ISO/IEC 30107-3 metric: the proportion of *attacks* the PAD let through. Lower is better.

**AUC (Area Under the Curve).** The integrated ROC curve. AUC = 1.0 is perfect discrimination; AUC = 0.5 is random.

**BPCER (Bona-fide Presentation Classification Error Rate).** ISO/IEC 30107-3 metric: the proportion of *legitimate users* the PAD wrongly rejected. Lower is better. Trades off with APCER.

**Calibration set.** A held-out portion of the data used to *tune* the matcher's parameters (thresholds, weights). Disjoint from the evaluation set.

**EER (Equal Error Rate).** The threshold at which FAR = FRR. A common single-number summary of a matcher's performance, even though no real deployment runs at the EER (you usually want to push one error rate down at the cost of the other).

**Evaluation set.** A held-out portion of the data used only to *report* numbers, never to tune anything. Disjoint from the calibration set. The numbers in `docs/performance.md` will come from the evaluation set, not the calibration set.

**FAR (False Accept Rate).** The proportion of *impostor* pairs the matcher wrongly accepted as the same identity. Synonyms: FMR (False Match Rate). Lower is better.

**FMR / FNMR.** False Match Rate / False Non-Match Rate. Synonyms for FAR / FRR; the standards sometimes prefer these terms.

**FRR (False Reject Rate).** The proportion of *genuine* pairs the matcher wrongly rejected as different identities. Synonyms: FNMR. Lower is better.

**FPIR / FNIR.** False Positive Identification Rate / False Negative Identification Rate. The 1:N analogues of FAR/FRR, used for *identification* (find which subject this matches?) rather than *verification* (does this match the named subject?). TANIK is verification-only; FPIR/FNIR don't apply.

**Genuine pair.** A pair of biometric captures from the *same* identity. Should match if the matcher is working.

**Impostor pair.** A pair of captures from *different* identities. Should not match.

**ROC curve (Receiver Operating Characteristic).** A plot of FRR vs. FAR (or one minus FRR vs. FAR — both conventions exist) as the matcher's threshold varies. Lets you see the FAR/FRR tradeoff at every possible operating point in one figure.

**Threshold.** The numeric cutoff that converts a matcher's score into a binary decision. In TANIK: `TANIK_IRIS_MATCH_THRESHOLD` (HD < threshold → match), `TANIK_FINGERPRINT_MATCH_THRESHOLD` (score ≥ threshold → match), `TANIK_FUSION_DECISION_THRESHOLD` (fused ≥ threshold → match).

## Architecture concepts

**1:1 verification.** Confirming that a probe matches a *named* subject_id. Always returns one yes/no plus a score. TANIK's `verify` endpoints are 1:1.

**1:N identification.** Finding *which* subject (if any) a probe matches in a database of size N. Different cost profile; TANIK does not do this in v1.

**Decision-level fusion.** Combining the *yes/no decisions* of multiple matchers (e.g. AND, OR, majority vote). Coarse; loses information.

**Feature-level fusion.** Combining the *features* (templates) of multiple matchers before matching. Difficult in practice because templates from different modalities are not commensurable.

**Score-level fusion.** Combining the *scores* of multiple matchers and applying a single threshold to the combined score. The standard approach for multi-modal systems and what TANIK does — see `docs/fusion.md`.

**Sum rule, weighted sum, min/max, product rule.** The basic score-fusion combiners. TANIK uses weighted sum, anchored at the per-modality thresholds.

**Template aggregation.** Combining multiple captures of the same person into a single template (or a list of templates) for more reliable matching. Deferred in TANIK — each enrol creates one subject; re-enrolling the same person creates a new subject_id.

**Verification vs. identification.** Verification is "are you who you claim to be?" (1:1). Identification is "who are you?" (1:N). TANIK is verification-only.

## Standards bodies and programs

**ICAO 9303.** International Civil Aviation Organisation standard for machine-readable travel documents (passports). The reference for the iris and face templates that go into ePassports. Out of TANIK's current scope; relevant if TANIK ever shipped a "validate against an ePassport" flow.

**IREX.** NIST Iris Exchange — a long-running benchmark series for iris recognition algorithms. The ND CVRL TripletIris and ArcIris algorithms appear on the IREX X leaderboard at <https://pages.nist.gov/IREX10/>.

**ISO/IEC 19794.** International family of standards for biometric data interchange formats. -2 is fingerprint minutiae; -6 is iris image data.

**ISO/IEC 24745.** International standard for biometric template protection (cancellable biometrics, secure sketches, biocryptosystems). Frames the future encryption-and-protection roadmap for stored templates.

**ISO/IEC 30107.** International standard for biometric presentation attack detection. Defines APCER, BPCER, attack categorisation, and reporting requirements. The reference for `docs/pad.md`.

**ISO/IEC 19795.** International standard for biometric performance testing and reporting. Frames `docs/performance.md` and the `tests/evaluation/` harness in Phase 3 #43.

**MINEX.** NIST Minutiae Interoperability Exchange — the fingerprint analogue of IREX. MINEX III validation imagery is what TANIK uses for Phase 2 fingerprint test fixtures (U.S. public domain; see `docs/datasets.md`).

**FRVT.** NIST Face Recognition Vendor Test. Out of TANIK's scope (no face modality), but the gold-standard reference for face matcher accuracy claims.

**PFT.** NIST Proprietary Fingerprint Template — a benchmark for vendor-specific fingerprint templates. Less relevant for TANIK because SourceAFIS is open and standards-based.

**NIST IR 8311.** *Biometric Performance Testing under Common Cybersecurity Frameworks.* A useful sanity check for anyone wiring biometrics into a US-federally-aligned posture.

## Privacy and regulation

**Cancellable biometric.** A template-protection scheme where the stored representation is a deliberately distorted version of the underlying biometric, with the distortion controlled by a key. If the database is breached, you can issue a new key and re-enrol — "cancelling" the leaked templates. ISO/IEC 24745 defines the framework.

**EU AI Act (Regulation 2024/1689).** EU regulation that risk-tiers AI systems. Remote real-time biometric identification in public spaces is heavily restricted; biometric verification (1:1) faces lighter constraints. TANIK is in scope conceptually for any EU deployment.

**GDPR (Regulation 2016/679).** EU data protection regulation. Treats biometric data as *special category* (Art. 9); requires explicit consent (or one of the other narrow lawful bases) for processing.

**KVKK (Türkiye, Law No. 6698).** Turkish data protection law. Treats biometric data as *özel nitelikli kişisel veri* (special category) under Art. 6; analogous in shape to GDPR Art. 9.

**Lawful basis.** The legal justification for processing personal data. Under GDPR Art. 9 / KVKK Art. 6, the lawful basis for biometric processing is most often *explicit consent* — there are other narrow exceptions (employment law, vital interests, public interest in health) that rarely apply to a kiosk system.

**Pseudonymous.** Data that does not directly identify a person but could re-identify them when combined with other data. UUIDs and session IDs are pseudonymous; storing them is still subject to GDPR/KVKK obligations.

**Right to erasure (GDPR Art. 17 / KVKK Art. 7).** A data subject can request that a controller delete their personal data, subject to certain exceptions. The Phase 4 admin `DELETE /api/v1/admin/subjects/{id}` endpoint implements this for TANIK.

**Special category personal data.** Personal data given heightened protection under GDPR Art. 9 / KVKK Art. 6 — biometric data, health data, sexual orientation, religious beliefs, etc. The threshold for processing is higher: explicit consent or one of the narrow exceptions.

## Honesty discipline (TANIK-specific)

**`calibration_status: "placeholder"`.** TANIK's in-band signal in unified-verify responses that the fusion weights and thresholds in use are honest defaults, not tuned on a calibration set. Flips to `"calibrated"` when Phase 3 #43 publishes measured weights.

**Honest TBD.** The convention used in `docs/performance.md` and elsewhere: any number that has not been measured on a real evaluation set reads `TBD`, never an invented "1 in a million" or similar. This is enforced by convention, not by tooling.

**No raw image persistence.** TANIK's actual privacy guarantee. Stronger than vague "biometric data is protected" claims because it can be verified by `grep` against the codebase. **Not** the same as "zero-knowledge biometrics" — templates are stored, and templates are personal data.

**Phase-gate.** TANIK's project discipline: a phase ships before the next phase starts. New ideas go in `BACKLOG.md`, not silently into the active phase. Documented in `CLAUDE.md` and `ROADMAP.md`.

## Worth-knowing references

- Daugman, J. (2004). *How iris recognition works.* IEEE TCSVT. The single most useful reference for understanding iris matching.
- Maltoni, D., Maio, D., Jain, A. K., Prabhakar, S. (2009). *Handbook of Fingerprint Recognition.* Springer. The textbook for fingerprint matching.
- Marcel, S., Nixon, M.S., Fierrez, J., Evans, N. (eds.) (2019). *Handbook of Biometric Anti-Spoofing.* Springer. The single best reference for PAD across modalities.
- Ross, A. & Jain, A. K. (2003). *Information fusion in biometrics.* Pattern Recognition Letters. The reference for score-level fusion.
- ISO/IEC 30107-3 (PAD reporting), 19795-1 (performance testing), 24745 (template protection), 19794-2 (fingerprint templates).
