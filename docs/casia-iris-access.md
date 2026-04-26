# CASIA Iris access — what to do, step by step

How to request access to a CASIA iris database — the Phase 3 fallback if ND-IRIS-0405's institutional-signature wall blocks the independent-author path.

> **Important caveat.** CASIA's website (`biometrics.idealtest.org`) was unreachable from the network this guide was prepared from. **The exact submission URL, email address, and current form filename below need to be verified by you when you visit the actual site.** This guide captures what is well-known about CASIA's general process; the specific contact details have changed over the years and the authoritative source is the live website, not this document.

---

## Why CASIA (and not just one of the others)

For a Phase 3 iris-evaluation set on this project, the realistic options for an unaffiliated independent author are roughly in this order:

| Dataset | NIR? | Scale | Application gate |
|---|---|---|---|
| **CASIA-Iris-V4** (Thousand, Interval, Lamp, etc.) | ✅ | ~54,600 images / ~1,800 subjects across the V4 subsets | Application form + intended-use statement; individuals are eligible in practice |
| **UBIRIS.v2** (U. Beira Interior, Portugal) | ❌ visible-light captures | 11,102 / 261 | Online registration only — no committee gate |
| **IIT Delhi Iris Database** | ✅ | 2,240 / 224 | Application via IIT Delhi; smaller scale |
| **MMU iris** | ✅ | small (~450) | Already in use for Phase 0 fixtures |

CASIA wins on **scale + NIR + individual-eligibility-in-practice**. UBIRIS is the no-gate fallback if CASIA also says no, but UBIRIS visible-light captures are less representative of real iris-recognition deployments (which use NIR illumination). Prefer CASIA; fall back to UBIRIS only if CASIA refuses.

## What CASIA is and isn't

- **Who hosts it.** The Center for Biometrics and Security Research (CBSR) at the Institute of Automation, Chinese Academy of Sciences (CASIA, Beijing).
- **What's in V4.** Six subsets: `CASIA-Iris-Interval`, `CASIA-Iris-Lamp`, `CASIA-Iris-Twins`, `CASIA-Iris-Distance`, `CASIA-Iris-Thousand`, `CASIA-Iris-Syn`. The `Thousand` subset is the largest (≈ 1,000 subjects) and the most commonly cited for evaluation.
- **License.** Research/educational use only. Redistribution prohibited. Citation required in publications.
- **What it is NOT.** Not a "drop-in download." There is an application process; submission to redownload, no torrents, no unofficial mirrors that this project will use.

## The application process — typical shape

> Verify the current details on the live site before submitting; the elements below describe the *typical* shape of CASIA's process based on widely-shared experience among researchers, not the *current* exact form.

1. **Find the official page.** Google `CASIA Iris Database CBSR application` or visit `biometrics.idealtest.org` (if reachable). Confirm the page is on a `*.ia.ac.cn` or `*.idealtest.org` domain — those are the legitimate CASIA / CBSR hosts.
2. **Download the application form.** Historically a PDF or Word doc with fields for: full name, organisation/affiliation, country, postal address, email, intended use of the data, list of which subset(s) you want, and a signature.
3. **Fill it in honestly.** Affiliation as "independent open-source researcher" or your country/city — *not* an institution you don't actually represent. Intended use: a 2-3 sentence description of TANIK and what you'll measure with the data.
4. **Submit it.** Historically by email to a CBSR address (the exact address has changed; the live page is authoritative). Send from any email address you'll receive replies on.
5. **Wait.** CASIA review timelines vary; typical reports range from a few days to a few weeks.
6. **Receive the access link.** Historically a download URL plus a password, valid for a limited time. The data ships as compressed archives; total size is in the multi-GB range for the V4 subsets.

## What goes in the "intended use" field

For TANIK specifically, this is what to write (or close to it):

> The dataset will be used to evaluate the iris matching component of TANIK, an MIT-licensed open-source reference implementation of a multi-modal biometric authentication kiosk (`https://github.com/Ayberkone/tanik`). I will compute and report False Accept Rate (FAR), False Reject Rate (FRR), and the Equal Error Rate (EER) of the iris pipeline (Worldcoin's `open-iris`) on a held-out subset of the data, in order to publish honest, measured performance numbers in `docs/performance.md` of the project. The original data will not be redistributed; only the computed metrics will be published. The dataset citation will appear in the project's `docs/datasets.md` and in any blog post or article describing the evaluation.

That paragraph is honest (it accurately describes what you'll do), specific (FAR/FRR/EER, not "research"), and reassuring on the redistribution concern (only metrics, not images).

## What to NOT do

- **Don't fabricate institutional affiliation.** "Independent open-source researcher" or your country is the right answer. Inventing a university or company affiliation for a license you'll later cite in a blog post is a problem, not a shortcut.
- **Don't redistribute the data.** If granted access, the images stay outside the TANIK repository (gitignored cache is the right pattern; same as the MMU and MINEX fixtures).
- **Don't apply to multiple databases simultaneously hoping one approves.** Pick CASIA first; fall back to UBIRIS only if CASIA refuses. Multiple-applications-at-once burns goodwill if anyone notices.

## When you have access

1. Update `docs/datasets.md` — promote the CASIA entry from "planned" to "in use," with the specific subset name and download date.
2. Update `OWNER-ACTIONS.md` — move "Acquire iris evaluation dataset" to the Done section.
3. The Phase 3 `#43` evaluation harness then becomes unblocked. Drop a note in the next session and Phase 3 can actually close.

## If CASIA refuses

UBIRIS.v2 is the no-gate fallback. Visit <https://www.cs.ubi.pt/projects/ubipr/ubiris2.html> (or search "UBIRIS.v2 download"), register with your email, download. Visible-light captures rather than NIR — document the trade-off explicitly in `docs/datasets.md` and in any reported results: UBIRIS-derived numbers should not be quoted as "iris recognition performance" without the qualifier "on visible-light captures."

If both CASIA and UBIRIS refuse (extremely unlikely for UBIRIS), the honest answer is that Phase 3 cannot ship measured numbers and the project plateaus at "architectural reference with placeholder calibration" until institutional sponsorship materialises.

---

**Source verification reminder:** the contact details, form filename, and submission email below are what to confirm on the live CASIA site before sending anything. This guide captures the *shape* of the process; the *specifics* are authoritative only on `biometrics.idealtest.org` or the equivalent live CBSR page.
