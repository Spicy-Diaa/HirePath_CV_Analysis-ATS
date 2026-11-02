"""Downloadable HTML report (open in a browser, or print -> Save as PDF). No extra libraries."""
from html import escape

COLORS = {"Found": "#1e8e3e", "Good": "#1e8e3e", "Missing": "#d93025", "Problem": "#d93025",
          "Needs Improvement": "#f29900"}


def badge(status):
    c = COLORS.get(status, "#5f6368")
    return (f'<span style="background:{c};color:#fff;padding:2px 10px;border-radius:12px;'
            f'font-size:12px;font-weight:600;white-space:nowrap">{escape(status)}</span>')


def build_html_report(result):
    s = result["score"]
    rows = "".join(
        f"<tr><td>{escape(b['category'])}</td><td>{b['earned']} / {b['max']}</td><td>{escape(b['detail'])}</td></tr>"
        for b in s["breakdown"])
    items = "".join(
        f"<tr><td>{escape(i['label'])}</td><td>{badge(i['status'])}</td><td>{escape(i['detail'])}"
        + (f"<br><i>{escape(i['fix'])}</i>" if i["status"] != "Found" and i["fix"] else "") + "</td></tr>"
        for i in result["items"])
    checks = "".join(
        f"<tr><td>{escape(c['name'])}</td><td>{badge(c['status'])}</td><td>{escape(c['detail'])}"
        + (f"<br><i>{escape(c['fix'])}</i>" if c["status"] not in ("Good", "Skipped") and c["fix"] else "") + "</td></tr>"
        for c in result["checks"])
    recs = "".join(f"<li><b>[{escape(r['priority'])}] {escape(r['title'])}</b><br>{escape(r['detail'])}</li>"
                   for r in result["recommendations"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Hire Path - ATS Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;color:#202124}}
table{{border-collapse:collapse;width:100%;margin-bottom:20px}}td,th{{border:1px solid #ddd;padding:8px;vertical-align:top;font-size:14px}}
th{{background:#f1f3f4;text-align:left}}.score{{font-size:48px;font-weight:700}}li{{margin-bottom:10px}}</style></head><body>
<h1>Hire Path - General ATS Report</h1>
<div class="score">{s['score']}/100 <span style="font-size:20px">({escape(s['label'])})</span></div>
<p><i>{escape(s['disclaimer'])}</i></p>
<h2>Score breakdown</h2><table><tr><th>Category</th><th>Points</th><th>Based on</th></tr>{rows}</table>
<h2>Information check</h2><table><tr><th>Item</th><th>Status</th><th>Details</th></tr>{items}</table>
<h2>Formatting analysis</h2><table><tr><th>Check</th><th>Status</th><th>Details</th></tr>{checks}</table>
<h2>Recommendations</h2><ol>{recs}</ol></body></html>"""
