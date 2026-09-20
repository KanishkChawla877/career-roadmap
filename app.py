import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

st.set_page_config(page_title="CareerGuide AI", page_icon="🎯", layout="wide")
st.title("🎯 CareerGuide AI — Career Roadmap Generator")
st.write("Create a personalized career roadmap based on your education, interests, and skills.")

# API key drawer/sidebar
with st.sidebar:
    st.header("🔐 API Settings")
    st.caption("Your Gemini API key is used only to make requests to Gemini.")
    sidebar_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Paste your API key here",
        help="For deployed apps, you can also store GOOGLE_API_KEY in Streamlit Secrets."
    )
    st.caption("Keep your API key private. Do not share it or commit it to GitHub.")

# Career knowledge base from the Jupyter Notebook
career_data = [
    {"career": "Data Scientist", "skills": ["Python", "SQL", "Statistics", "Machine Learning"],
     "courses": ["Python", "SQL", "Statistics", "Machine Learning"],
     "projects": ["Sales Prediction", "Customer Segmentation"],
     "roles": ["Data Analyst", "Data Scientist"], "duration": "6-12 months"},
    {"career": "Web Developer", "skills": ["HTML", "CSS", "JavaScript", "React"],
     "courses": ["HTML", "CSS", "JavaScript", "React"],
     "projects": ["Portfolio Website", "E-commerce Website"],
     "roles": ["Frontend Developer", "Web Developer"], "duration": "4-8 months"},
    {"career": "Cybersecurity Analyst", "skills": ["Networking", "Linux", "Python", "Security"],
     "courses": ["Networking", "Linux", "Ethical Hacking"],
     "projects": ["Network Security Lab", "Log Analyzer"],
     "roles": ["SOC Analyst", "Security Analyst"], "duration": "6-12 months"},
    {"career": "AI/ML Engineer", "skills": ["Python", "Mathematics", "Machine Learning"],
     "courses": ["Python", "Statistics", "Machine Learning", "Deep Learning"],
     "projects": ["Image Classifier", "Chatbot"],
     "roles": ["AI Engineer", "ML Engineer"], "duration": "8-15 months"},
    {"career": "UI/UX Designer", "skills": ["Figma", "Creativity", "Design", "Communication"],
     "courses": ["Design Basics", "Figma", "UI/UX Principles"],
     "projects": ["Mobile App Prototype", "Website Redesign"],
     "roles": ["UI Designer", "UX Designer"], "duration": "4-8 months"}
]
career_df = pd.DataFrame(career_data)

# Inputs
with st.form("student_profile"):
    st.subheader("Student Profile")
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Student Name")
        education = st.text_input("Education", placeholder="e.g., BCA 2nd Year")
        interests = st.text_input("Career Interests", placeholder="e.g., Data Science, Cybersecurity")
    with col2:
        skills = st.text_input("Existing Skills", placeholder="e.g., Python Basics, HTML, CSS")
        career_goal = st.text_input("Career Goal", placeholder="e.g., Become a Data Scientist / Not Sure")
    submitted = st.form_submit_button("Generate Career Roadmap 🚀")

if submitted:
    # Streamlit Cloud: set GOOGLE_API_KEY in App settings > Secrets.
    # Local run: set GOOGLE_API_KEY in your .env file.
    try:
        api_key = (
            sidebar_api_key.strip()
            or st.secrets.get("GOOGLE_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", "")
        )
    except Exception:
        api_key = sidebar_api_key.strip() or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        st.error("Gemini API key nahi mili. Sidebar ke API Settings mein key paste karein, ya Streamlit Secrets/.env mein GOOGLE_API_KEY set karein.")
        st.stop()
    if not interests.strip() and not career_goal.strip():
        st.error("Please enter your interests or career goal.")
        st.stop()

    @tool
    def search_career_information(career_name: str) -> str:
        """Search the career knowledge base for required skills, courses, projects, job roles, and estimated learning duration."""
        matched = career_df[career_df["career"].str.lower() == career_name.lower()]
        if matched.empty:
            return "Career not found in the database."
        return matched.iloc[0].to_json()

    @tool
    def analyze_skill_gap(career_name: str, student_skills: list) -> str:
        """Compare student's existing skills with career requirements; return matched and missing skills."""
        matched = career_df[career_df["career"].str.lower() == career_name.lower()]
        if matched.empty:
            return "Career not found in the database."
        required = set(matched.iloc[0]["skills"])
        existing = {s.strip().lower() for s in student_skills}
        available = [s for s in required if s.lower() in existing]
        missing = [s for s in required if s.lower() not in existing]
        return json.dumps({"career": career_name, "matched_skills": available, "skills_to_learn": missing})

    @tool
    def create_learning_plan(career_name: str) -> str:
        """Retrieve courses, practical projects, job roles, and estimated duration for a career learning plan."""
        matched = career_df[career_df["career"].str.lower() == career_name.lower()]
        if matched.empty:
            return "Career not found. Suggest a general learning plan."
        return json.dumps(matched.iloc[0].to_dict(), indent=2)

    system_prompt = """
You are CareerGuide AI, a professional career roadmap assistant.
Use the student's profile and available career tools. Return clean Markdown only.
Never return a Python list/dictionary, JSON wrapper, or escaped newline symbols.
Use real headings, bullets, paragraphs, and Markdown tables.

Follow this COMPLETE structure in the exact order:

# Career Roadmap for [Student Name]

## 1. Student Profile Summary
Summarize education, interests, current skills, and career goal.

## 2. Career Options
Give 2-3 relevant career options. For each, explain the role, why it may fit,
and key skills required. Do not guarantee outcomes or claim one career is best for everyone.

## 3. Recommended Direction
Explain a practical direction based on the profile and briefly mention alternatives.

## 4. Skill Gap Analysis
Create a table: Skill Area | Current Status | What to Learn | Priority.
Do not claim the student has a skill unless it was listed in the profile.

## 5. Personalized Learning Roadmap
Create a 6-month table: Month | Learning Focus | Action Items | Expected Outcome.
Make it realistic and include hands-on practice.

## 6. Projects for Portfolio
Suggest at least 3 projects. For each, give a short description and skills practiced.

## 7. Courses and Learning Resources
List useful courses/topics and established free learning platforms. Do not invent URLs.

## 8. Internship and Job Preparation
Give practical resume, GitHub/portfolio, interview, and application steps.

## 9. Weekly Study Routine
Give a realistic weekly routine the student can consistently follow.

## 10. Final Action Checklist
Provide 5-8 actionable checkboxes.

## 11. Important Note
Mention that this is informational guidance and career outcomes are not guaranteed.

Keep every section specific, clear, student-friendly, and useful. Avoid repetition.
"""

    student_profile = f"""
    Student Name: {student_name or 'Not provided'}
    Education: {education or 'Not provided'}
    Interests: {interests or 'Not provided'}
    Existing Skills: {skills or 'Not provided'}
    Career Goal: {career_goal or 'Not provided'}

    Analyze this student profile. Recommend suitable careers, identify skill gaps,
    and create a personalized career roadmap. Use available tools.
    """

    try:
        with st.spinner("CareerGuide AI is preparing your roadmap..."):
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                temperature=0.3,
                google_api_key=api_key
            )
            career_agent = create_agent(
                model=llm,
                tools=[search_career_information, analyze_skill_gap, create_learning_plan],
                system_prompt=system_prompt
            )
            response = career_agent.invoke({"messages": [{"role": "user", "content": student_profile}]})

        answer = response["messages"][-1].content

        # Gemini/LangChain may return a list of text blocks. Extract clean text.
        if isinstance(answer, list):
            answer = "\n\n".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in answer
            )
        elif not isinstance(answer, str):
            answer = str(answer)

        st.success("Career roadmap generated!")
        st.markdown(answer)
        st.download_button("Download Roadmap (.txt)", answer,
                           file_name="career_roadmap.txt", mime="text/plain")

        with st.expander("Agent Tool Execution Trace"):
            for message in response["messages"]:
                if getattr(message, "tool_calls", None):
                    for call in message.tool_calls:
                        st.write("**Tool Used:**", call.get("name"))
                        st.json(call.get("args", {}))
                if getattr(message, "type", "") == "tool":
                    st.write("**Tool Result:**")
                    st.code(str(message.content)[:1500])

    except Exception as e:
        error = str(e)
        lower = error.lower()
        if "429" in lower or "resource_exhausted" in lower or "quota" in lower:
            st.error("Gemini API quota exceeded. Check Google AI Studio usage/quota and retry after reset. Re-running repeatedly may not help.")
        elif "401" in lower or "403" in lower or "api_key_invalid" in lower:
            st.error("API key/permission error. Verify your Gemini API key and project access.")
        else:
            st.error("Roadmap generate nahi ho paya. Error details:")
            st.code(error)

st.divider()
st.caption("CareerGuide AI | BCA Project")
