"""Streamlit rendering of the ATS report (green = good, red = problem, orange = needs improvement)."""
from html import escape

import streamlit as st

from .report import COLORS, badge, build_html_report


def _download(result):
    html = build_html_report(result)
    kwargs = dict(label="⬇️ Download ATS report (HTML - open it and print to PDF)", data=html,
                  file_name="hire_path_ats_report.html", mime="text/html")
    try:  # on_click="ignore" keeps the page from re-running (and hiding the results) after download
        st.download_button(on_click="ignore", **kwargs)
    except TypeError:  # older Streamlit versions
        st.download_button(**kwargs)


def _rows(rows, ok_values):
    for name, status, detail, fix in rows:
        c1, c2, c3 = st.columns([2, 1.4, 5])
        c1.markdown(f"**{escape(name)}**")
        c2.markdown(badge(status), unsafe_allow_html=True)
        text = escape(detail)
        if status not in ok_values and fix:
            text += f"<br><span style='color:{COLORS['Needs Improvement']}'>💡 {escape(fix)}</span>"
        c3.markdown(text, unsafe_allow_html=True)


def render_ats_report(result):
    if result.get("error"):
        st.error(result["error"])
        if result.get("is_scanned"):
            st.info("Tip: if you can copy text from your CV when you open it in a PDF viewer, it is ATS-readable. "
                    "If you cannot, ATS software will see an empty page.")
        return

    s = result["score"]
    color = COLORS["Good"] if s["score"] >= 70 else COLORS["Needs Improvement"] if s["score"] >= 50 else COLORS["Problem"]
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"<div style='font-size:56px;font-weight:700;color:{color};line-height:1'>{s['score']}"
                    f"<span style='font-size:22px;color:#888'>/100</span></div>"
                    f"<div style='font-size:18px;color:{color}'>{escape(s['label'])}</div>", unsafe_allow_html=True)
        st.progress(s["score"] / 100)
    with right:
        for b in s["breakdown"]:
            st.markdown(f"**{escape(b['category'])}** — {b['earned']} / {b['max']}")
            st.progress(b["earned"] / b["max"] if b["max"] else 0)
    st.caption(s["disclaimer"])

    found = sum(1 for i in result["items"] if i["status"] == "Found")
    miss = sum(1 for i in result["items"] if i["status"] == "Missing")
    imp = sum(1 for i in result["items"] if i["status"] == "Needs Improvement")
    st.markdown(f"{badge('Found')} {found} &nbsp; {badge('Needs Improvement')} {imp} &nbsp; {badge('Missing')} {miss}",
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Information check", "🛠️ Formatting analysis", "💡 Recommendations"])
    with tab1:
        _rows([(i["label"], i["status"], i["detail"], i["fix"]) for i in result["items"]], {"Found"})
    with tab2:
        _rows([(c["name"], c["status"], c["detail"], c["fix"]) for c in result["checks"]], {"Good", "Skipped"})
    with tab3:
        icons = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}
        for r in result["recommendations"]:
            st.markdown(f"{icons[r['priority']]} **{escape(r['title'])}** *({r['priority']} priority)*  \n{escape(r['detail'])}")
    _download(result)
