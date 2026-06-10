from __future__ import annotations

import re
import time
from typing import List, Optional

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


_COUNTRY_ORIGIN_PATTERNS = [
    r"\b(?:product\s+of|produced\s+in|made\s+in|imported\s+from)\s+(?P<country>[A-Za-z][A-Za-z .'-]{1,40})(?:[\n,.]|$)",
    r"\bcountry\s+of\s+origin\s*:?\s*(?P<country>[A-Za-z][A-Za-z .'-]{1,40})(?:[\n,.]|$)",
]


def _first_nonempty_lines(text: str, max_lines: int) -> str:
    """Return the first non-empty label lines as a smaller search area."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return "\n".join(lines[:max_lines])


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


def _field_match_near_top(
    field: str,
    expected: str,
    label_text: str,
    max_lines: int,
    threshold: float = 0.92,
) -> CheckResult:
    """Check front-label fields in the top lines only.

    This prevents a producer/address line from accidentally satisfying the brand-name
    check. For example, a STONE'S THROW label should not pass the brand check just
    because the producer line says Old Tom Distillery.
    """
    top_text = _first_nonempty_lines(label_text, max_lines=max_lines)
    return _field_match(field, expected, top_text, threshold=threshold)


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


def _detect_country_origin(label_text: str) -> Optional[str]:
    """Detect common country-of-origin wording in label text.

    This intentionally does not try to infer every possible country. It only catches
    explicit origin phrases such as "Product of Jamaica" or "Imported from France".
    """
    for pattern in _COUNTRY_ORIGIN_PATTERNS:
        match = re.search(pattern, label_text or "", flags=re.IGNORECASE)
        if not match:
            continue
        country = re.sub(r"\s+", " ", match.group("country")).strip(" .,-")
        country = re.sub(r"\s+GOVERNMENT\s+WARNING.*$", "", country, flags=re.IGNORECASE).strip()
        if country:
            return country
    return None


def _country_origin_match(expected: str, label_text: str) -> Optional[CheckResult]:
    """Validate country of origin only when relevant information exists.

    Rules:
    - Application country filled + matching label country => PASS/REVIEW.
    - Application country filled + no matching label country => FAIL.
    - Application country blank + label appears to state origin => REVIEW.
    - Application country blank + no origin wording => no check emitted.
    """
    expected = (expected or "").strip()
    observed_country = _detect_country_origin(label_text)

    if expected:
        ok, score, observed = contains_fuzzy(expected, label_text, threshold=0.90)
        if ok and score >= 0.995:
            return CheckResult(
                "Country of Origin",
                Status.PASS,
                expected,
                observed_country or expected,
                "Country of origin matches the application value.",
                score,
            )
        if ok:
            return CheckResult(
                "Country of Origin",
                Status.REVIEW,
                expected,
                observed_country or observed,
                "Close country-of-origin match found; reviewer should confirm.",
                score,
            )
        return CheckResult(
            "Country of Origin",
            Status.FAIL,
            expected,
            observed_country or "not found",
            "Application provides a country of origin, but matching country-origin text was not found on the label.",
            score,
        )

    if observed_country:
        return CheckResult(
            "Country of Origin",
            Status.REVIEW,
            "not provided in application data",
            f"Label appears to state: {observed_country}",
            "Country-origin wording appears on the label, but the application country-of-origin field was left blank.",
            0.75,
        )

    return None


def overall_status(checks: List[CheckResult]) -> Status:
    if any(check.status == Status.FAIL for check in checks):
        return Status.FAIL
    if any(check.status == Status.REVIEW for check in checks):
        return Status.REVIEW
    return Status.PASS


def verify_label_text(filename: str, application: ApplicationData, label_text: str) -> VerificationReport:
    start = time.perf_counter()
    checks: List[CheckResult] = [
        _field_match_near_top("Brand Name", application.brand_name, label_text, max_lines=4, threshold=0.90),
        _field_match_near_top("Class/Type", application.class_type, label_text, max_lines=6, threshold=0.88),
        _abv_match(application.alcohol_content, label_text),
        _net_contents_match(application.net_contents, label_text),
        _warning_match(label_text),
    ]

    if application.producer_name_address.strip():
        checks.append(_field_match("Producer/Bottler Name and Address", application.producer_name_address, label_text, threshold=0.82))

    country_check = _country_origin_match(application.country_of_origin, label_text)
    if country_check is not None:
        checks.append(country_check)

    elapsed = time.perf_counter() - start
    return VerificationReport(
        filename=filename,
        elapsed_seconds=elapsed,
        overall_status=overall_status(checks),
        checks=checks,
        extracted_text=label_text,
    )
