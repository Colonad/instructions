from __future__ import annotations

import csv
import io
import json
import re
from typing import List

import pandas as pd
import streamlit as st

from labelguard.models import ApplicationData, Status
from labelguard.ocr import extract_text_from_upload
from labelguard.validator import GOVERNMENT_WARNING_EXACT, verify_label_text


st.set_page_config(
    page_title="LabelGuard AI — Alcohol Label Verification",
    page_icon="🏷️",
    layout="wide",
)

STATUS_ICON = {
    Status.PASS: "✅",
    Status.REVIEW: "⚠️",
    Status.FAIL: "❌",
}

st.title("🏷️ LabelGuard AI")
st.caption("Local-first alcohol label verification for brand, class/type, ABV, net contents, and government warning checks.")

with st.expander("What this prototype checks", expanded=False):
    st.markdown(
        """
        - Compares application fields against uploaded label text/artwork.
        - Accepts **multiple files at once** for batch review.
        - Uses local OCR for images when Tesseract is installed; no cloud API calls are made.
        - Treats obvious case/punctuation variations as **Review**, not automatic failure, except for the government warning wording.
        - Checks the health warning text exactly, but cannot verify bold formatting from OCR text alone.
        """
    )
    st.code(GOVERNMENT_WARNING_EXACT, language="text")

st.sidebar.header("Application data")
st.sidebar.write("Enter the fields from the label application.")

brand_name = st.sidebar.text_input("Brand name", "OLD TOM DISTILLERY")
class_type = st.sidebar.text_input("Class/type", "Kentucky Straight Bourbon Whiskey")
alcohol_content = st.sidebar.text_input("Alcohol content", "45% Alc./Vol. (90 Proof)")
net_contents = st.sidebar.text_input("Net contents", "750 mL")
producer_name_address = st.sidebar.text_area("Producer/bottler name and address", "Old Tom Distillery, Louisville, KY")
country_of_origin = st.sidebar.text_input("Country of origin, if imported", "")
st.sidebar.markdown("**Beverage type**")
st.sidebar.info(
    "Demo profile: distilled spirits sample label. "
    "This prototype currently applies common label/application checks rather than separate beverage-specific rule profiles."
)
beverage_type = "distilled_spirits"
application = ApplicationData(
    brand_name=brand_name,
    class_type=class_type,
    alcohol_content=alcohol_content,
    net_contents=net_contents,
    producer_name_address=producer_name_address,
    country_of_origin=country_of_origin,
    beverage_type=beverage_type,
)

with st.expander("Sample-data guide", expanded=True):
    st.markdown(
        """
        The same sidebar application data is applied to every uploaded file in a batch.

        **Default demo:** leave the sidebar values as-is and upload files from `sample_data/default_demo_batch/`.
        Some of those files are intentionally invalid and should show `FAIL`.

        **Country-origin demo:** upload `sample_data/special_scenarios/country_origin_jamaica_label.txt`.
        Set **Country of origin, if imported** to `Jamaica` for `PASS`; leave it blank to see `REVIEW`.

        **STONE'S THROW demo:** upload `sample_data/special_scenarios/review_stones_throw_case_label.txt`.
        Set **Brand name** to `Stone's Throw` to demonstrate case/punctuation-tolerant matching.
        """
    )

uploaded_files = st.file_uploader(
    "Upload label files",
    type=["txt", "md", "csv", "png", "jpg", "jpeg", "tif", "tiff", "webp", "bmp"],
    accept_multiple_files=True,
    help="For the fastest deterministic demo, upload TXT files containing OCR text. Image OCR works locally when Tesseract is installed.",
)

run = st.button("Verify labels", type="primary", use_container_width=True)

if run:
    if not uploaded_files:
        st.warning("Upload at least one label file to verify.")
        st.stop()

    reports = []
    for file in uploaded_files:
        try:
            label_text = extract_text_from_upload(file.name, file.getvalue())
            reports.append(verify_label_text(file.name, application, label_text))
        except Exception as exc:
            st.error(f"Could not process {file.name}: {exc}")

    if not reports:
        st.stop()

    summary_rows = []
    detail_rows = []
    for report in reports:
        summary_rows.append(
            {
                "File": report.filename,
                "Overall": f"{STATUS_ICON[report.overall_status]} {report.overall_status.value.upper()}",
                "Processing time (s)": round(report.elapsed_seconds, 3),
                "Failed checks": sum(check.status == Status.FAIL for check in report.checks),
                "Needs review": sum(check.status == Status.REVIEW for check in report.checks),
            }
        )
        for check in report.checks:
            detail_rows.append(
                {
                    "File": report.filename,
                    "Field": check.field,
                    "Status": check.status.value.upper(),
                    "Expected": check.expected,
                    "Observed": check.observed,
                    "Message": check.message,
                    "Confidence": round(check.confidence, 3),
                }
            )

    st.subheader("Batch summary")
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.subheader("Detailed checks")
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

    for idx, report in enumerate(reports):
        safe_filename = re.sub(r"[^A-Za-z0-9_.-]+", "-", report.filename)
        with st.expander(f"{STATUS_ICON[report.overall_status]} {report.filename} — extracted text"):
            st.text_area(
                "OCR/text output",
                report.extracted_text,
                height=220,
                key=f"text-{idx}-{safe_filename}",
            )

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=list(detail_rows[0].keys()))
    writer.writeheader()
    writer.writerows(detail_rows)

    st.download_button(
        "Download detailed CSV",
        csv_buffer.getvalue(),
        file_name="labelguard_verification_results.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download JSON report",
        json.dumps([report.to_dict() for report in reports], indent=2),
        file_name="labelguard_verification_results.json",
        mime="application/json",
    )
else:
    st.info("Enter application data, upload one or more label files, then click **Verify labels**.")
