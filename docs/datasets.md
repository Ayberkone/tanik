# Datasets

Every biometric dataset referenced anywhere in this repo, with its source, license, and access conditions. Biometric data is personal data; the provenance matters.

**This document grows as datasets are added.** The Phase 3 evaluation work formalises the dataset list once `#11` (ND-IRIS-0405) and the FVC-style fingerprint set land — that's when FAR/FRR measurement starts depending on a documented composition.

## Principle

- No proprietary or privately-obtained biometric data, ever.
- No dataset images are redistributed through this repository. `notebooks/data/` is gitignored; images are downloaded from their authoritative sources.
- Every dataset is named, sourced, and credited. Papers that introduced the dataset are cited where relevant.
- Retention: if a dataset owner asks, we remove all references and cease use. No data outlives its terms.

## In use

### MMU Iris Database (Multimedia University, Malaysia)

- **Composition used in Phase 0:** 16 images across 4 subjects (`0`, `1`, `2`, `3` — left-eye captures). Grayscale, 320×240, near-infrared, BMP.
- **Primary source:** Multimedia University's original distribution page (historically `pesona.mmu.edu.my/~ccteo/`; intermittently available).
- **Phase 0 is fetched from:** `https://github.com/emrealtann/IrisRecognition` (MIT-licensed) as a practical mirror of the MMU1 set. The upstream repository credits Multimedia University; TANIK does not claim the data.
- **License / terms:** MMU is distributed for academic research. No commercial use. No redistribution from the MMU project itself — TANIK references but does not host the images.
- **Role here:** Phase 0 teaching notebook only. Not used for FAR/FRR in any reported metric.

## Planned (access in progress)

### ND-IRIS-0405 (University of Notre Dame)

- **Composition:** 64,980 NIR iris images from 356 subjects (712 unique irises), captured at the University of Notre Dame between January 2004 and May 2005.
- **Status:** License-execution in progress. Adam Czajka (ND CVRL) confirmed the formal access path 2026-04-25; license agreement at <https://cvrl.nd.edu/media/django-summernote/2018-09-19/397132ea-96bd-4f41-b796-7ffd63021e41.pdf>. Step-by-step author-side guide at `docs/nd-iris-0405-access.md`. Outreach in `docs/outreach/nd-iris-request.md`.
- **Purpose:** Phase 3 FAR/FRR evaluation (`#11` → `#43`). Larger scale and better-documented subject splits than MMU.
- **Delivery:** Globus transfer after ND-CVRL approval.
- **Storage:** outside the repo (suggested `~/datasets/nd-iris-0405/`); never committed.
- **Citation requirement:** publications and public reports using this dataset must cite the paper named in the license agreement.

### CASIA-Iris (Institute of Automation, Chinese Academy of Sciences)

- **Status:** Not yet requested. Required for Phase 3 if ND-IRIS is not granted.
- **Access:** Formal request via CASIA's biometrics group.

### UBIRIS.v2 (University of Beira Interior)

- **Status:** Noted as backup. Non-cooperative / visible-light captures; complements ND-IRIS/CASIA if cross-condition testing is added.

## Excluded

### UCI / Fisher "Iris" dataset

- **Excluded for a specific reason:** despite the name, this is the Fisher iris *flower* classification dataset (1936), not iris biometrics. Any occurrence of it in this repo would be a mistake.

## Fingerprint datasets

### NIST MINEX III validation imagery

- **Composition used in Phase 2 tests:** six grayscale plain-impression images sampled from `usnistgov/minex/minexiii/validation/validation_imagery_raw`. Three from subject `a001` (right index, right middle, right ring) and three from subject `a002` (right index, right middle, left index). Sufficient for "different fingers do not match" assertions; not sufficient for "same finger matches an independent capture", because the MINEX validation set ships only one impression per finger.
- **Format:** 8-bit raw grayscale (`.gray`), 500 dpi, dimensions vary per image (width/height encoded in `minexiii_validation_data.h`). Converted to PNG in the test fixture before being passed to SourceAFIS.
- **Primary source:** https://github.com/usnistgov/minex/tree/master/minexiii/validation/validation_imagery_raw
- **License / terms:** NIST works are not subject to copyright (17 USC §105) and are in the U.S. public domain. Royalty-free worldwide redistribution and modification, with attribution to NIST. License text: https://github.com/usnistgov/minex/blob/master/LICENSE.md
- **Role here:** Phase 2 binding + discrimination tests for the SourceAFIS / JPype engine. The `tests/conftest.py` `fingerprint_bytes` fixture downloads these into a gitignored cache (`tests/fixtures/_cache/`) on first run, mirroring the iris-fixture pattern. They are **not redistributed via this repository**.
- **Out of scope here:** MINEX validation has no within-finger pairs, so Phase 3 evaluation cannot use it for genuine-vs-impostor scoring. That dataset (FVC-style or similar with multiple impressions per finger) is captured in `BACKLOG.md` as the dataset gap to close before Phase 3.

## Planned (access in progress) — fingerprint

### FVC2002 / FVC2004 DB1_B (free subsets)

- **Composition (typical):** 80 fingerprint images per database in the "B" subset (10 fingers × 8 impressions). Multiple impressions per finger is the property MINEX III lacks and is what makes FVC-style data the right choice for genuine-vs-impostor scoring.
- **Status:** noted as the natural Phase 3 candidate for genuine/impostor pairs. The competition's "B" subsets are widely treated as freely usable for academic research; the FVC website is no longer authoritative, so any use must verify the licence wording at acquisition time. Not vendored, not yet referenced in tests. BACKLOG-tracked.

## Planned (access in progress) — PAD (Phase 4)

The Phase 4 PAD module needs labelled bona-fide-vs-attack pairs. Candidate sources, in order of preference (final selection happens in Phase 4 once licensing is verified):

### NDIris3D (University of Notre Dame)

- **Composition:** Live + 3D-printed iris attacks.
- **Access:** ND CVRL, same license route as ND-IRIS-0405. Follow the `docs/nd-iris-0405-access.md` procedure with the dataset name swapped.
- **Role:** Strong candidate for the v1 iris-PAD training/evaluation set.

### CASIA-Iris-Fake (Institute of Automation, Chinese Academy of Sciences)

- **Composition:** Live + printed-photo + contact-lens iris attacks.
- **Access:** Request-based via CASIA's biometrics group. Older but well-cited.

### LivDet-Iris and LivDet-Fingerprint (annual competitions)

- **Composition:** Per-edition bona-fide + spoof sets across multiple sensors and attack types. LivDet-Iris-2017 / 2020 / 2023; LivDet-Fingerprint similar cadence.
- **Access:** Per-edition; <https://livdet.org/>.
- **Role:** Useful as evaluation sets even if v1 trains on a different dataset — published per-year results give a realistic upper bound on what software-only PAD achieves.

See `docs/pad.md` for the full PAD plan, including ISO/IEC 30107 framing and the candidate approaches.
