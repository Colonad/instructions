from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO


def extract_text_from_upload(filename: str, data: bytes) -> str:
    """Extract text from uploaded TXT/image files.

    TXT files are treated as already-extracted OCR text, which makes demos and tests
    deterministic. Image OCR is local-only through Tesseract when available; no cloud
    APIs are called.
    """
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8", errors="replace")

    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp"}:
        try:
            from PIL import Image
            import pytesseract
        except Exception as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError(
                "Image OCR requires Pillow and pytesseract. Install requirements and the Tesseract OCR system package."
            ) from exc

        image = Image.open(BytesIO(data))
        # Keep preprocessing intentionally conservative to avoid damaging label text.
        return pytesseract.image_to_string(image)

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}. Upload TXT or common image files.")
