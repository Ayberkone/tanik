# ND-IRIS-0405 access — step-by-step

What you need to do, in order, to obtain the ND-IRIS-0405 dataset (the Phase 3 iris-evaluation prerequisite — task `#11` in the active task list).

> **Why this dataset?** ND-IRIS-0405 ships 64,980 iris images from 356 subjects (712 unique irises), captured at the University of Notre Dame between January 2004 and May 2005. It is the canonical research-grade NIR iris dataset and is the only realistic basis on which to compute FAR / FRR for the iris pipeline honestly. Without it, `docs/performance.md` cannot ship measured numbers, which means the unified `/api/v1/verify` endpoint stays at `calibration_status: "placeholder"`.

---

## What you actually have to do

### 1. Download the license agreement

PDF: <https://cvrl.nd.edu/media/django-summernote/2018-09-19/397132ea-96bd-4f41-b796-7ffd63021e41.pdf>

Save it to your Downloads folder. **Do not sign it yourself yet — see step 2.**

### 2. Get the right person at your institution to sign it

This is the part most people get wrong, because the academic licensing template is strict:

- **The license must be signed by an individual authorised to make legal commitments on behalf of your organisation.**
- ND-CVRL **will not accept** a license signed by a student or postdoctoral scholar, regardless of seniority.
- ND-CVRL **will not accept** a license signed by a faculty member unless the faculty member has been *explicitly delegated* contracting authority by the institution.
- The practical answer: the institution's legal office, contracting office, or research-administration office signs it.

**For TANIK specifically:** because Ayberk is signing as an independent open-source author and not on behalf of an institution, this is a real friction point. Two paths to resolve:

1. **Affiliate route.** Find a Turkish university research group (or Proline's R&D legal contact) willing to be the named licensee and route the data through them. This is the cleanest path; Adam Czajka's reply (2026-04-25) confirmed there is a path.
2. **Independent-researcher route.** Email cvrl@nd.edu *first*, before signing, explaining the situation: open-source biometrics reference project, no institutional backer, request for guidance on how an independent author can be a licensee. Adam already knows the project exists and gave the access pointer — this is the natural follow-up.

Don't fill out and sign the document until step 3 — the answer to "who signs?" determines whose details go in.

### 3. Fill in the institutional point-of-contact information

The submission email (or fax) must include:

- **Institutional full name** (e.g. "Pasifik Teknoloji A.Ş." or "Bilkent University" — whichever is the licensee).
- **Title of the signing officer.**
- **Postal address of the institution.**
- **Phone number** of the institutional point of contact.

If you go the independent-researcher route in step 2, this list is exactly what you should ask Adam to flex on.

### 4. Submit the signed license

Two channels accepted:

- **Email (preferred):** send the signed PDF to **`cvrl@nd.edu`** *from an institutional email address*. The submission instructions are explicit that personal email providers (Gmail, Yahoo, etc.) are not accepted — the email address itself functions as a soft credential that the sender belongs to the licensee organisation.
- **Fax:** `+1 574 631 9260`, attention **"J. Dhar"**.

### 5. Wait for ND-CVRL approval

Once the signed license is received and approved, ND-CVRL responds with **download instructions delivered via Globus** (the research-data transfer service). They do not email a download link directly; they grant Globus access to the dataset endpoint.

If you do not have a Globus account yet, create one at <https://www.globus.org/> ahead of time so step 6 is unblocked when the approval lands.

### 6. Download via Globus

When the approval email arrives, follow its instructions to add the ND-CVRL endpoint to your Globus account and transfer the dataset. **Estimated download size: tens of GB** (64,980 NIR images). Plan storage accordingly — local SSD with at least ~80 GB free is the safe target, and the data should land in a directory that is **outside the TANIK git repo** so it cannot be accidentally committed.

Suggested location:

```
~/datasets/nd-iris-0405/
```

The TANIK evaluation harness (Phase 3 task `#43`) will read from a path you configure via env var; never check the data into the repo.

### 7. Cite the paper

Publications and public-facing reports using ND-IRIS-0405 must cite the paper named in the license agreement. The TANIK README and `docs/datasets.md` will need a citation entry once the dataset is in use; that gets added in the same commit as the first evaluation result.

---

## What this is NOT

- This dataset request **is not part of automated CI**. It is a one-time human-and-institution process.
- Claude cannot do step 2, 3, or 4 for you. They require institutional authority and an institutional email address. Claude can do step 1 (point at the PDF), help draft the cover email in step 4, and fully take over from step 6 onward.

## When it lands

Update task `#11` to completed, drop a note in `CHANGELOG.md` under the `Phase 3` section, and the next session can then ship `#43` (FAR/FRR/ROC harness) which unblocks `#42` (threshold-slider UI).

---

**Source:** `https://cvrl.nd.edu/projects/data/` (fetched 2026-04-26). Re-verify the email address and the PDF link before sending — the page may have moved between this guide being written and you acting on it.
