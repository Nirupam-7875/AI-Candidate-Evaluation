import streamlit as st
import json
import time
from PyPDF2 import PdfReader
from google import genai
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="AI Candidate Evaluator", page_icon="⚖️", layout="wide")

# --- Helper Functions ---
def parse_json_response(text):
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        if lines[0].startswith('```'): lines = lines[1:]
        if lines[-1].startswith('```'): lines = lines[:-1]
        text = '\n'.join(lines)
    try:
        return json.loads(text)
    except Exception as e:
        st.error(f"Failed to parse AI response: {e}")
        return {}

def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# --- Prompts & AI Logic ---
def build_profile(client, resume_text, transcript_text):
    prompt = f"""
    Analyze the resume and transcript. Extract:
    1. Candidate name
    2. Top 5 skills
    3. Brief overall summary
    
    Return EXACTLY this JSON format:
    {{
      "name": "Candidate Name",
      "skills": ["Skill 1", "Skill 2"],
      "summary": "Brief 2-3 sentence summary."
    }}
    
    Resume: {resume_text}
    Transcript: {transcript_text}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return parse_json_response(response.text)

def run_agent(client, agent_name, agent_emoji, sys_prompt, profile, resume, transcript):
    prompt = f"""
    You are the {agent_name} {agent_emoji}.
    System Instructions: {sys_prompt}
    
    Candidate Name: {profile.get('name', 'Unknown')}
    Resume: {resume}
    Transcript: {transcript}
    
    Return EXACTLY this JSON format:
    {{
        "agentName": "{agent_name}",
        "agentEmoji": "{agent_emoji}",
        "rating": 7.5,
        "confidence": 0.8,
        "strengths": ["strength 1", "strength 2"],
        "concerns": ["concern 1", "concern 2"],
        "detailedAnalysis": "1-2 paragraphs of your specific analysis"
    }}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return parse_json_response(response.text)

def run_all_agents(client, profile, resume, transcript):
    agents_config = [
        ("Technical Agent", "🔧", "Evaluate technical depth, system design, and coding ability. Rate 1-10."),
        ("HR/Culture Agent", "🤝", "Evaluate communication, teamwork, and cultural fit. Rate 1-10."),
        ("Hiring Manager", "📋", "Evaluate ROI, leadership potential, and delivery ability. Rate 1-10."),
        ("Skeptic Agent", "🔍", "Find contradictions, exaggerations, and red flags. Rate 1-10.")
    ]
    
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for name, emoji, sys_prompt in agents_config:
            futures.append(executor.submit(run_agent, client, name, emoji, sys_prompt, profile, resume, transcript))
        for future in futures:
            results.append(future.result())
    return results

def run_debate(client, agents_evals):
    prompt = f"""
    You are simulating a debate between 4 interviewers.
    Here are their initial evaluations:
    {json.dumps(agents_evals, indent=2)}
    
    Write a short 1-round debate transcript where they discuss the candidate.
    Return EXACTLY this JSON format:
    {{
        "exchanges": [
            {{ "agent": "Technical Agent", "message": "I noticed..." }}
        ],
        "finalRatings": {{
            "Technical Agent": 7.5,
            "HR/Culture Agent": 8.0,
            "Hiring Manager": 7.0,
            "Skeptic Agent": 6.5
        }}
    }}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return parse_json_response(response.text)

def final_decision(client, agents_evals, debate_result):
    prompt = f"""
    Based on the evaluations and debate, make a final hiring decision.
    Evaluations: {json.dumps(agents_evals)}
    Debate: {json.dumps(debate_result)}
    
    Return EXACTLY this JSON format:
    {{
        "recommendation": "Hire",
        "finalScore": 7.2,
        "reasoning": "2-3 paragraphs explaining the final decision.",
        "keyStrengths": ["..."],
        "keyConcerns": ["..."]
    }}
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return parse_json_response(response.text)

# --- UI Setup ---
st.title("⚖️ AI Candidate Evaluator")
st.markdown("Upload a Resume (PDF) and Interview Transcript (Text) to launch a Multi-Agent AI evaluation.")

api_key = st.text_input("Gemini API Key", type="password")
col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
with col2:
    transcript_text = st.text_area("Paste Interview Transcript", height=150)
job_role = st.text_input("Job Role (Optional)", "Software Engineer")

if st.button("Run Full Evaluation", type="primary"):
    if not api_key:
        st.error("Please enter a Gemini API Key.")
    elif not resume_file:
        st.error("Please upload a resume.")
    elif not transcript_text:
        st.error("Please paste the transcript.")
    else:
        # Initialize Client
        client = genai.Client(api_key=api_key)
        
        # Step 0: Parse PDF
        with st.status("Parsing PDF...", expanded=True) as status:
            resume_text = extract_pdf_text(resume_file)
            status.update(label="PDF Parsed Successfully!", state="complete")
        
        # Step 1: Profile
        with st.status("Building Candidate Profile...", expanded=True) as status:
            profile = build_profile(client, resume_text, transcript_text)
            st.write(f"**Name:** {profile.get('name')}")
            st.write(f"**Skills:** {', '.join(profile.get('skills', []))}")
            st.write(f"**Summary:** {profile.get('summary')}")
            status.update(label="Profile Built!", state="complete")
            
        # Step 2: Agent Evaluations
        with st.status("Running 4 AI Agents in Parallel...", expanded=True) as status:
            evals = run_all_agents(client, profile, resume_text, transcript_text)
            cols = st.columns(4)
            for i, ev in enumerate(evals):
                with cols[i]:
                    st.info(f"{ev.get('agentEmoji', '')} **{ev.get('agentName')}**\n\nRating: {ev.get('rating')}/10")
            status.update(label="Agent Evaluations Complete!", state="complete")
            
        # Step 3: Debate
        with st.status("Agents are Debating...", expanded=True) as status:
            debate = run_debate(client, evals)
            for ex in debate.get('exchanges', []):
                st.markdown(f"**{ex.get('agent')}**: {ex.get('message')}")
            status.update(label="Debate Complete!", state="complete")
            
        # Step 4: Final Decision
        with st.status("Generating Final Report...", expanded=True) as status:
            final = final_decision(client, evals, debate)
            status.update(label="Evaluation Complete!", state="complete")
            
        # --- Final Report Display ---
        st.divider()
        st.header(f"Final Recommendation: {final.get('recommendation')}")
        st.subheader(f"Overall Score: {final.get('finalScore')}/10")
        st.markdown(f"**Reasoning:**\n{final.get('reasoning')}")
        
        col_s, col_c = st.columns(2)
        with col_s:
            st.success("**Key Strengths:**\n" + "\n".join([f"- {s}" for s in final.get('keyStrengths', [])]))
        with col_c:
            st.error("**Key Concerns:**\n" + "\n".join([f"- {c}" for c in final.get('keyConcerns', [])]))
        
        st.divider()
        st.subheader("Detailed Agent Breakdowns")
        for ev in evals:
            with st.expander(f"{ev.get('agentEmoji', '')} {ev.get('agentName')} ({ev.get('rating')}/10)"):
                st.write(ev.get('detailedAnalysis'))
                st.write("**Strengths:** " + ", ".join(ev.get('strengths', [])))
                st.write("**Concerns:** " + ", ".join(ev.get('concerns', [])))
