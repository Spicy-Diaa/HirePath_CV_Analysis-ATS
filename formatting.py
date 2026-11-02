"""ATS formatting / parsing checks. Each check returns Good / Needs Improvement / Problem / Skipped."""
import re

GOOD, IMPROVE, PROBLEM, SKIPPED = "Good", "Needs Improvement", "Problem", "Skipped"

MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
RE_MONTH_YEAR = re.compile(r"\b" + MONTHS + r"\s+(?:19|20)\d{2}\b", re.I)
RE_NUMERIC = re.compile(r"\b(?:0?[1-9]|1[0-2])\s*[/.\-]\s*(?:19|20)\d{2}\b")
RE_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
BULLET_START = re.compile(r"^\s*[•●▪■◦‣▸►➢➤✓\-–*·\uf000-\uf8ff\x7f\x01-\x08]")
ICON_CHARS = re.compile("[\ue000-\uf8ff\u2600-\u26ff\u2700-\u27bf\U0001F300-\U0001FAFF]")


def _check(key, category, name, status, detail, fix=""):
    return {"key": key, "category": category, "name": name, "status": status, "detail": detail, "fix": fix}


def _text_extraction(ext):
    text = ext["text"]
    n = max(len(text), 1)
    garbage = text.count("\ufffd") + text.count("(cid:") * 6
    weird = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
    ratio = (garbage + weird) / n
    toks = text.split()
    spaced = (sum(1 for t in toks if len(t) == 1 and t.isalpha()) / max(len(toks), 1))
    avg = sum(ext["chars_per_page"]) / max(ext["pages"], 1)
    if ratio > 0.05:
        return _check("text_extraction", "parsing", "Text extraction quality", PROBLEM,
                      f"About {ratio:.0%} of the extracted text is unreadable symbols.",
                      "Re-export the CV from Word/Google Docs using a standard font (Arial, Calibri) instead of 'print to PDF' from design tools.")
    if ratio > 0.01 or spaced > 0.30:
        why = "letters appear spaced out" if spaced > 0.30 else "some characters could not be read"
        return _check("text_extraction", "parsing", "Text extraction quality", IMPROVE,
                      f"Text was extracted, but {why}.",
                      "Avoid decorative fonts and letter-spacing; use standard fonts and normal spacing.")
    return _check("text_extraction", "parsing", "Text extraction quality", GOOD,
                  f"Clean selectable text was extracted (~{int(avg)} characters per page).")


def _hidden_in_images(ext, det):
    contact_missing = [k for k in ("email", "phone", "name") if not det["contact"].get(k)]
    if ext["images"] == 0:
        return _check("hidden_info", "parsing", "Information inside images", GOOD,
                      "No embedded images were found, so everything is selectable text.")
    if contact_missing:
        return _check("hidden_info", "parsing", "Information inside images", PROBLEM,
                      f"The CV contains {ext['images']} image(s) and the {', '.join(contact_missing)} could not be read as text. "
                      "It may be embedded in an image or icon.",
                      "Type your contact details as plain text in the header; never place them inside images.")
    return _check("hidden_info", "parsing", "Information inside images", GOOD,
                  f"{ext['images']} image(s) found, but your contact details are readable as text.")


def _layout(ext):
    """Detect side-by-side columns / table cells from the x,y position of text fragments."""
    rows = {}
    for pno, x, y, fs, text in ext.get("fragments", []):
        rows.setdefault((pno, round(y / 3)), []).append((x, fs, text))
    if not rows:
        return _check("layout", "format", "Columns / tables", SKIPPED, "Layout analysis was not available for this file.")
    gapped = 0
    for frs in rows.values():
        frs.sort()
        for (x1, fs1, t1), (x2, _, _) in zip(frs, frs[1:]):
            if x2 - (x1 + 0.45 * fs1 * len(t1.strip())) > 60:  # a wide empty gap inside one line
                gapped += 1
                break
    ratio = gapped / len(rows)
    pipes = sum(1 for l in ext["text"].splitlines() if l.count("|") >= 3)
    if ratio > 0.35:
        return _check("layout", "format", "Columns / tables", PROBLEM,
                      f"About {ratio:.0%} of lines are split into side-by-side columns or table cells.",
                      "Use a single-column layout. Many ATS read columns line-by-line and mix up sections.")
    if ratio > 0.15 or pipes > 3:
        return _check("layout", "format", "Columns / tables", IMPROVE,
                      "Some parts of the CV look like columns or a table (e.g. a sidebar or skills grid).",
                      "Prefer a single column; present skills as a simple comma-separated list.")
    return _check("layout", "format", "Columns / tables", GOOD, "The layout reads as a single column.")


def _images_icons(ext):
    text = ext["text"]
    icons = 0
    for line in text.splitlines():
        body = BULLET_START.sub("", line, count=1)
        icons += len(ICON_CHARS.findall(body))
    problems = []
    if ext["large_images"]:
        problems.append(f"{ext['large_images']} large image(s) (photo/graphic)")
    if ext["images"] - ext["large_images"] > 3:
        problems.append(f"{ext['images'] - ext['large_images']} small images/icons")
    if icons > 3:
        problems.append(f"{icons} icon/symbol characters")
    if not problems:
        return _check("images_icons", "format", "Images, icons and symbols", GOOD, "No problematic images or icons were found.")
    status = PROBLEM if (ext["large_images"] and icons > 6) or ext["images"] > 8 else IMPROVE
    return _check("images_icons", "format", "Images, icons and symbols", status,
                  "Found " + ", ".join(problems) + ".",
                  "Remove the photo, skill-bars and decorative icons; use words instead (e.g. write 'Email:' not an envelope icon).")


def _length(ext, det):
    words = det["metrics"]["word_count"]
    pages = ext["pages"]
    if words < 150:
        return _check("length", "format", "CV length", PROBLEM, f"Only {words} words found, which is too little content.",
                      "Add detail to experience, projects and skills (aim for 300-700 words).")
    if words < 250:
        return _check("length", "format", "CV length", IMPROVE, f"{words} words ({pages} page(s)) is on the short side.",
                      "Expand projects and experience with what you built and the results.")
    if pages > 2 or words > 1100:
        return _check("length", "format", "CV length", IMPROVE, f"{pages} pages / {words} words is long.",
                      "Keep the CV to 1-2 pages; remove old or irrelevant details.")
    return _check("length", "format", "CV length", GOOD, f"{pages} page(s), {words} words: a good length.")


def _headings(det):
    m = det["metrics"]
    core = [k for k in ("education", "experience", "skills", "projects", "summary") if k in det["sections"]]
    n = m["heading_count"]
    names = ", ".join(m["headings"][:8])
    if n >= 4 and len(core) >= 3:
        return _check("headings", "organization", "Standard section headings", GOOD, f"{n} standard headings recognised: {names}.")
    if n >= 2:
        return _check("headings", "organization", "Standard section headings", IMPROVE,
                      f"Only {n} standard heading(s) recognised ({names}).",
                      "Use common headings: Summary, Education, Experience, Skills, Projects, Certifications, Languages.")
    return _check("headings", "organization", "Standard section headings", PROBLEM,
                  "Almost no standard section headings were recognised.",
                  "Use plain, common headings (Education, Experience, Skills...) rather than creative names.")


def _dates(text):
    month = RE_MONTH_YEAR.findall(text)
    numeric = RE_NUMERIC.findall(text)
    rest = RE_NUMERIC.sub(" ", RE_MONTH_YEAR.sub(" ", text))
    years = RE_YEAR.findall(rest)
    styles = [n for n, c in (("Month YYYY", month), ("MM/YYYY", numeric), ("YYYY only", years)) if c]
    if not styles:
        return _check("dates", "organization", "Date consistency", IMPROVE, "No dates were found.",
                      "Add dates to education and experience (e.g. Jan 2024 - Present).")
    # YYYY only next to another style is common (education years), so only flag clearly mixed month styles
    if len([s for s in styles if s != "YYYY only"]) >= 2 or (len(month) >= 2 and len(years) >= 3 and len(month) < len(years)):
        return _check("dates", "organization", "Date consistency", IMPROVE,
                      "Several date formats are mixed: " + ", ".join(styles) + ".",
                      "Choose one format for all dates (for example 'Jan 2024 - Mar 2025').")
    return _check("dates", "organization", "Date consistency", GOOD, "Dates use a consistent format (" + ", ".join(styles) + ").")


def _bullets(ext, det):
    lines = [l for l in ext["text"].splitlines() if l.strip()]
    bullets = sum(1 for l in lines if BULLET_START.match(l))
    exp_words = det["sections"].get("experience", {}).get("words", 0) + det["sections"].get("projects", {}).get("words", 0)
    if exp_words > 40 and bullets < 3:
        return _check("bullets", "organization", "Bullet points", IMPROVE,
                      "Experience/projects are written as long text without bullet points.",
                      "Use short bullet points (2-4 per role/project), each starting with an action verb.")
    return _check("bullets", "organization", "Bullet points", GOOD,
                  f"{bullets} bullet line(s) found." if bullets else "Not much descriptive text, so bullets are not required.")


def analyze_formatting(ext, det):
    checks = [
        _text_extraction(ext), _hidden_in_images(ext, det),
        _layout(ext), _images_icons(ext), _length(ext, det),
        _headings(det), _dates(ext["text"]), _bullets(ext, det),
    ]
    return checks
