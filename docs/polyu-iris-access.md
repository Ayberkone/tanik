# PolyU Cross-Spectral Iris Database access — step-by-step

The new primary path for `#11` (Phase 3 iris-evaluation dataset). Replaces the dataset-acquisition role that ND-IRIS-0405 originally held — PolyU is comparable in scale, more accessible to independent authors, and is **bi-spectral** (NIR + visible, pixel-to-pixel paired) which actually opens evaluation paths ND-IRIS doesn't (cross-spectral matching as an extension story).

---

## Why this is now the primary path

Discovery (2026-04-26): the IEEE Biometrics Council resources page (<https://ieee-biometrics.org/resources/biometric-databases/ocular-iris-periocular/>) lists nine ocular databases, including the PolyU Cross-Spectral Iris Database hosted by **Ajay Kumar at Hong Kong PolyU**. The PolyU process is a **web-form application** with no institutional-signature wall — exactly what an unaffiliated independent author needs.

Comparison vs. the previously-planned alternatives:

| Dataset | Scale | NIR? | Access wall |
|---|---|---|---|
| **PolyU Cross-Spectral** ⭐ | 12,540 images / 209 subjects | **NIR + visible (paired)** | Web form |
| ND-IRIS-0405 | 64,980 / 356 | NIR | Institutional signature (hard wall for solo authors) |
| CASIA-Iris-V4 | ~54,600 / ~1,800 | NIR | Application + email (CASIA site intermittently unreachable) |
| IIT Delhi Iris | 2,180 / 218 | Visible | Web form (smaller, visible-only) |
| UBIRIS.v2 | 11,102 / 261 | Visible | No-gate registration |

PolyU wins on **scale × spectrum × accessibility**. ND-IRIS-0405 has more subjects but the institutional wall makes it a non-option without a sponsor; CASIA's site has been unreachable from multiple networks. PolyU is the path that actually moves Phase 3 forward.

## Dataset details

- **Name:** PolyU Cross-Spectral Iris Images Database (sometimes referenced as `PolyU-CS`).
- **Composition:** 12,540 images from 209 subjects. **15 instances per subject** in the primary session; 12 subjects participated in a second session.
- **Spectrum:** Both NIR and visible-light captures, **with pixel-to-pixel correspondence**. This is rare and valuable — most NIR datasets do not have a paired visible-light view.
- **Resolution:** 640 × 480 pixels.
- **Eyes:** Both left and right.
- **Format:** Raw images plus automatically segmented/normalised versions.
- **Founding paper:** Ramaiah & Kumar (2017). Cite this in `docs/datasets.md` and any published evaluation results.
- **Hosting institution:** The Hong Kong Polytechnic University, Department of Computing.
- **Maintainer / contact:** Ajay Kumar (`ajay.kumar@polyu.edu.hk`).

## Access procedure

1. **Open the application form** at <http://www4.comp.polyu.edu.hk/~csajaykr/myhome/database_request/polyuiris/>.
2. **Fill it in honestly.** Affiliation as "independent open-source researcher" or your country/city. Intended use: brief description of TANIK and what the data will be used for. The draft email in `docs/outreach/polyu-iris-request.md` carries the exact wording you can paste into the form.
3. **Submit.** The page says confirmation arrives via email with download instructions.
4. **Wait.** Ajay Kumar's response time is reportedly within days for individual researcher requests.

## Restrictions to respect

Per the database terms (verbatim):

- *"Commercial use/distribution of this database is strictly prohibited."*
- *"All rights reserved."*
- Publications using the database must acknowledge and cite the founding paper (Ramaiah & Kumar, 2017).

For TANIK specifically:

- ✅ MIT-licensed open-source educational project — **non-commercial use is the intended scope.**
- ✅ The data will not be redistributed; only computed metrics (FAR, FRR, EER) will appear in `docs/performance.md`.
- ✅ Citation will appear in `docs/datasets.md` and in any published results.

## What changes when you have access

1. Update `docs/datasets.md` — promote the PolyU entry from "in progress" to "in use," with the download date.
2. Update `OWNER-ACTIONS.md` — move item 1 ("Acquire iris evaluation dataset") to the Done section.
3. Phase 3 `#43` (FAR/FRR harness) becomes the next concrete coding task.
4. Drop a note in the next chat — Phase 3 work resumes immediately.

## If PolyU refuses (extremely unlikely)

In order:

1. **IIT Delhi Iris** — same web-form pattern, smaller scale, visible-only. <http://www4.comp.polyu.edu.hk/~csajaykr/IITD/Database_Iris.htm>.
2. **UBIRIS.v2** — no-gate registration. <https://www.cs.ubi.pt/projects/ubipr/ubiris2.html>. Visible-only; document the trade-off in `docs/datasets.md`.
3. **CASIA-Iris** if and when the site becomes reachable. The previously-prepared draft is in `docs/outreach/casia-iris-request.md`.

## Source

IEEE Biometrics Council, *Resources → Biometric Databases → Ocular: Iris & Periocular*, <https://ieee-biometrics.org/resources/biometric-databases/ocular-iris-periocular/> (consulted 2026-04-26). The IEEE page is the authoritative cross-reference for currently-available ocular datasets — worth re-checking annually.
