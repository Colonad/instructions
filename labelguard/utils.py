from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional, Tuple


def normalize_for_compare(text: str) -> str:
    """Normalize text for human-equivalent comparisons, not legal exactness."""
    text = unicodedata.normalize("NFKD", text or "")
    text = text.casefold()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = re.sub(r"[^a-z0-9%./' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def similarity(a: str, b: str) -> float:
    a_norm = normalize_for_compare(a)
    b_norm = normalize_for_compare(b)
    if not a_norm and not b_norm:
        return 1.0
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def contains_fuzzy(needle: str, haystack: str, threshold: float = 0.92) -> Tuple[bool, float, str]:
    """Return whether needle approximately appears inside haystack.

    The method checks exact normalized containment first, then slides a window over
    tokens. This is intentionally lightweight so batch uploads remain fast.
    """
    needle_norm = normalize_for_compare(needle)
    hay_norm = normalize_for_compare(haystack)

    if not needle_norm:
        return True, 1.0, ""
    if needle_norm in hay_norm:
        return True, 1.0, needle

    needle_tokens = needle_norm.split()
    hay_tokens = hay_norm.split()
    if not needle_tokens or not hay_tokens:
        score = similarity(needle, haystack)
        return score >= threshold, score, haystack[:120]

    window = max(1, len(needle_tokens))
    best_score = 0.0
    best_text = ""
    for size in {window - 1, window, window + 1, window + 2}:
        if size <= 0:
            continue
        for i in range(0, max(1, len(hay_tokens) - size + 1)):
            candidate = " ".join(hay_tokens[i:i + size])
            score = SequenceMatcher(None, needle_norm, candidate).ratio()
            if score > best_score:
                best_score = score
                best_text = candidate
    return best_score >= threshold, best_score, best_text


def extract_abv_percent(text: str) -> Optional[float]:
    text = text or ""
    patterns = [
        r"(?P<abv>\d{1,2}(?:\.\d+)?)\s*%\s*(?:alc\.?\s*/?\s*vol\.?|abv|alcohol\s+by\s+volume)?",
        r"(?:alc\.?\s*/?\s*vol\.?|abv|alcohol\s+by\s+volume)\s*(?P<abv>\d{1,2}(?:\.\d+)?)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group("abv"))

    proof_match = re.search(r"(?P<proof>\d{2,3}(?:\.\d+)?)\s*proof", text, flags=re.IGNORECASE)
    if proof_match:
        return float(proof_match.group("proof")) / 2.0
    return None


def parse_abv_from_expected(expected: str) -> Optional[float]:
    return extract_abv_percent(expected)


_UNIT_FACTORS_TO_ML = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "litre": 1000.0,
    "litres": 1000.0,
    "fl oz": 29.5735,
    "floz": 29.5735,
    "fluid ounce": 29.5735,
    "fluid ounces": 29.5735,
}


def _normalize_unit(unit: str) -> str:
    unit = normalize_for_compare(unit).replace(".", "")
    unit = unit.replace("fl oz", "fl oz").strip()
    if unit in {"m l", "m l."}:
        return "ml"
    return unit


def extract_net_contents_ml(text: str) -> Optional[float]:
    text = text or ""
    pattern = re.compile(
        r"(?P<amount>\d{1,5}(?:\.\d+)?)\s*(?P<unit>m\s*l\.?|ml\.?|milliliters?|l\.?|liters?|litres?|fl\.?\s*oz\.?|fluid\s+ounces?)",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        amount = float(match.group("amount"))
        unit = _normalize_unit(match.group("unit"))
        unit = unit.replace("m l", "ml").replace("fl oz", "fl oz")
        factor = _UNIT_FACTORS_TO_ML.get(unit)
        if factor:
            return amount * factor
    return None


def render_ml(value: Optional[float]) -> str:
    if value is None:
        return "not found"
    if abs(value - round(value)) < 0.05:
        return f"{round(value):,} mL"
    return f"{value:,.1f} mL"
