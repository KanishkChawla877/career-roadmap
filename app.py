mport os
import io
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="CareerGuide AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM STYLE ----------------
st.markdown("""
<style>
.main {background-color: #f7f9fc;}
.hero {
    padding: 28px; border-radius: 18px;
    background: linear-gradient(120deg, #172554, #2563eb);
    color: white; margin-bottom: 18px;
}
.hero h1 {color: white; margin-bottom: 8px;}
.small-card {
    padding: 18px; border-radius: 14px; background: white;
    border: 1px solid #e5e7eb; min-height: 110px;
}
div.stButton > button {
    border-radius: 10px; font-weight: 600; min-height: 42px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🎯 CareerGuide AI")
    st.caption("Your personal career planning assistant")
    st.divider()
    st.subheader("🔐 API Settings")
    sidebar_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Paste your API key",
        help="Your key is not displayed in plain text. Never commit it to GitHub."
    )
    model_name = st.selectbox(
        "Gemini Model",
        ["gemini-2.5-flash", "gemini-2.0-flash"],
        index=0
    )
    st.divider()
    st.markdown("**Pages**")
    st.caption("🏠 Home · 🧑‍🎓 Student Profile · 🗺️ Roadmap · 💬 Career Chat")
    st.info("Keep your API key private. For deployment, use Streamlit Secrets.")

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <h1>Build Your Career Roadmap 🚀</h1>
    <p>Explore career paths, identify skill gaps, and create a personalized learning plan.</p>
</div>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "roadmap" not in st.session_state:
    st.session_state.roadmap = ""
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- HELPERS ----------------
def get_api_key():
    if sidebar_key.strip():
        return sidebar_key.strip()
    try:
        secret_key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("GOOGLE_API_KEY", "")

def make_llm():
    key = get_api_key()
    if not key:
        raise ValueError(
            "Gemini API key nahi mili. Sidebar mein key enter karein, "
            "ya Streamlit Secrets/.env mein GOOGLE_API_KEY set karein."
        )
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=key,
        temperature=0.3,
        max_retries=1
    )

def clean_response(content):
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n\n".join(x for x in parts if x.strip())
    return str(content)

def safe_pdf_text(text):
    # Basic conversion to a PDF-friendly plain text representation.
    text = re.sub(r"```.*?```", "[Code block omitted]", text, flags=re.S)
    text = re.sub(r"[#*_`]", "", text)
    return text

def create_pdf(text):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    from xml.sax.saxutils import escape

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=0.65*inch, leftMargin=0.65*inch,
        topMargin=0.65*inch, bottomMargin=0.65*inch
    )
    styles = getSampleStyleSheet()
    story = []
    for line in safe_pdf_text(text).splitlines():
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(escape(line), styles["BodyText"]))
            story.append(Spacer(1, 3))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------- NAVIGATION TABS ----------------
home_tab, profile_tab, roadmap_tab, chat_tab = st.tabs([
    "🏠 Home", "🧑‍🎓 Student Profile", "🗺️ My Roadmap", "💬 Career Chat"
])

# ---------------- HOME ----------------
with home_tab:
    st.subheader("Welcome to CareerGuide AI")
    st.write(
        "This application helps students explore career options using their "
        "education, academic performance, interests, and current skills."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="small-card"><h3>🎯 Career Options</h3><p>Explore paths that match your interests.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="small-card"><h3>📊 Skill Gap</h3><p>Understand which skills to develop next.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="small-card"><h3>🗓️ Learning Plan</h3><p>Get a practical 6-month roadmap.</p></div>', unsafe_allow_html=True)

    st.markdown("### How it works")
    st.markdown("""
    1. Open **Student Profile** and enter your details.
    2. Add your education marks/grades (optional).
    3. Click **Generate My Career Roadmap**.
    4. Review, download, and discuss your roadmap in **Career Chat**.
    """)
    if st.session_state.roadmap:
        st.success("A roadmap is saved in this session. Open **My Roadmap** to view it.")
    else:
        st.info("No roadmap generated yet. Start with the Student Profile tab.")

# ---------------- STUDENT PROFILE ----------------
with profile_tab:
    st.subheader("🧑‍🎓 Student Profile")
    st.caption("Enter the details that apply to you. Academic scores are optional.")

    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            name = st.text_input("Full Name")
            education = st.selectbox(
                "Current Education",
                ["Class 10", "Class 11", "Class 12", "Diploma", "BCA",
                 "B.Tech / B.E.", "B.Sc.", "B.Com.", "BA", "MBA",
                 "Other Undergraduate", "Postgraduate", "Other"]
            )
            course = st.text_input("Course / Stream", placeholder="e.g., BCA, Commerce, PCM")
            interests = st.text_area("Career Interests", placeholder="e.g., Cybersecurity, Data Science")
            goal = st.text_input("Career Goal", placeholder="e.g., Become a Data Analyst")
        with right:
            skills = st.text_area("Current Skills", placeholder="e.g., Python basics, HTML, communication")
            experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Experienced"])
            study_time = st.selectbox("Study Time Available", ["1 hour/day", "2 hours/day", "3 hours/day", "4+ hours/day"])
            location = st.text_input("Country / City (optional)")
            preferred_mode = st.selectbox("Learning Preference", ["Self-paced", "Online classes", "Offline classes", "Mixed"])
        st.markdown("#### 📚 Academic Performance (optional)")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            tenth = st.number_input("Class 10th %", min_value=0.0, max_value=100.0, value=None, step=0.1, placeholder="0–100")
        with m2:
            twelfth = st.number_input("Class 12th %", min_value=0.0, max_value=100.0, value=None, step=0.1, placeholder="0–100")
        with m3:
            sgpa = st.number_input("Current SGPA (out of 10)", min_value=0.0, max_value=10.0, value=None, step=0.1, placeholder="0–10")
        with m4:
            cgpa = st.number_input("Overall CGPA (out of 10)", min_value=0.0, max_value=10.0, value=None, step=0.1, placeholder="0–10")

        submitted = st.form_submit_button("🚀 Generate My Career Roadmap", use_container_width=True)

    if submitted:
        if not interests.strip() and not goal.strip():
            st.error("Please enter your career interests or career goal.")
        else:
            profile = {
                "Name": name or "Not provided",
                "Education": education,
                "Course/Stream": course or "Not provided",
                "Career Interests": interests or "Not provided",
                "Career Goal": goal or "Not provided",
                "Current Skills": skills or "Not provided",
                "Experience Level": experience,
                "Study Time": study_time,
                "Location": location or "Not provided",
                "Learning Preference": preferred_mode,
                "Class 10th Percentage": f"{tenth}%" if tenth is not None else "Not provided",
                "Class 12th Percentage": f"{twelfth}%" if twelfth is not None else "Not provided",
                "Current SGPA": str(sgpa) if sgpa is not None else "Not provided",
                "Overall CGPA": str(cgpa) if cgpa is not None else "Not provided"
            }
            st.session_state.profile = profile

            prompt = f"""
Create a personalized career guidance report using this student profile:
{profile}

Return clean, well-structured Markdown. Follow this exact structure:

# Career Roadmap for {profile['Name']}

## 1. Student Profile Summary
Summarize the student's education, interests, skills, goals, and supplied academic scores.

## 2. Career Options
Suggest 3 relevant career paths. For each include role overview, why it may fit,
key skills, and possible entry-level roles. Do not guarantee outcomes.

## 3. Career Direction
Explain practical options and trade-offs without declaring one universally best career.

## 4. Academic Profile & Skill Gap Analysis
Use a table: Area | Student Information | What It Means / Next Step.
Do not judge potential only by marks. Never invent missing grades or skills.

## 5. Personalized 6-Month Roadmap
Use a table: Month | Learning Focus | Weekly Actions | Expected Outcome.
Make it realistic for the student's level and study time.

## 6. Portfolio Projects
Give at least 3 projects, each with purpose and skills practiced.

## 7. Courses & Learning Resources
Suggest recognized learning platforms and course topics. Do not invent URLs.

## 8. Internship & Job Preparation
Include resume, portfolio/GitHub (if relevant), interview practice, and applications.

## 9. Weekly Study Routine
Provide a practical weekly routine matching the available study time.

## 10. Action Checklist
Give 6-8 useful checkbox items.

## 11. Important Note
Explain that this is informational guidance, not a job or salary guarantee.
Use encouraging, realistic language. If the profile lacks information, state assumptions.
"""
            try:
                with st.spinner("AI is preparing your personalized roadmap..."):
                    llm = make_llm()
                    result = llm.invoke([
                        SystemMessage(content="You are CareerGuide AI, a practical and student-friendly career guidance assistant. Output readable Markdown only."),
                        HumanMessage(content=prompt)
                    ])
                st.session_state.roadmap = clean_response(result.content)
                st.session_state.chat_history = []
                st.success("Your roadmap has been generated! Open the My Roadmap tab.")
                st.rerun()
            except Exception as e:
                err = str(e)
                low = err.lower()
                if "429" in low or "resource_exhausted" in low or "quota" in low:
                    st.error("Gemini API quota limit reached. Check Google AI Studio usage and retry after quota reset.")
                elif "401" in low or "403" in low or "api_key_invalid" in low:
                    st.error("API key/permission error. Check your Gemini API key and project access.")
                else:
                    st.error("Roadmap generate nahi ho paya. Error details:")
                    st.code(err)

# ---------------- ROADMAP ----------------
with roadmap_tab:
    st.subheader("🗺️ My Career Roadmap")
    if st.session_state.roadmap:
        st.markdown(st.session_state.roadmap)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "⬇️ Download Roadmap (.md)",
                data=st.session_state.roadmap,
                file_name="career_roadmap.md",
                mime="text/markdown",
                use_container_width=True
            )
        with d2:
            try:
                pdf_data = create_pdf(st.session_state.roadmap)
                st.download_button(
                    "📄 Download Roadmap (PDF)",
                    data=pdf_data,
                    file_name="career_roadmap.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception:
                st.warning("PDF export ke liye reportlab install karein: pip install reportlab")
        if st.button("🗑️ Clear Current Roadmap"):
            st.session_state.roadmap = ""
            st.session_state.profile = {}
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.info("Abhi roadmap nahi bana. Student Profile tab mein details fill karke generate karein.")

# ---------------- CAREER CHAT ----------------
with chat_tab:
    st.subheader("💬 Ask CareerGuide AI")
    st.caption("Ask follow-up questions about your generated roadmap.")
    if not st.session_state.roadmap:
        st.info("Generate a roadmap first to start career chat.")
    else:
        for item in st.session_state.chat_history:
            with st.chat_message(item["role"]):
                st.markdown(item["content"])

        question = st.chat_input("Ask about skills, courses, projects, or your roadmap...")
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        llm = make_llm()
                        chat_prompt = f"""
Student profile: {st.session_state.profile}
Their generated roadmap: {st.session_state.roadmap}
User's follow-up question: {question}
Answer specifically and clearly. Do not guarantee jobs, salaries, or outcomes.
"""
                        result = llm.invoke([
                            SystemMessage(content="You are CareerGuide AI. Answer career questions in a practical, supportive, factual way."),
                            HumanMessage(content=chat_prompt)
                        ])
                        answer = clean_response(result.content)
                        st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                low = str(e).lower()
                if "429" in low or "resource_exhausted" in low or "quota" in low:
                    st.error("Gemini API quota limit reached. Check AI Studio usage and try after reset.")
                else:
                    st.error(f"Chat request failed: {e}")

st.divider()
st.caption("CareerGuide AI | BCA Project | Built with Streamlit + LangChain + Gemini")
