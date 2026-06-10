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

| Area                    | Current Prototype Behavior                                                | Production Consideration                                                                                   |
| ----------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| COLA integration        | Standalone application only                                               | Direct integration would require authentication, authorization, audit logging, and federal security review |
| File storage            | Does not persist uploaded files                                           | Production would need retention rules and secure storage policies                                          |
| OCR                     | Supports text files immediately and image OCR when Tesseract is available | Production should improve OCR for glare, rotation, curved bottles, and low-light images                    |
| Bold text               | Extracted text can verify wording but not reliably prove bold styling     | Production would need layout-aware image/PDF analysis                                                      |
| Government warning      | Checks required wording and capitalization                                | Production should verify formatting, placement, and size requirements                                      |
| Beverage-specific rules | Focuses on common distilled spirits-style fields                          | Production should include separate rule profiles for distilled spirits, wine, and malt beverages           |
| Final decision          | Provides decision support                                                 | Human compliance reviewers should remain responsible for final determinations                              |

## Future Improvements

* Add bounding-box OCR overlays showing where each required field was found.
* Add image preprocessing for skew, glare, and low contrast.
* Add beverage-specific rule profiles.
* Add accessibility testing for keyboard-only and screen-reader workflows.
* Add confidence calibration using real review outcomes.
* Add a side-by-side view of application data and extracted label text.
* Add Azure deployment templates for government cloud environments.
* Add audit logs for reviewer decisions in a secure production version.
