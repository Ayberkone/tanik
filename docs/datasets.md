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

Deferred to Phase 2. Will be added here when that phase begins.
