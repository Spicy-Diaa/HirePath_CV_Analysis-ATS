"""General ATS CV Checker for Hire Path (independent of the job-matching code).

Usage:
    from ats_checker import run_ats_check, render_ats_report
    render_ats_report(run_ats_check(uploaded_file.getvalue()))
"""
from .extractor import extract_pdf
from .detector import analyze
from .formatting import analyze_formatting
from .scoring import compute_score
from .recommendations import build_recommendations


def run_ats_check(pdf_bytes):
    """Analyse a CV given as PDF bytes. Never raises for bad files: see result['error']."""
    ext = extract_pdf(pdf_bytes)
    if ext["error"]:
        return {"error": ext["error"], "is_scanned": ext["is_scanned"], "images": ext["images"], "pages": ext["pages"]}
    det = analyze(ext["text"])
    checks = analyze_formatting(ext, det)
    score = compute_score(det["items"], checks)
    return {
        "error": None, "is_scanned": False,
        "pages": ext["pages"], "images": ext["images"],
        "score": score, "items": det["items"], "checks": checks, "contact": det["contact"],
        "recommendations": build_recommendations(det["items"], checks, det["metrics"]),
    }


def render_ats_report(result):
    from .ui import render_ats_report as _render
    _render(result)


__all__ = ["run_ats_check", "render_ats_report"]
