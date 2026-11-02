"""Detects which CV items / sections are present (rule-based, no AI model)."""
import re

FOUND, MISSING, IMPROVE = "Found", "Missing", "Needs Improvement"

ITEM_ORDER = [
    ("name", "Full Name"), ("email", "Email Address"), ("phone", "Phone Number"),
    ("location", "Location"), ("summary", "Professional Summary"), ("education", "Education"),
    ("experience", "Work Experience"), ("skills", "Technical Skills"), ("soft_skills", "Soft Skills"),
    ("projects", "Projects"), ("certifications", "Certifications"), ("languages", "Languages"),
]

# heading text (lowercase, '&' -> 'and') -> section key
HEADING_ALIASES = {
    "summary": ["summary", "professional summary", "career summary", "executive summary", "profile",
                "professional profile", "personal profile", "objective", "career objective",
                "about me", "about", "personal statement", "الملخص", "نبذة عني", "نبذة", "الهدف الوظيفي"],
    "education": ["education", "academic background", "academic qualifications", "education and training",
                  "qualifications", "التعليم", "المؤهلات", "المؤهلات العلمية", "التعليم والمؤهلات"],
    "experience": ["experience", "work experience", "professional experience", "employment history",
                   "work history", "employment", "internships", "internship", "internship experience",
                   "career history", "practical experience", "الخبرات", "الخبرة", "الخبرات العملية", "الخبرة العملية"],
    "skills": ["skills", "technical skills", "core skills", "key skills", "skills and tools",
               "tools and technologies", "technologies", "technical expertise", "core competencies",
               "hard skills", "programming languages", "technical proficiencies", "skills and technologies",
               "المهارات", "مهارات", "المهارات التقنية", "المهارات الفنية"],
    "soft_skills": ["soft skills", "personal skills", "interpersonal skills", "personal strengths",
                    "المهارات الشخصية", "المهارات الناعمة"],
    "projects": ["projects", "personal projects", "academic projects", "selected projects", "key projects",
                 "project experience", "side projects", "graduation project", "المشاريع", "مشاريع", "المشروعات"],
    "certifications": ["certifications", "certificates", "certification", "courses", "training",
                       "training and courses", "courses and certifications", "licenses and certifications",
                       "licenses", "professional development", "الشهادات", "الدورات", "الدورات التدريبية"],
    "languages": ["languages", "language", "language skills", "اللغات", "اللغة"],
    # recognised only so that other sections end correctly / headings are counted
    "other": ["awards", "honors", "honors and awards", "achievements", "activities", "extracurricular activities",
              "volunteering", "volunteer experience", "volunteer work", "interests", "hobbies", "references",
              "publications", "contact", "contact information", "personal information", "personal details",
              "links", "additional information", "الجوائز", "الإنجازات", "الأنشطة", "الهوايات", "المراجع",
              "التطوع", "معلومات التواصل", "بيانات شخصية"],
}
_ALIAS_TO_KEY = {a: k for k, lst in HEADING_ALIASES.items() for a in lst}

TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "kotlin", "swift", "dart",
    "html", "css", "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "laravel", "flutter", "android", "ios", "sql", "mysql", "postgresql", "mongodb", "firebase", "oracle",
    "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras", "machine learning",
    "deep learning", "nlp", "computer vision", "power bi", "tableau", "excel", "git", "github", "docker",
    "kubernetes", "linux", "aws", "azure", "gcp", "ci/cd", "rest api", "rest apis", "figma", "selenium",
    "jira", "bash", "wireshark", "nmap", "burp suite", "streamlit", "hugging face",
]
SOFT_KEYWORDS = [
    "communication", "teamwork", "team player", "leadership", "problem solving", "problem-solving",
    "time management", "adaptability", "critical thinking", "collaboration", "creativity", "work ethic",
    "attention to detail", "self-motivated", "fast learner", "quick learner", "negotiation", "presentation",
    "analytical thinking", "emotional intelligence", "decision making", "flexibility",
]
JOB_WORDS = {
    "developer", "engineer", "analyst", "designer", "student", "manager", "intern", "specialist", "scientist",
    "resume", "cv", "curriculum", "vitae", "profile", "summary", "administrator", "consultant", "architect",
    "programmer", "graduate", "fresh", "tester", "officer", "technician", "lead", "senior", "junior",
}
PLACES = [
    "egypt", "cairo", "giza", "alexandria", "benha", "banha", "tanta", "mansoura", "qalyubia", "qalyubiyya",
    "shubra", "zagazig", "assiut", "aswan", "luxor", "ismailia", "suez", "port said", "damietta", "fayoum",
    "saudi", "riyadh", "jeddah", "uae", "dubai", "abu dhabi", "qatar", "doha", "kuwait", "oman", "jordan",
    "amman", "lebanon", "beirut", "morocco", "tunisia", "usa", "united states", "uk", "united kingdom",
    "london", "canada", "germany", "berlin", "france", "paris", "remote", "القاهرة", "الجيزة", "الإسكندرية",
    "مصر", "بنها", "القليوبية", "الرياض", "دبي", "طنطا", "المنصورة",
]
LANGUAGE_NAMES = ["arabic", "english", "french", "german", "spanish", "italian", "turkish", "chinese",
                  "russian", "العربية", "الإنجليزية", "الانجليزية", "الفرنسية", "الألمانية"]
LEVEL_WORDS = ["native", "fluent", "proficient", "intermediate", "beginner", "advanced", "basic", "mother tongue",
               "professional", "elementary", "upper-intermediate", "conversational", "bilingual",
               "a1", "a2", "b1", "b2", "c1", "c2", "اللغة الأم", "ممتاز", "جيد", "متوسط"]
BAD_EMAIL_WORDS = ["sexy", "cool", "baby", "king", "queen", "love", "hot", "crazy", "ninja", "gamer", "boy", "girl"]


# ---------------------------------------------------------------- helpers
def _norm(line):
    s = line.strip().lower().replace("&", " and ").replace("/", " ").replace("|", " ")
    s = re.sub(r"^[\W_]+|[\W_]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    toks = s.split(" ")
    if len(toks) >= 4 and all(len(t) == 1 for t in toks):  # "E D U C A T I O N"
        s = "".join(toks)
    return s


def heading_key(line):
    s = line.strip()
    if not s or len(s) > 45 or len(s.split()) > 5:
        return None
    return _ALIAS_TO_KEY.get(_norm(s))


def parse_sections(lines):
    heads = [(i, heading_key(l), l.strip()) for i, l in enumerate(lines) if heading_key(l)]
    sections = {}
    for n, (i, key, raw) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        content = [l for l in lines[i + 1:end] if l.strip()]
        if key in sections:
            sections[key]["lines"].extend(content)
        else:
            sections[key] = {"heading": raw, "lines": content}
    pre_end = heads[0][0] if heads else len(lines)
    return sections, heads, lines[:pre_end]


def _words(lines):
    return sum(len(l.split()) for l in lines)


def _has_kw(text, kw):
    return re.search(r"(?<![\w+#.])" + re.escape(kw) + r"(?![\w+#])", text) is not None


def _item(key, label, status, detail, fix=""):
    return {"key": key, "label": label, "status": status, "detail": detail, "fix": fix}


def _split_skill_items(lines):
    items = []
    for l in lines:
        l = re.sub(r"^[^\w]*", "", l)
        l = re.sub(r"^[^:]{1,30}:\s*", "", l)  # drop "Languages:" style prefixes
        items += [p.strip() for p in re.split(r"[,;•·|●▪]", l) if p.strip()]
    return items


# ---------------------------------------------------------------- detectors
def _find_name(lines):
    for l in lines[:10]:
        s = l.strip()
        low = s.lower()
        if not s or len(s) > 40 or "@" in s or re.search(r"\d", s) or "http" in low or "www." in low:
            continue
        if heading_key(s):
            continue
        words = s.replace("|", " ").split()
        if not 2 <= len(words) <= 4:
            continue
        if not all(re.fullmatch(r"[^\W\d_]+(?:[-'’.][^\W\d_]+)*\.?", w) for w in words):
            continue
        if any(w.lower().strip(".") in JOB_WORDS for w in words):
            continue
        return s
    return None


def _find_email(text):
    t = re.sub(r"\s*@\s*", "@", text)
    m = re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", t)
    return m[0] if m else None


def _find_phone(text):
    for m in re.finditer(r"(?<![\w])(\+?\(?\d[\d\s().\-]{7,17}\d)(?!\d)", text):
        cand = m.group(1)
        digits = re.sub(r"\D", "", cand)
        if not 9 <= len(digits) <= 15:
            continue
        groups = re.findall(r"\d+", cand)
        if all(len(g) == 4 and 1950 <= int(g) <= 2100 for g in groups):
            continue  # a list of years, not a phone number
        return cand.strip()
    return None


def _find_location(lines):
    head = lines[:15]
    for l in head:
        low = l.lower()
        if re.search(r"\b(address|location|based in|city)\b\s*[:\-]", low) or "العنوان" in l:
            return l.strip()
    for l in head:
        low = l.lower()
        if any(_has_kw(low, p) for p in PLACES):
            return l.strip()[:80]
    return None


def analyze(text):
    """Return dict(items, sections, headings, contact, metrics)."""
    lines = [l.rstrip() for l in text.splitlines()]
    nonempty = [l for l in lines if l.strip()]
    low = text.lower()
    sections, heads, preamble = parse_sections(nonempty)
    items = {}

    # ---- personal information
    name = _find_name(nonempty)
    items["name"] = (_item("name", "Full Name", FOUND, f"Detected: {name}") if name else
                     _item("name", "Full Name", MISSING, "No clear full name was detected at the top of the CV.",
                           "Put your full name alone on the first line, in plain text, as the biggest text on the page."))

    email = _find_email(text)
    if not email:
        items["email"] = _item("email", "Email Address", MISSING, "No email address was found in the text.",
                               "Add a professional email (e.g. firstname.lastname@gmail.com) in the header as plain text, not inside an image or icon.")
    else:
        local = email.split("@")[0].lower()
        if re.search(r"\d{4,}", local) or any(w in local for w in BAD_EMAIL_WORDS):
            items["email"] = _item("email", "Email Address", IMPROVE, f"Found {email}, but it does not look very professional.",
                                   "Use an address based on your real name, without long number strings or nicknames.")
        else:
            items["email"] = _item("email", "Email Address", FOUND, f"Detected: {email}")

    phone = _find_phone(text)
    items["phone"] = (_item("phone", "Phone Number", FOUND, f"Detected: {phone}") if phone else
                      _item("phone", "Phone Number", MISSING, "No phone number was found in the text.",
                            "Add a phone number with country code (e.g. +20 1X XXXX XXXX) in the header as plain text."))

    loc = _find_location(nonempty)
    items["location"] = (_item("location", "Location", FOUND, f"Detected: {loc}") if loc else
                         _item("location", "Location", MISSING, "No city/country was detected near the top of the CV.",
                               "Add your city and country (e.g. Cairo, Egypt) in the header. Recruiters often filter by location."))

    # ---- summary
    if "summary" in sections:
        n = _words(sections["summary"]["lines"])
        if n < 20:
            items["summary"] = _item("summary", "Professional Summary", IMPROVE, f"Summary found but very short ({n} words).",
                                     "Write 2-4 sentences (about 30-80 words): your target role, key skills and one strength.")
        elif n > 120:
            items["summary"] = _item("summary", "Professional Summary", IMPROVE, f"Summary is long ({n} words).",
                                     "Shorten it to 2-4 sentences (about 30-80 words).")
        else:
            items["summary"] = _item("summary", "Professional Summary", FOUND, f"Summary section found ({n} words).")
    else:
        paragraph = [l for l in preamble if "@" not in l and len(l.split()) >= 12]
        if sum(len(l.split()) for l in paragraph) >= 25:
            items["summary"] = _item("summary", "Professional Summary", IMPROVE,
                                     "A summary-like paragraph exists but it has no heading.",
                                     "Add a heading such as 'Professional Summary' above it so ATS software can recognise it.")
        else:
            items["summary"] = _item("summary", "Professional Summary", MISSING, "No professional summary was found.",
                                     "Add a 'Professional Summary' of 2-4 sentences under your contact details.")

    # ---- education
    if "education" in sections:
        content = sections["education"]["lines"]
        n = _words(content)
        has_year = re.search(r"\b(19|20)\d{2}\b", " ".join(content)) is not None
        if n < 5:
            items["education"] = _item("education", "Education", IMPROVE, "Education heading found but almost empty.",
                                       "List degree, field of study, university and graduation year.")
        elif not has_year:
            items["education"] = _item("education", "Education", IMPROVE, "Education found, but no year (start/end or expected graduation) was detected.",
                                       "Add the graduation year or 'Expected 2027'.")
        else:
            items["education"] = _item("education", "Education", FOUND, f"Education section found ({n} words).")
    elif re.search(r"\b(bachelor|b\.?sc|master|m\.?sc|university|faculty|college|diploma|institute)\b", low) or "جامعة" in text or "كلية" in text:
        items["education"] = _item("education", "Education", IMPROVE, "Education details appear in the text but without a clear 'Education' heading.",
                                   "Add a standard 'Education' heading above your degree.")
    else:
        items["education"] = _item("education", "Education", MISSING, "No education information was found.",
                                   "Add an 'Education' section: degree, field, university, years.")

    # ---- experience
    if "experience" in sections:
        n = _words(sections["experience"]["lines"])
        if n < 15:
            items["experience"] = _item("experience", "Work Experience", IMPROVE, f"Experience heading found but only {n} words under it.",
                                        "For each role add title, company, dates and 2-4 bullet points describing what you achieved.")
        else:
            items["experience"] = _item("experience", "Work Experience", FOUND, f"Experience section found ({n} words).")
    elif re.search(r"\b(intern|internship|trainee|freelance)\b", low) and re.search(r"\b(19|20)\d{2}\b", low):
        items["experience"] = _item("experience", "Work Experience", IMPROVE, "Experience-like content exists but there is no clear 'Experience' heading.",
                                    "Group it under a heading such as 'Work Experience' or 'Internships'.")
    else:
        items["experience"] = _item("experience", "Work Experience", MISSING, "No work experience section was found.",
                                    "If you have no jobs yet, add internships, training, freelance work or volunteering under 'Experience'.")

    # ---- technical skills
    tech_found = [k for k in TECH_KEYWORDS if _has_kw(low, k)]
    if "skills" in sections:
        count = len(_split_skill_items(sections["skills"]["lines"]))
        if count < 3:
            items["skills"] = _item("skills", "Technical Skills", IMPROVE, f"Skills section found but only {count} item(s) listed.",
                                    "List at least 5-8 relevant tools/technologies, grouped by category.")
        else:
            items["skills"] = _item("skills", "Technical Skills", FOUND, f"Skills section found ({count} items).")
    elif len(tech_found) >= 3:
        items["skills"] = _item("skills", "Technical Skills", IMPROVE,
                                f"Technical keywords exist ({', '.join(tech_found[:5])}...) but no 'Skills' heading.",
                                "Collect them under a 'Technical Skills' heading.")
    else:
        items["skills"] = _item("skills", "Technical Skills", MISSING, "No technical skills section was found.",
                                "Add a 'Technical Skills' section with your tools, languages and frameworks.")

    # ---- soft skills
    soft_found = [k for k in SOFT_KEYWORDS if _has_kw(low, k)]
    if ("soft_skills" in sections and _words(sections["soft_skills"]["lines"]) >= 2) or len(soft_found) >= 2:
        items["soft_skills"] = _item("soft_skills", "Soft Skills", FOUND,
                                     "Detected: " + (", ".join(soft_found[:5]) if soft_found else "soft skills section"))
    elif len(soft_found) == 1 or "soft_skills" in sections:
        items["soft_skills"] = _item("soft_skills", "Soft Skills", IMPROVE, "Only one soft skill was detected." if soft_found else "Soft skills heading is empty.",
                                     "Add 3-5 soft skills you can back up with an example (teamwork, communication, problem solving).")
    else:
        items["soft_skills"] = _item("soft_skills", "Soft Skills", MISSING, "No soft skills were detected.",
                                     "Add 3-5 soft skills, ideally reflected in your project or experience descriptions.")

    # ---- projects
    if "projects" in sections:
        n = _words(sections["projects"]["lines"])
        if n < 12:
            items["projects"] = _item("projects", "Projects", IMPROVE, f"Projects heading found but only {n} words under it.",
                                      "For each project add name, what it does, technologies used and a link (GitHub/demo).")
        else:
            items["projects"] = _item("projects", "Projects", FOUND, f"Projects section found ({n} words).")
    else:
        items["projects"] = _item("projects", "Projects", MISSING, "No projects section was found.",
                                  "Add 2-3 projects with technologies used and a GitHub/demo link.")

    # ---- certifications
    if "certifications" in sections:
        n = _words(sections["certifications"]["lines"])
        if n < 3:
            items["certifications"] = _item("certifications", "Certifications", IMPROVE, "Certifications heading found but almost empty.",
                                            "List certificate name, provider and year.")
        else:
            items["certifications"] = _item("certifications", "Certifications", FOUND, f"Certifications section found ({n} words).")
    elif re.search(r"\b(certificate|certified|certification|coursera|udemy|edx|udacity)\b", low):
        items["certifications"] = _item("certifications", "Certifications", IMPROVE, "Certificates are mentioned but not under a clear heading.",
                                        "Group them under a 'Certifications' heading.")
    else:
        items["certifications"] = _item("certifications", "Certifications", MISSING, "No certifications or courses were found.",
                                        "Add relevant courses/certificates (name, provider, year).")

    # ---- languages
    langs_found = [l for l in LANGUAGE_NAMES if _has_kw(low, l) or l in text]
    level_found = any(_has_kw(low, w) or w in text for w in LEVEL_WORDS)
    if "languages" in sections and _words(sections["languages"]["lines"]) >= 1:
        items["languages"] = _item("languages", "Languages", FOUND, "Languages section found.")
    elif langs_found and level_found:
        items["languages"] = _item("languages", "Languages", FOUND, "Detected: " + ", ".join(langs_found[:4]))
    elif langs_found:
        items["languages"] = _item("languages", "Languages", IMPROVE, "Language names appear but no proficiency level was detected.",
                                   "Add a 'Languages' section with levels, e.g. Arabic (Native), English (B2).")
    else:
        items["languages"] = _item("languages", "Languages", MISSING, "No spoken languages were found.",
                                   "Add a 'Languages' section with proficiency levels.")

    # ---- metrics used by formatting/recommendations
    exp_lines = sections.get("experience", {}).get("lines", []) + sections.get("projects", {}).get("lines", [])
    bullet_re = re.compile(r"^\s*[•●▪■◦‣▸►➢➤✓\-–*·\uf000-\uf8ff\x7f\x01-\x08]")
    exp_bullets = [l for l in exp_lines if bullet_re.match(l) or len(l.split()) >= 7]
    quantified = [l for l in exp_bullets if re.search(r"\d", l)]
    verbs = ("developed", "built", "designed", "created", "implemented", "led", "managed", "improved",
             "analyzed", "analysed", "optimized", "optimised", "automated", "deployed", "trained", "wrote",
             "integrated", "reduced", "increased", "launched", "achieved", "delivered", "tested", "collaborated")
    verb_lines = [l for l in exp_bullets if re.sub(r"^[^\w]+", "", l).lower().startswith(verbs)]
    skill_items = _split_skill_items(sections.get("skills", {}).get("lines", []))
    metrics = {
        "bullets": len(exp_bullets), "quantified": len(quantified), "action_verb_lines": len(verb_lines),
        "skill_count": len(skill_items),
        "skills_grouped": any(re.match(r"^[^\w]*[^:]{1,30}:", l) for l in sections.get("skills", {}).get("lines", [])),
        "has_linkedin": "linkedin" in low, "has_github": "github" in low,
        "summary_words": _words(sections["summary"]["lines"]) if "summary" in sections else 0,
        "word_count": len(text.split()),
        "heading_count": len(heads), "headings": [h[2] for h in heads],
    }
    return {
        "items": [items[k] for k, _ in ITEM_ORDER],
        "sections": {k: {"heading": v["heading"], "words": _words(v["lines"])} for k, v in sections.items()},
        "metrics": metrics,
        "contact": {"name": name, "email": email, "phone": phone, "location": loc},
    }
