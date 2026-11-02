import pandas as pd
import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from ats_checker import run_ats_check, render_ats_report
st.set_page_config(page_title="Hire Path", page_icon="🚀", layout="wide")

jobs = [
    {"work": "Front-End Developer", "requirements": "HTML, CSS, JavaScript, React, Web Performance"},
    {"work": "Python Back-End Developer", "requirements": "Python, Django, Flask, SQL, REST APIs"},
    {"work": "Data Analyst", "requirements": "Python, Pandas, SQL, Data Visualization, Excel"},
    {"work": "Mobile App Developer", "requirements": "Flutter, Dart, Android, iOS, Firebase, REST APIs"},
    {"work": "DevOps Engineer", "requirements": "Docker, Kubernetes, Linux, CI/CD, AWS, Git"},
    {"work": "Machine Learning Engineer", "requirements": "Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP"},
    {"work": "UI/UX Designer", "requirements": "Figma, User Research, Wireframing, Prototyping, Adobe XD"},
    {"work": "Cybersecurity Analyst", "requirements": "Network Security, Penetration Testing, Linux, Firewalls, SIEM"},
    {"work": "QA Engineer", "requirements": "Manual Testing, Selenium, Test Cases, Bug Tracking, Automation"},
    {"work": "Database Administrator", "requirements": "SQL, MySQL, PostgreSQL, Backup, Performance Tuning"},
    {"work": "Full-Stack Developer", "requirements": "HTML, CSS, JavaScript, React, Node.js, MongoDB, SQL"},
]

skill_priority = {
    "html": 10, "css": 9, "javascript": 10, "react": 9,
    "python": 10, "sql": 9, "flask": 8, "django": 8,
    "rest apis": 8, "git": 8, "docker": 8, "linux": 7,
    "node.js": 8, "mongodb": 7, "pandas": 8,
    "machine learning": 10, "tensorflow": 8, "pytorch": 8,
    "web performance": 4, "ci/cd": 6, "aws": 7,
}


@st.cache_resource
def load_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def analyze_gaps(student_text, job_requirements):
    job_skills = [s.strip().lower() for s in job_requirements.split(",")]
    text = student_text.lower()
    matched = [s for s in job_skills if s in text]
    missing = [s for s in job_skills if s not in text]
    return matched, missing


def make_roadmap(job_title, missing):
    if not missing:
        return ["Ready to apply now ✅"]
    ordered = sorted(missing, key=lambda s: skill_priority.get(s, 5), reverse=True)
    steps = [f"{i}. Learn {s.title()} and build a small project with it" for i, s in enumerate(ordered, start=1)]
    steps.append(f"{len(steps) + 1}. Add the new skills and project to your CV, then apply for {job_title}")
    return steps


st.title("🚀 Hire Path")
st.subheader("Smart Job Matching & Skill Gap Analysis")

uploaded = st.file_uploader("Upload your CV (PDF)", type=["pdf"])

if st.button("Analyze My CV"):
    if uploaded is None:
        st.warning("Please choose a PDF file first")
    else:
        with st.spinner("Analyzing your CV..."):
            model = load_model()
            reader = PdfReader(uploaded)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text() or ""

            cv_vec = model.encode([cv_text])
            results = []
            for job in jobs:
                job_vec = model.encode([job["requirements"]])
                ai_sim = round(float(cosine_similarity(cv_vec, job_vec)[0][0]) * 100, 1)
                matched, missing = analyze_gaps(cv_text, job["requirements"])
                total = len(matched) + len(missing)
                skills_match = round(len(matched) / total * 100, 1) if total else 0
                results.append({
                    "job": job["work"],
                    "skills_match": skills_match,
                    "ai_sim": ai_sim,
                    "matched": matched,
                    "missing": missing,
                    "roadmap": make_roadmap(job["work"], missing),
                })

            results.sort(key=lambda r: (r["skills_match"], r["ai_sim"]), reverse=True)

            st.success("CV analysis completed!")

            best = results[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Best Match", best["job"])
            c2.metric("Skills Match", f"{best['skills_match']}%")
            c3.metric("AI Similarity", f"{best['ai_sim']}%")

            st.subheader("Job Matching Results")
            table = pd.DataFrame([{
                "Job": r["job"],
                "Skills Match": r["skills_match"],
                "AI Similarity": r["ai_sim"],
                "Matched Skills": ", ".join(r["matched"]) or "None",
                "Missing Skills": ", ".join(r["missing"]) or "None",
            } for r in results])

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Skills Match": st.column_config.ProgressColumn(
                        "Skills Match", min_value=0, max_value=100, format="%.0f%%"
                    ),
                    "AI Similarity": st.column_config.ProgressColumn(
                        "AI Similarity", min_value=0, max_value=100, format="%.0f%%"
                    ),
                },
            )

            st.subheader("Your Learning Roadmap")
            for r in results[:5]:
                with st.expander(f"{r['job']} — {r['skills_match']}%"):
                    for step in r["roadmap"]:
                        st.write(step)
                        st.divider()
            st.header("📋 ATS CV Analysis")
            st.success("ATS section reached successfully!")
            ats_result = run_ats_check(uploaded.getvalue())
            render_ats_report(ats_result)            