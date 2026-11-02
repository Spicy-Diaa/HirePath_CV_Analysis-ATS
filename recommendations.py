"""Personalised recommendations built from what was actually found in the uploaded CV."""
from .detector import MISSING, IMPROVE

HIGH, MEDIUM, LOW = "High", "Medium", "Low"
_ORDER = {HIGH: 0, MEDIUM: 1, LOW: 2}
_ITEM_PRIORITY = {"name": HIGH, "email": HIGH, "phone": HIGH, "experience": HIGH, "education": HIGH,
                  "skills": HIGH, "summary": MEDIUM, "projects": MEDIUM, "location": MEDIUM,
                  "soft_skills": LOW, "certifications": LOW, "languages": LOW}


def build_recommendations(items, checks, metrics):
    recs = []

    for it in items:
        if it["status"] in (MISSING, IMPROVE) and it["fix"]:
            recs.append({"priority": _ITEM_PRIORITY.get(it["key"], MEDIUM),
                         "title": f"{it['label']}: " + ("add it" if it["status"] == MISSING else "improve it"),
                         "detail": f"{it['detail']} {it['fix']}"})

    for c in checks:
        if c["status"] in ("Problem", "Needs Improvement") and c["fix"]:
            recs.append({"priority": HIGH if c["status"] == "Problem" else MEDIUM,
                         "title": f"Formatting - {c['name']}", "detail": f"{c['detail']} {c['fix']}"})

    b, q = metrics["bullets"], metrics["quantified"]
    if b >= 3 and q / b < 0.3:
        recs.append({"priority": MEDIUM, "title": "Add measurable achievements",
                     "detail": f"Only {q} of {b} experience/project lines contain numbers. Add results such as "
                               "'reduced load time by 30%' or 'built a dashboard used by 50 students'."})
    if b >= 3 and metrics["action_verb_lines"] / b < 0.3:
        recs.append({"priority": LOW, "title": "Start bullets with action verbs",
                     "detail": f"Only {metrics['action_verb_lines']} of {b} lines start with a strong verb "
                               "(Developed, Built, Designed, Automated...)."})

    sc = metrics["skill_count"]
    if sc >= 8 and not metrics["skills_grouped"]:
        recs.append({"priority": LOW, "title": "Organize the skills section",
                     "detail": f"Your skills list has {sc} items in one block. Group them, e.g. "
                               "'Languages: ...', 'Frameworks: ...', 'Tools: ...'."})
    elif 0 < sc < 5:
        recs.append({"priority": MEDIUM, "title": "List more skills",
                     "detail": f"Only {sc} skill(s) were detected. Add the tools and technologies you really use."})

    missing_links = [n for n, ok in (("LinkedIn", metrics["has_linkedin"]), ("GitHub", metrics["has_github"])) if not ok]
    if missing_links:
        recs.append({"priority": LOW, "title": "Add professional links",
                     "detail": "No " + " or ".join(missing_links) + " link was found. Add it as plain text in the header."})

    if not recs:
        recs.append({"priority": LOW, "title": "Your CV looks ATS-friendly",
                     "detail": "No significant gaps were detected. Tailor the keywords to each job you apply for."})
    recs.sort(key=lambda r: _ORDER[r["priority"]])
    return recs
