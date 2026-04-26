# Email draft — CASIA Iris access request

**To:** `[verify the current address from biometrics.idealtest.org or the CBSR page]`
**Subject:** CASIA-Iris-V4 access request — open-source biometrics reference project

---

Dear CASIA / CBSR team,

I'm writing to request access to the CASIA-Iris-V4 database (specifically the **Thousand** and **Interval** subsets, if both are available; the Thousand subset alone is also acceptable) for the Phase 3 evaluation of an MIT-licensed open-source biometric reference project.

### Project

TANIK is an open-source multi-modal biometric authentication kiosk that fuses iris recognition (using Worldcoin's `open-iris` pipeline) and fingerprint matching (using SourceAFIS) into a single identity decision. The project is intended as a credible reference implementation demonstrating honest engineering practice in biometrics — including a documented threat model, accurately scoped liveness claims, and the discipline of not reporting any FAR/FRR numbers that have not been measured on a real test set.

Repository: <https://github.com/Ayberkone/tanik>
License: MIT

### Affiliation

I am an independent open-source researcher and developer based in Türkiye. I am not currently affiliated with a university or research institution; this project is a personal effort.

### Intended use

The CASIA iris data will be used to evaluate the iris matching component of TANIK. Specifically, I will compute:

- False Accept Rate (FAR) on impostor pairs
- False Reject Rate (FRR) on genuine pairs
- Equal Error Rate (EER) and an ROC curve

These measured numbers will be published in `docs/performance.md` of the project (currently a skeleton with every cell marked `TBD`). The CASIA dataset will be cited per the database's standard citation requirement in that document and in any blog post or article describing the results.

### Redistribution and handling

The original CASIA images will **not** be redistributed through the TANIK repository. They will be stored locally in a gitignored cache directory and will not appear in the public repository at any point. Only the computed evaluation metrics (FAR, FRR, EER, ROC curve) will be published. This is the same handling pattern already in use for the project's existing test fixtures (NIST MINEX III for fingerprints, Worldcoin's public iris demo set for iris).

I will follow whatever additional usage restrictions are specified in the CASIA license agreement.

### Citation

Once the data is in use, the project will cite the CASIA Iris databases per the standard citation form provided by CBSR. I will follow whatever specific citation language CBSR specifies in the access response.

If there is a formal application form to fill in alongside this email, please point me at the current version on the CBSR site and I will return it signed.

Thank you for considering this request, and for the work CBSR has put into making research-grade biometric data available to the community.

Best regards,
Ayberk Baytok
ayberk.baytok@gmail.com
Project repository: <https://github.com/Ayberkone/tanik>
Türkiye

---

## Notes on adapting this draft

- **Subject line:** if CBSR has a specific format they prefer (some labs want a tag like `[CASIA Iris Request]`), use that.
- **Subset choice:** the draft asks for `Thousand` + `Interval`. `Thousand` alone (the largest subset) is the most commonly used for FAR/FRR evaluation and is enough on its own.
- **The "affiliation" paragraph:** keep it. Being upfront about being an independent researcher is the right move; CASIA has historically approved individuals when the use case is clearly research/educational.
- **The "redistribution" paragraph:** this is the part CBSR cares about most. The TANIK pattern (gitignored cache, only metrics published) is exactly what they want to hear.
- **If CBSR sends back a PDF form:** fill it in, sign by hand or digitally, send back from the same email address. Keep a local copy.
