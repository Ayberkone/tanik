# Datasets

Every biometric dataset referenced anywhere in this repo, with its source, license, and access conditions. Biometric data is personal data; the provenance matters.

**This document is a stub maintained as datasets are added.** The comprehensive list arrives with Phase 3's evaluation work, where FAR/FRR measurement actually depends on dataset composition.

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

- **Status:** Access request draft at `docs/outreach/nd-iris-request.md`, addressed to Prof. Adam Czajka.
- **Purpose:** Phase 3 FAR/FRR evaluation. Larger scale, better-documented subject splits than MMU.

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

- **Status:** noted as the natural Phase 3 candidate for genuine/impostor pairs. The competition's "B" subsets are widely treated as freely usable for academic research; the FVC website is no longer authoritative, so any use must verify the licence wording at acquisition time. Not vendored, not yet referenced in tests.
