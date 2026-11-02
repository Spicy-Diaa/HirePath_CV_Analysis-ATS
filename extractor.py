"""PDF text extraction + basic file-level facts for the ATS checker.

Uses pypdf only (already used by Hire Path). Never raises: problems are
returned in the "error" field so the UI can show a clear message.
"""
import io

from pypdf import PdfReader

MIN_CHARS_PER_PAGE = 60  # below this on average we treat the PDF as scanned/image-only


def _count_images(page):
    """Count image XObjects without decoding them (no Pillow needed).

    Returns (total_images, large_images) where large means >= 200x200 px
    (typically a profile photo or a graphic, not a tiny icon).
    """
    total, large = 0, 0
    try:
        resources = page.get("/Resources")
        resources = resources.get_object() if resources is not None else {}
        xobjects = resources.get("/XObject")
        if xobjects is None:
            return 0, 0
        for obj in xobjects.get_object().values():
            obj = obj.get_object()
            if obj.get("/Subtype") == "/Image":
                total += 1
                if int(obj.get("/Width", 0)) >= 200 and int(obj.get("/Height", 0)) >= 200:
                    large += 1
    except Exception:
        pass
    return total, large


def extract_pdf(pdf_bytes):
    out = {
        "error": None,
        "is_scanned": False,
        "text": "",
        "fragments": [],  # (page, x, y, font_size, text) positions, used to detect columns/tables
        "pages": 0,
        "chars_per_page": [],
        "images": 0,
        "large_images": 0,
    }
    if not pdf_bytes:
        out["error"] = "The uploaded file is empty."
        return out

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                pass
        pages = list(reader.pages)
    except Exception:
        out["error"] = ("This file could not be opened as a PDF. It may be corrupted or "
                        "password-protected. Please upload a normal, unprotected PDF.")
        return out

    out["pages"] = len(pages)
    texts = []
    for pno, page in enumerate(pages):
        frags = []

        def visitor(text, cm, tm, font_dict, font_size, _frags=frags):
            if text and text.strip():
                try:
                    x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                    y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                    _frags.append((x, y, float(font_size or 10), text))
                except Exception:
                    pass

        try:
            t = page.extract_text(visitor_text=visitor) or ""
        except Exception:
            t = ""
            frags = []
        texts.append(t)
        out["chars_per_page"].append(len(t.strip()))
        out["fragments"] += [(pno,) + f for f in frags]
        total, large = _count_images(page)
        out["images"] += total
        out["large_images"] += large

    out["text"] = "\n".join(texts)

    if out["pages"] == 0:
        out["error"] = "The PDF has no pages."
    elif sum(out["chars_per_page"]) / out["pages"] < MIN_CHARS_PER_PAGE:
        out["is_scanned"] = True
        out["error"] = ("No selectable text was found in this PDF. It looks like a scanned document "
                        "or a CV exported as images. ATS software cannot read it either. "
                        "Re-export it as a text-based PDF from Word or Google Docs.")
    return out
