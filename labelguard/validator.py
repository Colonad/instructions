from __future__ import annotations

import time
from typing import List

from .models import ApplicationData, CheckResult, Status, VerificationReport
from .utils import (
    contains_fuzzy,
    extract_abv_percent,
    extract_net_contents_ml,
    normalize_for_compare,
    normalize_whitespace,
    parse_abv_from_expected,
    render_ml,
)

# Required warning statement from the Alcoholic Beverage Labeling Act / 27 CFR Part 16.
GOVERNMENT_WARNING_EXACT = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or operate "
    "machinery, and may cause health problems."
)


def _field_match(field: str, expected: str, label_text: str, threshold: float = 0.92) -> CheckResult:
    expected = expected.strip()
    if not expected:
        return CheckResult(
            field=field,
            status=Status.REVIEW,
            expected="not provided",
            observed="not checked",
            message="No expected value was provided for this application field.",
            confidence=0.0,
        )

    ok, score, observed = contains_fuzzy(expected, label_text, threshold=threshold)
    if ok and score >= 0.995:
        return CheckResult(field, Status.PASS, expected, expected, "Exact or normalized exact match found.", score)
    if ok:
        return CheckResult(
            field,
            Status.REVIEW,
            expected,
            observed,
            "Close human-equivalent match found; agent should confirm capitalization/punctuation is acceptable.",
            score,
        )
    return CheckResult(
        field,
        Status.FAIL,
        expected,
        observed or "not found",
        "Expected field was not found on the label text.",
        score,
    )


def _abv_match(expected: str, label_text: str, tolerance: float = 0.15) -> CheckResult:
    expected_value = parse_abv_from_expected(expected)
    observed_value = extract_abv_percent(label_text)
    if expected_value is None:
        return CheckResult("Alcohol Content", Status.REVIEW, expected or "not provided", "not checked", "Could not parse expected ABV.")
    if observed_value is None:
        return CheckResult("Alcohol Content", Status.FAIL, f"{expected_value:g}%", "not found", "Could not find ABV or proof on label.")
    delta = abs(expected_value - observed_value)
    if delta <= tolerance:
        return CheckResult(
            "Alcohol Content",
            Status.PASS,
            f"{expected_value:g}% ABV",
            f"{observed_value:g}% ABV",
            f"ABV matches within ±{tolerance:g}% tolerance.",
            max(0.0, 1.0 - delta),
        )
    return CheckResult(
        "Alcohol Content",
        Status.FAIL,
        f"{expected_value:g}% ABV",
        f"{observed_value:g}% ABV",
        "ABV on label does not match the application value.",
        max(0.0, 1.0 - delta / 10.0),
    )


def _net_contents_match(expected: str, label_text: str, tolerance_ml: float = 2.0) -> CheckResult:
    expected_ml = extract_net_contents_ml(expected)
    observed_ml = extract_net_contents_ml(label_text)
    if expected_ml is None:
        return CheckResult("Net Contents", Status.REVIEW, expected or "not provided", "not checked", "Could not parse expected net contents.")
    if observed_ml is None:
        return CheckResult("Net Contents", Status.FAIL, render_ml(expected_ml), "not found", "Could not find net contents on label.")
    delta = abs(expected_ml - observed_ml)
    if delta <= tolerance_ml:
        return CheckResult(
            "Net Contents",
            Status.PASS,
            render_ml(expected_ml),
            render_ml(observed_ml),
            f"Net contents match within ±{tolerance_ml:g} mL tolerance.",
            max(0.0, 1.0 - delta / max(tolerance_ml, 1.0)),
        )
    return CheckResult(
        "Net Contents",
        Status.FAIL,
        render_ml(expected_ml),
        render_ml(observed_ml),
        "Net contents on label do not match the application value.",
        max(0.0, 1.0 - delta / max(expected_ml, 1.0)),
    )


def _warning_match(label_text: str) -> CheckResult:
    compact_label = normalize_whitespace(label_text)
    compact_expected = normalize_whitespace(GOVERNMENT_WARNING_EXACT)
    exact_present = compact_expected in compact_label

    if exact_present:
        # OCR/plain text cannot verify bold. The tool flags wording/case only.
        return CheckResult(
            "Government Health Warning",
            Status.PASS,
            compact_expected,
            compact_expected,
            "Exact required wording and all-caps GOVERNMENT WARNING prefix found. Bold formatting still requires visual confirmation.",
            1.0,
        )

    # Detect likely case-only or punctuation-only issue separately.
    if normalize_for_compare(compact_expected) in normalize_for_compare(compact_label):
        return CheckResult(
            "Government Health Warning",
            Status.FAIL,
            compact_expected,
            "case/punctuation variant found",
            "Warning wording appears semantically present but not exact. The government-warning statement must be exact.",
            0.85,
        )

    ok, score, observed = contains_fuzzy(compact_expected, compact_label, threshold=0.82)
    if ok:
        return CheckResult(
            "Government Health Warning",
            Status.FAIL,
            compact_expected,
            observed,
            "A similar warning was found, but it is not the exact required statement.",
            score,
        )
    return CheckResult(
        "Government Health Warning",
        Status.FAIL,
        compact_expected,
        "not found",
        "Required government health warning was not found.",
        score,
    )


def overall_status(checks: List[CheckResult]) -> Status:
    if any(check.status == Status.FAIL for check in checks):
        return Status.FAIL
    if any(check.status == Status.REVIEW for check in checks):
        return Status.REVIEW
    return Status.PASS


def verify_label_text(filename: str, application: ApplicationData, label_text: str) -> VerificationReport:
    start = time.perf_counter()
    checks: List[CheckResult] = [
        _field_match("Brand Name", application.brand_name, label_text, threshold=0.90),
        _field_match("Class/Type", application.class_type, label_text, threshold=0.88),
        _abv_match(application.alcohol_content, label_text),
        _net_contents_match(application.net_contents, label_text),
        _warning_match(label_text),
    ]

    if application.producer_name_address.strip():
        checks.append(_field_match("Producer/Bottler Name and Address", application.producer_name_address, label_text, threshold=0.82))
    if application.country_of_origin.strip():
        checks.append(_field_match("Country of Origin", application.country_of_origin, label_text, threshold=0.90))

    elapsed = time.perf_counter() - start
    return VerificationReport(
        filename=filename,
        elapsed_seconds=elapsed,
        overall_status=overall_status(checks),
        checks=checks,
        extracted_text=label_text,
    )
