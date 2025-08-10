from __future__ import annotations
import mimetypes
import os
from typing import Optional

import pdfplumber
from PIL import Image

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore


def detect_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def extract_text(file_path: str) -> str:
    """Best-effort text extraction.
    - PDF: extract embedded text via pdfplumber
    - Image: use Tesseract if available
    - Other: return empty string
    """
    mime = detect_mime(file_path)
    if mime == "application/pdf":
        return _extract_text_from_pdf(file_path)
    if mime and mime.startswith("image/"):
        return _extract_text_from_image(file_path)
    return ""


def _extract_text_from_pdf(pdf_path: str) -> str:
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            texts.append(txt)
    return "\n".join(texts).strip()


def _extract_text_from_image(image_path: str) -> str:
    if pytesseract is None:
        return ""
    img = Image.open(image_path)
    # Use LSTM engine; assume a general block of text
    config = "--oem 1 --psm 6"
    try:
        return pytesseract.image_to_string(img, config=config)
    except Exception:
        return ""