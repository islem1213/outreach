import streamlit as st
import os
import pandas as pd
from utils import extract_text_from_pdf
from orchestrator import PipelineOrchestrator
import time

# Page configuration
st.set_page_config(
    page_title="Autonomous Job App Multiagent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom styles for a premium design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.main-title {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.2rem;
}
.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}
.card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
}
.tag {
    display: inline-block;
    background: rgba(99, 102, 241, 0.12);
    color: #818cf8;
    padding: 0.3rem 0.7rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(99, 102, 241, 0.25);
    font-weight: 500;
}
.score-badge {
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    display: inline-block;
}
.score-high {
    background-color: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
}
.score-medium {
    background-color: rgba(245, 158, 11, 0.12);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.25);
}
.score-low {
    background-color: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.25);
}
.agent-step {
    border-left: 3px solid #6366f1;
    padding-left: 1rem;
    margin-bottom: 1rem;
}
.agent-title {
    font-weight: 600;
    color: #4f46e5;
    margin-bottom: 0.2rem;
}
.agent-desc {
    font-size: 0.9rem;
    color: #64748b;
}
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.markdown("<h1 class='main-title'>Autonomous Job Application Agent</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>A premium multi-agent system that searches, evaluates, and writes applications for you</p>", unsafe_allow_html=True)

# Sidebar configurations
st.sidebar.image("https://img.icons8.com/clouds/200/robot-vacuum-cleaner.png", width=100)
st.sidebar.title("Configuration")

# Fetch API key (prioritize user-input value or pre-filled value)
api_key_env = os.environ.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Gemini API Key", 
    value=api_key_env if api_key_env else "AQ.Ab8RN6I2So0Wt16RxhOV6IC2O-AQqj4mGmesz70Xm1Dy2jXFVQ", 
    type="password"
)

selected_model = st.sidebar.selectbox(
    "Gemini Model",
    ["gemini-2.5-flash", "gemini-2.5-pro"],
    index=0
)

st.sidebar.markdown("""
---
### How it works:
1. **Resume Profiler Agent** parses skills, experience, and educational background.
2. **Job Searcher Agent** forms optimized search strings and queries relevant positions.
3. **Job Matcher Agent** executes a multi-dimensional assessment of candidates vs job requirements.
4. **Cover Letter Agent** writes highly tailored, specific letters for the highest scoring job.
""")

# Setup core layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📥 Candidate Inputs")
    with st.form("pipeline_inputs"):
        desired_role = st.text_input("Target Job Title / Desired Role", placeholder="e.g. Senior Backend Engineer")
        location = st.text_input("Preferred Location / Type", placeholder="e.g. Remote, Paris, New York")
        
        uploaded_file = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"])
        
        submit_btn = st.form_submit_button("Run Multi-Agent Pipeline", use_container_width=True)

with col2:
    st.markdown("### ⚙️ Live Agent Activity Logs")
    activity_placeholder = st.container()

# Session state initialization
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None

# If running the pipeline
if submit_btn:
    if not api_key:
        st.error("Please enter a valid Gemini API Key in the sidebar.")
    elif not desired_role:
        st.error("Please specify a Target Job Title.")
    elif not uploaded_file:
        st.error("Please upload a resume (PDF or TXT file).")
    else:
        # Extract text from resume
        with st.spinner("Extracting text from resume..."):
            file_type = uploaded_file.name.split(".")[-1].lower()
            if file_type == "pdf":
                resume_text = extract_text_from_pdf(uploaded_file.read())
            else:
                resume_text = uploaded_file.read().decode("utf-8")
                
        if not resume_text.strip():
            st.error("Could not extract any text from the uploaded resume. Please check the file.")
        else:
            # Setup logging container
            activity_container = activity_placeholder.container()
            
            # Progress callback for the orchestrator
            def pipeline_callback(step: str, status: str, details: dict = None):
                msg = details.get("message", "") if details else ""
                
                with activity_container:
                    if status == "start":
                        st.info(f"⏳ **[{step.upper()} AGENT]**: {msg}")
                    elif status == "success":
                        st.success(f"✅ **[{step.upper()} AGENT]**: {msg}")
                    elif status == "error":
                        st.error(f"❌ **[{step.upper()} AGENT]**: {msg}")
                time.sleep(0.5)

            try:
                orchestrator = PipelineOrchestrator(api_key=api_key, model=selected_model)
                query_full = f"{desired_role} {location}".strip()
                
                results = orchestrator.run(
                    resume_text=resume_text,
                    desired_role=query_full,
                    progress_cb=pipeline_callback
                )
                st.session_state.pipeline_results = results
                st.balloons()
            except Exception as e:
                st.error(f"Pipeline Execution Failed: {e}")

# If we have results, display them beautifully
if st.session_state.pipeline_results:
    results = st.session_state.pipeline_results
    profile = results.get("profile")
    evaluations = results.get("evaluations", [])
    cover_letter = results.get("cover_letter")
    best_job = results.get("best_job")
    
    st.markdown("---")
    
    # 3 tabs for viewing the results
    tab1, tab2, tab3 = st.tabs([
        "👤 Candidate Profile", 
        "💼 Job Openings & Match Analysis", 
        "📝 Tailored Cover Letter"
    ])
    
    with tab1:
        if profile:
            st.markdown(f"## {profile.name}")
            st.markdown(f"📧 **Email:** {profile.email} | 📞 **Phone:** {profile.phone}")
            
            col_prof1, col_prof2 = st.columns(2)
            with col_prof1:
                st.markdown("#### Summary")
                st.write(profile.experience_summary)
                
                st.markdown("#### Core Skills")
                skills_html = "".join([f"<span class='tag'>{s}</span>" for s in profile.skills])
                st.markdown(skills_html, unsafe_allow_html=True)
                
            with col_prof2:
                st.markdown("#### Educational History")
                for edu in profile.education:
                    st.write(f"- {edu}")
                    
                st.markdown("#### Projects & Achievements")
                for proj in profile.projects:
                    st.write(f"- {proj}")
                    
                st.markdown("#### Target Roles")
                roles_html = "".join([f"<span class='tag' style='background:rgba(236,72,153,0.1);color:#ec4899;border-color:rgba(236,72,153,0.2)'>{r}</span>" for r in profile.target_roles])
                st.markdown(roles_html, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Job Match Rankings")
        st.write(f"Search Query Used: `{results.get('search_query', '')}`")
        
        if not evaluations:
            st.warning("No evaluations generated.")
        else:
            for i, job in enumerate(evaluations):
                # Color code match scores
                score_class = "score-low"
                if job.match_score >= 80:
                    score_class = "score-high"
                elif job.match_score >= 50:
                    score_class = "score-medium"
                    
                expander_label = f"Match Score: {job.match_score}% | {job.title} at {job.company} ({job.recommendation})"
                
                with st.expander(expander_label, expanded=(i == 0)):
                    col_m1, col_m2 = st.columns([2, 1])
                    with col_m1:
                        st.markdown("##### Job Description Snippet")
                        st.write(job.body)
                        st.markdown(f"[View Job Posting / Source Link]({job.href})")
                        
                    with col_m2:
                        st.markdown(f"Match Level: <span class='score-badge {score_class}'>{job.match_score}%</span>", unsafe_allow_html=True)
                        st.write(f"**Recommendation:** {job.recommendation}")
                        
                        st.markdown("**Key Strengths:**")
                        for s in job.strengths:
                            st.write(f"- ✅ {s}")
                            
                        st.markdown("**Identified Skill Gaps:**")
                        if job.gaps:
                            for g in job.gaps:
                                st.write(f"- ⚠️ {g}")
                        else:
                            st.write("- None! Perfect fit.")

    with tab3:
        if cover_letter and best_job:
            st.markdown(f"### Cover Letter for {best_job.title} at {best_job.company}")
            st.info(f"**Relevance details:** The writer agent customized this letter targeting: {', '.join(cover_letter.tailored_skills_highlighted)}")
            
            st.text_input("Subject Line", value=cover_letter.subject)
            st.text_area("Body Content", value=cover_letter.body, height=450)
            
            st.success("You can copy the cover letter text and subjects directly to apply!")
        else:
            st.warning("No cover letter generated because no matches were evaluated.")
