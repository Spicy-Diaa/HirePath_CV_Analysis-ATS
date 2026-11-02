"""General ATS score (0-100) with a transparent breakdown."""
from .detector import FOUND, IMPROVE

# points available for each detected item (total = 55)
PERSONAL = {"name": 6, "email": 7, "phone": 7, "location": 5}                       # 25
SECTIONS = {"summary": 4, "education": 6, "experience": 7, "skills": 5,
            "soft_skills": 2, "projects": 3, "certifications": 2, "languages": 1}   # 30
# formatting categories: max points, check category
FORMAT_CATS = [("Readability & parsing", "parsing", 20),
               ("Formatting quality", "format", 15),
               ("Organization & consistency", "organization", 10)]

CHECK_VALUE = {"Good": 1.0, "Needs Improvement": 0.5, "Problem": 0.0}


def _item_value(status):
    return 1.0 if status == FOUND else 0.5 if status == IMPROVE else 0.0


def compute_score(items, checks):
    by_key = {i["key"]: i for i in items}
    breakdown = []

    def group(title, weights, note):
        earned = sum(w * _item_value(by_key[k]["status"]) for k, w in weights.items())
        breakdown.append({"category": title, "earned": round(earned, 1), "max": sum(weights.values()), "detail": note})

    group("Personal information", PERSONAL, "Name, email, phone and location (partial credit if they need improvement).")
    group("Important CV sections", SECTIONS, "Summary, education, experience, skills, projects, certifications, languages.")

    for title, cat, max_pts in FORMAT_CATS:
        scored = [c for c in checks if c["category"] == cat and c["status"] in CHECK_VALUE]
        if scored:
            earned = max_pts * sum(CHECK_VALUE[c["status"]] for c in scored) / len(scored)
        else:
            earned = max_pts
        names = ", ".join(c["name"].lower() for c in scored)
        breakdown.append({"category": title, "earned": round(earned, 1), "max": max_pts, "detail": f"Based on: {names}."})

    score = int(round(sum(b["earned"] for b in breakdown)))
    score = max(0, min(100, score))
    label = ("Excellent" if score >= 85 else "Good" if score >= 70 else
             "Needs work" if score >= 50 else "Poor")
    return {
        "score": score, "label": label, "breakdown": breakdown,
        "disclaimer": "This is an estimated general ATS-compatibility score based on common ATS practices. "
                      "It is not an official score from any company's ATS and does not predict hiring decisions.",
    }
