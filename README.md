# LabelGuard AI — Alcohol Label Verification Prototype

LabelGuard AI is a local-first Streamlit application for verifying alcohol beverage label artwork or extracted label text against application data. It is designed as a standalone proof of concept for reducing routine alcohol label review work while keeping the final compliance decision understandable to human reviewers.

The application focuses on the workflow described in the take-home assignment:

* Fast feedback for routine label checks
* A simple one-page interface for non-technical users
* Batch upload support for reviewing multiple labels at once
* Clear `PASS`, `REVIEW`, and `FAIL` results
* Strict government health warning validation
* No external AI API dependency
* No direct COLA integration

## Deployed Application

Deployed application URL:

```text
Deployed application URL:

```

Source code repository:

```text
https://github.com/Colonad/instructions/tree/labelguard-prototype
```

## What the App Checks

For each uploaded label, the application verifies whether the label text matches the submitted application fields:

1. Brand name
2. Class/type designation
3. Alcohol content, ABV, or proof equivalence
4. Net contents
5. Producer or bottler name/address, when provided
6. Country of origin, when provided
7. Government health warning statement

The government warning statement used by the prototype is:

```text
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
```

## Key Features

* **Single-label review:** Enter application fields and upload one label.
* **Batch review:** Upload multiple labels in one run.
* **Local-first validation:** Uses deterministic checks and optional local OCR.
* **No cloud AI dependency:** Works without sending files to third-party AI services.
* **Transparent results:** Shows which checks passed, failed, or need review.
* **CSV and JSON exports:** Allows reviewers to download structured results.
* **Sample data included:** Demo files are included for immediate testing.

## Approach

The application uses a practical rule-based pipeline rather than relying on external AI services.

The review flow is:

1. The reviewer enters application data in the sidebar.
2. The reviewer uploads one or more label files.
3. The app extracts text from each file.
4. The validator compares extracted label text against the application data.
5. The app returns a status for each file:

   * `PASS`
   * `REVIEW`
   * `FAIL`
6. The reviewer can inspect detailed checks and download results.

This approach was chosen because the assignment emphasizes speed, usability, and government-network constraints. A local-first system avoids slow remote calls, reduces deployment friction, and keeps the decision path easy to inspect.

## Tools Used

* **Python** for application logic
* **Streamlit** for the user interface
* **pandas** for tabular results and CSV export
* **Pillow** for image handling
* **pytesseract** for optional local OCR
* **pytest** for automated tests
* **GitHub Actions** for continuous integration
* **Render or Streamlit Community Cloud** for deployment

## Repository Structure

```text
.
├── app.py                         # Streamlit user interface
├── labelguard/
│   ├── __init__.py
│   ├── models.py                  # Dataclasses and status types
│   ├── ocr.py                     # Text extraction and optional OCR
│   ├── utils.py                   # Normalization/parsing helpers
│   └── validator.py               # Verification rules
├── sample_data/
│   ├── old_tom_label.txt          # Passing demo label
│   ├── bad_warning_label.txt      # Warning failure demo
│   ├── review_case_old_tom_case.txt
│   └── batch_expected.csv
├── tests/
│   └── test_validator.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .streamlit/
│   └── config.toml
├── .gitignore
├── Procfile
├── pytest.ini
├── requirements.txt
└── README.md
```

## Prerequisites

* Python 3.11 or newer
* pip
* Optional: Tesseract OCR for image-based label files

Text files do not require Tesseract. The included sample files are plain text, so the core application can be tested immediately after installing Python dependencies.

### Optional Tesseract Installation

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

#### macOS

```bash
brew install tesseract
```

#### Windows

Install Tesseract from the UB Mannheim Windows builds, then make sure the installation directory is available on your `PATH`.

## Local Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run Automated Tests

```bash
python -m pytest -q
```

Expected result:

```text
5 passed
```

## Run the App Locally

```bash
python -m streamlit run app.py
```

Open the local URL shown by Streamlit. It is usually:

```text
http://localhost:8501
```

## Quick Demo Script

This section gives reviewers a fast, repeatable path to test the prototype without reading the full codebase first.

### Local demo

From the project root, run:

    source .venv/bin/activate
    python -m pytest -q
    python -m streamlit run app.py

Open the URL printed by Streamlit. It is usually:

    http://localhost:8501

### Important testing note

The app applies one set of sidebar application data to every uploaded file in a batch. That means the default Old Tom labels, the Jamaica import label, and the STONE'S THROW label should not all be tested with the same sidebar values unless you intentionally want to see mismatches.

### Default demo batch

Leave the default application fields as:

| Field | Value |
|---|---|
| Brand Name | `OLD TOM DISTILLERY` |
| Class/Type | `Kentucky Straight Bourbon Whiskey` |
| Alcohol Content | `45% Alc./Vol. (90 Proof)` |
| Net Contents | `750 mL` |
| Producer | `Old Tom Distillery, Louisville, KY` |
| Country of origin | leave blank |

Then upload the `.txt` files from:

    sample_data/default_demo_batch/

Expected results:

| File | Expected Result | What it Demonstrates |
|---|---|---|
| `old_tom_label.txt` | `PASS` | Baseline passing label |
| `pass_linebreak_warning_label.txt` | `PASS` | Required warning text split across lines |
| `pass_proof_only_label.txt` | `PASS` | `90 Proof` recognized as equivalent to `45% ABV` |
| `review_case_old_tom_case.txt` | `PASS` | Human-equivalent casing/formatting |
| `bad_warning_label.txt` | `FAIL` | Non-standard warning wording |
| `fail_abv_mismatch_label.txt` | `FAIL` | ABV mismatch |
| `fail_missing_warning_label.txt` | `FAIL` | Missing government warning |
| `fail_net_contents_mismatch_label.txt` | `FAIL` | Net contents mismatch |
| `fail_titlecase_warning_label.txt` | `FAIL` | `Government Warning` title case instead of exact all-caps prefix |

### Country-origin scenario

To test the import country-origin case, upload:

    sample_data/special_scenarios/country_origin_jamaica_label.txt

Use these sidebar values:

| Field | Value |
|---|---|
| Brand Name | `OLD TOM DISTILLERY` |
| Class/Type | `Kentucky Straight Bourbon Whiskey` |
| Alcohol Content | `45% Alc./Vol. (90 Proof)` |
| Net Contents | `750 mL` |
| Producer | `Old Tom Distillery, Louisville, KY` |
| Country of origin | `Jamaica` |

Expected result: `PASS`.

If the country field is left blank, the expected result is `REVIEW`, because the label appears to state `Product of Jamaica` but the application field is empty.

### STONE'S THROW scenario

To test Dave's case/punctuation nuance, upload:

    sample_data/special_scenarios/review_stones_throw_case_label.txt

Change the sidebar value:

| Field | Value |
|---|---|
| Brand Name | `Stone's Throw` |

Expected result: `PASS`, because the label text `STONE'S THROW` and application value `Stone's Throw` are treated as human-equivalent.

If the default brand value `OLD TOM DISTILLERY` is left in the sidebar, the expected result is `FAIL`, because that is a different brand.

### What to look for during review

The prototype demonstrates:

1. **Single-label review** using application fields entered in the sidebar.
2. **Batch upload** for multiple labels at once.
3. **Fast local checks** without relying on external AI APIs.
4. **Strict government-warning validation** where exact legal wording matters.
5. **Fuzzy matching** for obvious human-equivalent differences such as casing, punctuation, and spacing.
6. **Downloadable CSV and JSON results** for audit/review workflows.

### Suggested reviewer path

1. Run the tests with `python -m pytest -q`.
2. Start the app with `python -m streamlit run app.py`.
3. Upload the default demo batch from `sample_data/default_demo_batch/`.
4. Confirm that the app separates passing labels from intentionally failing labels.
5. Test the country-origin scenario with Country of origin set to `Jamaica`.
6. Test the STONE'S THROW scenario with Brand Name set to `Stone's Throw`.
7. Download the CSV/JSON results.
8. Review the documented assumptions and limitations.

## Git Ignore Notes

This repository should not include the virtual environment or local cache files.

The `.gitignore` should exclude:

```text
.venv/
venv/
env/
__pycache__/
.pytest_cache/
.streamlit/secrets.toml
labelguard_verification_results.csv
labelguard_verification_results.json
```

Before committing, check:

```bash
git status
git status --ignored
```

If `.venv/` was accidentally staged, remove it from Git tracking:

```bash
git rm -r --cached .venv
```

## Assumptions and Limitations

This prototype is designed as a standalone proof of concept for alcohol label verification. It focuses on fast, transparent checks that help compliance agents identify obvious matches, likely mismatches, and labels that need human review. The goal is not to replace final compliance judgment, but to reduce repetitive field-matching work and make review faster.

| Area | Current Prototype Behavior | Assumption / Limitation | Possible Production Improvement |
|---|---|---|---|
| COLA integration | Runs as a standalone Streamlit application | The prototype does not connect to the COLA system, authentication services, or production TTB infrastructure | Integrate with COLA only after security review, access control design, audit logging, and procurement approval |
| Label uploads | Supports text files and common image formats | Text files are the most reliable demo path; image OCR quality depends on local Tesseract and image clarity | Add layout-aware OCR, bounding boxes, confidence scores, and preprocessing for glare, skew, rotation, and low contrast |
| Batch review | Allows multiple files to be uploaded and checked at once | Batch results are generated in-memory during the session and are not stored permanently | Add queue management, persistent review history, audit trails, and exportable batch reports |
| Speed | Uses lightweight local parsing and matching | Plain-text labels should process quickly; image OCR may be slower depending on file size and OCR environment | Add performance benchmarks, asynchronous processing, cached OCR results, and optimized document pipelines |
| Brand/class matching | Uses normalized and fuzzy text comparison | Obvious human-equivalent differences such as casing, spacing, and punctuation may be treated as acceptable or review-worthy | Add configurable agency rules for when differences should pass, fail, or require supervisor review |
| Alcohol content | Parses common ABV and proof-style expressions | The prototype checks the application value against the extracted label text, but it does not currently apply different alcohol-content rules by beverage type | Add beverage-specific rule profiles for distilled spirits, wine, malt beverages, and imports |
| Net contents | Parses common metric and U.S. volume expressions | The prototype checks numeric equivalence within a small tolerance, but it does not currently validate beverage-specific container-size rules | Add official container-size validation by beverage type and regulatory category |
| Government warning | Checks for the required warning text and all-caps `GOVERNMENT WARNING:` wording | OCR/plain text can verify wording, but cannot reliably prove bold styling, font size, placement, or separation from other text | Add image/PDF layout analysis to validate boldness, font size, placement, contrast, and separation |
| Country of origin | Checks provided country-origin values and flags explicit label origin text when the application country field is blank | The prototype detects common phrases such as `Product of Jamaica`, but it does not fully infer import status from all possible label wording | Add stronger import-status logic, country-name normalization, and required-field validation based on product origin |
| Human judgment | Produces `PASS`, `REVIEW`, or `FAIL` style results | Nuanced compliance decisions still require trained reviewer judgment | Add reviewer notes, supervisor override, decision history, and confidence calibration from real review outcomes |
| Data storage | Does not store uploaded labels or results after the session | This reduces prototype privacy risk but means there is no long-term audit trail | Add secure storage only after retention, privacy, and federal compliance requirements are defined |
| Cloud/API usage | Avoids external AI APIs | This assumes the prototype may be tested in a restricted network environment where outbound API calls may be blocked | For production, evaluate approved government cloud services or Azure-hosted OCR/ML services under appropriate security controls |
| Accessibility | Uses Streamlit’s default accessible UI components | The prototype has not undergone formal Section 508/accessibility testing | Perform keyboard navigation, screen-reader, color contrast, and usability testing with actual compliance agents |
| Scope | Focuses on common label/application matching checks | The prototype does not currently implement separate rule engines for distilled spirits, wine, or malt beverages; the beverage-type concept is treated as future scope | Expand into beverage-specific rule profiles only after the core workflow is validated with users |

### Summary of Key Trade-offs

- The prototype prioritizes **speed, clarity, and reliability** over complex AI automation.
- It uses deterministic checks where exact compliance matters, especially for the government warning statement.
- It uses fuzzy matching only where human reviewers would likely recognize two values as equivalent.
- It avoids storing data or calling external APIs to keep the prototype simple and safer for a government-style review environment.
- Final compliance decisions should remain with trained TTB reviewers, especially when typography, layout, image quality, or regulatory nuance matters.
## Future Improvements

* Add bounding-box OCR overlays showing where each required field was found.
* Add image preprocessing for skew, glare, and low contrast.
* Add beverage-specific rule profiles for distilled spirits, wine, malt beverages, and imports.
* Add accessibility testing for keyboard-only and screen-reader workflows.
* Add confidence calibration using real review outcomes.
* Add a side-by-side view of application data and extracted label text.
* Add Azure deployment templates for government cloud environments.
* Add audit logs for reviewer decisions in a secure production version.
