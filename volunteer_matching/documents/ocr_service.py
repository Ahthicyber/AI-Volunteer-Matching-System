"""
documents/ocr_service.py
────────────────────────
Basic OCR/text extraction service for volunteer documents.

This module uses free/local libraries only. It never raises raw exceptions to
Streamlit pages; callers receive (success, text_or_error).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from documents.document_utils import clean_extracted_text, detect_file_type, truncate_text
from utils.config import get_tesseract_cmd


def _configure_tesseract(pytesseract_module) -> None:
    """Configure pytesseract with an explicit executable path when available."""
    cmd = get_tesseract_cmd()
    if cmd:
        pytesseract_module.pytesseract.tesseract_cmd = cmd


def _tesseract_missing_message() -> str:
    return (
        "Tesseract OCR is not installed or not configured. On Windows, install Tesseract OCR and add "
        "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe to your .env, then restart Streamlit."
    )


def extract_text_from_image(file_path: str) -> tuple[bool, str]:
    """Extract text from a JPG/JPEG/PNG image using pytesseract."""
    try:
        path = Path(file_path)
        if not path.exists():
            return False, "File not found."

        from PIL import Image
        import pytesseract
        _configure_tesseract(pytesseract)

        with Image.open(path) as image:
            text = pytesseract.image_to_string(image)

        cleaned = clean_extracted_text(text)
        if not cleaned:
            return False, "OCR completed but no readable text was found."
        return True, cleaned
    except ImportError:
        return False, "OCR Python libraries are not installed. Run: pip install pytesseract pillow"
    except Exception as exc:
        message = str(exc)[:220]
        if "tesseract" in message.lower() or "not installed" in message.lower():
            return False, _tesseract_missing_message()
        return False, f"Image OCR failed safely: {message}"


def _extract_pdf_text_with_pdfplumber(file_path: str) -> str:
    """Extract selectable text from PDF pages using pdfplumber."""
    try:
        import pdfplumber

        chunks: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:8]:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
        return clean_extracted_text("\n\n".join(chunks))
    except Exception:
        return ""


def _ocr_pdf_pages_with_pymupdf(file_path: str) -> str:
    """Fallback OCR for scanned PDFs by rendering pages with PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        import pytesseract
        _configure_tesseract(pytesseract)
        from PIL import Image

        chunks: list[str] = []
        with TemporaryDirectory() as tmpdir:
            doc = fitz.open(file_path)
            try:
                for page_index in range(min(len(doc), 5)):
                    page = doc.load_page(page_index)
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
                    img_path = Path(tmpdir) / f"page_{page_index + 1}.png"
                    pix.save(str(img_path))
                    with Image.open(img_path) as image:
                        chunks.append(pytesseract.image_to_string(image))
            finally:
                doc.close()
        return clean_extracted_text("\n\n".join(chunks))
    except Exception:
        return ""


def extract_text_from_pdf(file_path: str) -> tuple[bool, str]:
    """Extract text from a PDF using selectable text first, then OCR fallback."""
    try:
        path = Path(file_path)
        if not path.exists():
            return False, "File not found."

        text = _extract_pdf_text_with_pdfplumber(str(path))
        if not text:
            text = _ocr_pdf_pages_with_pymupdf(str(path))

        cleaned = clean_extracted_text(text)
        if not cleaned:
            return False, "No readable text could be extracted from this PDF."
        return True, cleaned
    except ImportError:
        return False, "PDF OCR Python libraries are not installed. Run: pip install pdfplumber pymupdf pytesseract pillow"
    except Exception as exc:
        message = str(exc)[:220]
        if "tesseract" in message.lower() or "not installed" in message.lower():
            return False, _tesseract_missing_message()
        return False, f"PDF OCR failed safely: {message}"


def extract_text_from_document(file_path: str) -> tuple[bool, str]:
    """Extract text from a supported PDF/JPG/PNG document."""
    file_type = detect_file_type(file_path)
    if file_type == "image":
        return extract_text_from_image(file_path)
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    return False, "Unsupported document type. Please use PDF, JPG, JPEG, or PNG."
