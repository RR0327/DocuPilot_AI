"""Bounded OCR for scanned PDFs and uploaded PNG/JPEG, using local Tesseract.
No network calls, external image URLs, or untrusted command execution.
"""
import io

import fitz
from PIL import Image, UnidentifiedImageError
import pytesseract
from django.conf import settings

MAX_IMAGE_PIXELS = 20_000_000
MAX_OCR_PAGES = 50
MAX_OCR_CHARS = 1_000_000
OCR_DPI = 150

class OCRError(Exception):
    pass


def _configure_tesseract():
    executable = getattr(settings, "DOCUPILOT_TESSERACT_CMD", "")
    if executable:
        pytesseract.pytesseract.tesseract_cmd = executable


def _recognize(image):
    _configure_tesseract()
    if image.width * image.height > MAX_IMAGE_PIXELS:
        raise OCRError("Image exceeds OCR pixel limit")
    try:
        content = pytesseract.image_to_string(image, lang=getattr(settings, "DOCUPILOT_OCR_LANG", "eng"), timeout=25)
    except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError, RuntimeError) as exc:
        raise OCRError("OCR engine unavailable or unsuccessful; check Tesseract installation and OCR language packs") from exc
    if len(content) > MAX_OCR_CHARS:
        raise OCRError("OCR text exceeds supported page limit")
    return content


def validate_image(raw, kind):
    try:
        with Image.open(io.BytesIO(raw)) as im:
            expected = "PNG" if kind == "png" else "JPEG"
            if im.format != expected or im.width * im.height > MAX_IMAGE_PIXELS or im.width < 1 or im.height < 1:
                raise OCRError("Invalid image format or unsafe dimensions")
            im.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise OCRError("Invalid or unsafe image") from exc


def ocr_image_bytes(raw, kind):
    validate_image(raw, kind)
    try:
        with Image.open(io.BytesIO(raw)) as source:
            return _recognize(source.convert("RGB"))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise OCRError("Image could not be processed") from exc


def ocr_pdf_page(page):
    # Only render pages needing OCR, with bounded dimensions and CPU time.
    rect = page.rect
    if rect.width <= 0 or rect.height <= 0:
        raise OCRError("Invalid PDF page dimensions")
    scale = min(OCR_DPI / 72, (MAX_IMAGE_PIXELS / (rect.width * rect.height)) ** .5)
    if scale <= 0:
        raise OCRError("Invalid PDF render scale")
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
        if pix.width * pix.height > MAX_IMAGE_PIXELS:
            raise OCRError("PDF rendered image exceeds OCR pixel limit")
        with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
            return _recognize(image)
    except (OSError, ValueError) as exc:
        raise OCRError("PDF page could not be rendered for OCR") from exc
