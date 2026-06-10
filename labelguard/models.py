from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class Status(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


@dataclass(frozen=True)
class ApplicationData:
    brand_name: str
    class_type: str
    alcohol_content: str
    net_contents: str
    producer_name_address: str = ""
    country_of_origin: str = ""
    beverage_type: str = "distilled_spirits"


@dataclass(frozen=True)
class CheckResult:
    field: str
    status: Status
    expected: str
    observed: str
    message: str
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(frozen=True)
class VerificationReport:
    filename: str
    elapsed_seconds: float
    overall_status: Status
    checks: List[CheckResult]
    extracted_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "overall_status": self.overall_status.value,
            "checks": [check.to_dict() for check in self.checks],
            "extracted_text": self.extracted_text,
        }
