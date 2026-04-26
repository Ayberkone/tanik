# PolyU Cross-Spectral Iris Database — application content

The PolyU dataset is requested via a **web form** at <http://www4.comp.polyu.edu.hk/~csajaykr/myhome/database_request/polyuiris/>, not via direct email. The text below is what to paste into the form's free-text fields. The contact for follow-up correspondence is `ajay.kumar@polyu.edu.hk`.

---

## Form fields — what to enter

### Name
`Ayberk Baytok`

### Email
`ayberk.baytok@gmail.com`

### Affiliation / institution
`Independent open-source researcher (Türkiye)`

### Country
`Türkiye`

### Intended use of the database

Paste verbatim — this is calibrated to be honest, specific, and reassuring on the redistribution concern:

```
The PolyU Cross-Spectral Iris Database will be used to evaluate the iris matching component of TANIK, an MIT-licensed open-source reference implementation of a multi-modal biometric authentication kiosk (https://github.com/Ayberkone/tanik). The project demonstrates honest engineering practice in biometrics — including a documented threat model, accurately scoped liveness claims, and the discipline of not reporting any FAR/FRR numbers that have not been measured on a real test set.

Specifically, I will compute and report the False Accept Rate (FAR), False Reject Rate (FRR), and Equal Error Rate (EER) of the iris pipeline (Worldcoin's open-source open-iris) on a held-out subset of the PolyU NIR captures. The bi-spectral nature of the database also potentially supports a follow-up cross-spectral evaluation — measuring how matching performance changes between same-spectrum (NIR-NIR) and cross-spectrum (NIR-visible) pairs — which would be a meaningful contribution to the project's evaluation chapter.

The original images will not be redistributed through the TANIK repository. They will be stored locally in a gitignored cache directory and will not appear in the public repository at any point. Only the computed evaluation metrics will be published. The Ramaiah & Kumar (2017) founding paper will be cited in the project's datasets and performance documents, and in any blog post or article describing the evaluation results.
```

### Project / research description (if asked separately)

If the form has a separate "research description" or "project" field, the second paragraph above (intended use) covers it. If a shorter version is needed:

```
Open-source multi-modal biometric kiosk reference (iris + fingerprint),
MIT-licensed. Phase 3 evaluation: measured FAR/FRR/EER for the iris
matching component on a held-out subset of the PolyU NIR captures.
```

### Consent / agreement to terms

The form is expected to ask the applicant to agree to the database usage terms (no commercial use, no redistribution, citation requirement). All three are compatible with TANIK's posture — agree truthfully.

---

## After submission

The PolyU page states: *"Confirmation arrives via email with download instructions."* Reported response times for individual researcher requests to Ajay Kumar are typically within a few days.

When the email arrives:

1. Save the download instructions and any access credentials.
2. Download the data into `~/datasets/polyu-iris/` (outside the TANIK repo — never commit dataset images).
3. Update `docs/datasets.md` with the download date and the dataset composition.
4. Drop a note in the next chat — `#43` (FAR/FRR harness) becomes the next concrete coding task.

## If a follow-up question comes back from Prof. Kumar

The likely questions are: clarification on what "TANIK" is (point at the README), confirmation of non-commercial use (yes), confirmation that data won't be redistributed (yes), or a request for citation language (use the Ramaiah & Kumar 2017 form he specifies in the response).

A short, clear reply that confirms the three constraints (non-commercial, no redistribution, will cite) is what's wanted. Don't oversell the project; he sees research applications regularly and prefers brevity.
