from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app.utils.text import clean_text


def parse_pdf_bytes(file_bytes: bytes) -> tuple[str, int]:
    reader = PdfReader(BytesIO(file_bytes), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    raw_text = "\n\n".join(pages)
    cleaned = clean_text(raw_text)
    if not cleaned:
        raise ValueError("No extractable text found in this PDF. Image-only resumes need OCR support.")
    return cleaned, len(reader.pages)
