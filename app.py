import streamlit as st
import pyrebase
import os
import re
import spacy
import time
import requests
from streamlit_lottie import st_lottie
from PyPDF2 import PdfReader
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq 

# --- 1. FIREBASE CONFIGURATION (Fixed for Python) ---
firebaseConfig = {
    "apiKey": "AIzaSyBTPjU9dlh-tQvkORiIkYEu97f0CWzAB7c",
    "authDomain": "resumeanalyzer-ed553.firebaseapp.com",
    "projectId": "resumeanalyzer-ed553",
    "storageBucket": "resumeanalyzer-ed553.firebasestorage.app",
    "messagingSenderId": "97614342438",
    "appId": "1:97614342438:web:5e595c5134cb1b57e0f9e7",
    "databaseURL": "https://resumeanalyzer-ed553-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# --- 2. ADVANCED UI STYLING ---
st.set_page_config(page_title="AI Resume Intelligence Pro", page_icon="🔮", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }
    .auth-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 25px; padding: 40px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
    }
    .header-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 35px; border-radius: 20px; color: white; margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;
    }
    .dashboard-card {
        background: white; padding: 25px; border-radius: 15px;
        border: 1px solid #e2e8f0; text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 12px; font-weight: bold;
        transition: 0.3s all; height: 3.2em; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Lottie Animation Loader
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None

lottie_auth = load_lottieurl("https://lottie.host/80709559-6932-4217-9f79-994361543888/v7lKzJ9X4v.json")

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_email' not in st.session_state: st.session_state['user_email'] = ""

# --- 4. BACKEND SETUP ---
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "your-fallback-key"))

@st.cache_resource
def load_nlp():
    try: return spacy.load("en_core_web_sm")
    except:
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = load_nlp()
SKILLS_DB = ["Java", "JavaScript", "Python", "React", "Node.js", "SQL", "AWS", "Machine Learning", "Data Science", "DevOps"]

def extract_text(file):
    if file.name.endswith('.pdf'):
        return "".join([p.extract_text() for p in PdfReader(file).pages])
    return "\n".join([para.text for para in docx.Document(file).paragraphs])

# --- 5. AUTHENTICATION PAGE ---
def show_auth_page():
    st.markdown("<div class='header-box'><h1>🔐 AI Resume Pro Access</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            if lottie_auth: st_lottie(lottie_auth, height=120, key="login_anim")
            email = st.text_input("Email", placeholder="name@domain.com", key="l_email")
            pwd = st.text_input("Password", type="password", placeholder="••••••••", key="l_pwd")
            if st.button("LOGIN", key="login_btn"):
                try:
                    auth.sign_in_with_email_and_password(email, pwd)
                    st.session_state['logged_in'] = True
                    st.session_state['user_email'] = email
                    st.success("Login Successful!")
                    st.rerun()
                except:
                    st.error("Invalid credentials. Please check your Email/Password.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            new_email = st.text_input("New Email", placeholder="example@email.com", key="s_email")
            new_pwd = st.text_input("New Password (min 6 chars)", type="password", key="s_pwd")
            if st.button("CREATE ACCOUNT", key="signup_btn"):
                if not new_email or len(new_pwd) < 6:
                    st.warning("Please provide a valid email and a password of at least 6 characters.")
                else:
                    try:
                        auth.create_user_with_email_and_password(new_email, new_pwd)
                        st.success("Account created! Now you can Login.")
                    except Exception as e:
                        if "EMAIL_EXISTS" in str(e): st.error("This email is already registered.")
                        else: st.error(f"Signup error: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

# --- 6. MAIN DASHBOARD ---
if not st.session_state['logged_in']:
    show_auth_page()
else:
    st.sidebar.markdown(f"""
        <div style='text-align:center; padding:15px; border-radius:12px; background:white; border:1px solid #ddd;'>
            <h4 style='color:#764ba2; margin:0;'>Active Session</h4>
            <p style='color:#555; font-size:0.9em;'>{st.session_state['user_email']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown(f"<div class='header-box'><h1>🔮 Resume Analysis Dashboard</h1></div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"], label_visibility="collapsed")

    if uploaded_file:
        with st.spinner("Analyzing profile..."):
            raw_text = extract_text(uploaded_file)
            found_skills = [s for s in SKILLS_DB if s.lower() in raw_text.lower()]
            time.sleep(1)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="dashboard-card"><p>FORMAT</p><h2>{uploaded_file.name.split(".")[-1].upper()}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="dashboard-card"><p>SKILLS</p><h2>{len(found_skills)}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="dashboard-card"><p>STATUS</p><h2 style="color:#10b981;">SECURE</h2></div>', unsafe_allow_html=True)

        col_l, col_r = st.columns([1, 1.2])
        with col_l:
            st.subheader("🛠️ Technical Stack")
            if found_skills:
                for skill in found_skills: st.markdown(f'<span style="display:inline-block; background:#764ba2; color:white; padding:5px 12px; border-radius:15px; margin:3px;">{skill}</span>', unsafe_allow_html=True)
            else: st.write("No skills detected.")
        
        with col_r:
            st.subheader("🧠 AI Expert Insights")
            if st.button("🚀 GET AI SUGGESTIONS"):
                with st.spinner("Consulting AI Engine..."):
                    try:
                        completion = client.chat.completions.create(
                            model="llama3-8b-8192",
                            messages=[{"role": "user", "content": f"Give 3 short career tips for: {raw_text[:800]}"}]
                        )
                        st.write(completion.choices[0].message.content)
                    except:
                        st.warning("⚠️ AI Service Busy - Using Expert Guidelines:")
                        st.markdown("""
                        * **Action Verbs:** Use words like 'Optimized', 'Architected', or 'Led'.
                        * **Quantify Results:** Add metrics (e.g., 'Improved speed by 20%').
                        * **Clean Format:** Use an ATS-friendly single-column layout.
                        """)

        st.divider()
        st.subheader("🎯 ATS Matcher")
        jd = st.text_area("Paste Job Description:")
        if jd and st.button("🔍 CHECK MATCH"):
            vectorizer = TfidfVectorizer()
            matrix = vectorizer.fit_transform([raw_text, jd])
            score = round(cosine_similarity(matrix)[0][1] * 100, 2)
            st.write(f"### Match Score: {score}%")
            st.progress(score/100)
    else: st.info("👋 System ready. Please upload your resume.")