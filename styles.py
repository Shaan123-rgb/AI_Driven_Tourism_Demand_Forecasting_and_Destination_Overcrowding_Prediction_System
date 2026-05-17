import streamlit as st

def apply_styles():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* ===== 1. GLOBAL THEME & TYPOGRAPHY ===== */
    :root {
        --bg-color: #060b14;               /* Very deep sleek background */
        --card-bg: #111827;                /* Dark card */
        --card-border: rgba(255, 255, 255, 0.06);
        --accent-primary: #0ea5e9;         /* Vibrant Sky Blue */
        --accent-gradient: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
        --text-primary: #f8fafc;           /* Almost pure white for ultimate readability */
        --text-secondary: #94a3b8;         /* Subtle grey for secondary text */
        --border-radius: 12px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Base Font application - Let inheritance work, avoid breaking icons */
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: var(--text-primary) !important;
    }
    
    /* CRITICAL FIX for Random Texts / Broken Icons */
    .material-symbols-rounded,
    [data-testid="stIconMaterial"],
    [class*="material-symbols"],
    .stIcon {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* Main background */
    .stApp {
        background-color: #020c1b !important;
        background-image: linear-gradient(135deg, #0a192f 0%, #020c1b 100%) !important;
        background-attachment: fixed !important;
    }
    
    /* ===== STREAMLIT UI CLEANUP ===== */
    /* Make the header bar transparent but keep the buttons visible */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    
    /* Only hide the top colored decoration line, keep the rest visible */
    div[data-testid="stDecoration"] {
        display: none !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Ensure paragraphs and general text are strictly primary text to avoid grey-out */
    p, span, label, li, div.stMarkdown {
        color: var(--text-primary) !important;
    }

    /* Specific subtle text areas */
    .stCaptionContainer p {
        color: var(--text-secondary) !important;
    }

    /* ===== 2. LOGIN / SIGNUP PAGE & FORMS ===== */
    /* Global form fallback (auth.py has its own unified override) */
    div[data-testid="stForm"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.8));
        border-radius: 20px;
        padding: 3rem;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
        border: 1px solid var(--card-border);
        transition: var(--transition);
    }

    /* ===== 3. DASHBOARD METRICS ===== */
    div[data-testid="metric-container"] {
        background: var(--card-bg) !important;
        border-radius: 16px !important;
        padding: 1.5rem 1.8rem !important;
        border: 1px solid var(--card-border) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        transition: var(--transition) !important;
        position: relative;
        overflow: hidden;
    }
    
    /* Top accent line on metrics */
    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 4px;
        background: var(--accent-gradient);
        opacity: 0;
        transition: var(--transition);
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 30px rgba(14, 165, 233, 0.15) !important;
        border-color: rgba(14, 165, 233, 0.3) !important;
    }

    div[data-testid="metric-container"]:hover::before {
        opacity: 1;
    }

    /* Metric Labels */
    div[data-testid="metric-container"] label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="metric-container"] label p {
        color: var(--text-secondary) !important;
    }
    
    /* Metric Values */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        padding-top: 0.5rem !important;
    }
    
    /* Fix weird streamlit inner text nodes in metrics */
    div[data-testid="stMetricValue"] > div {
        color: #ffffff !important;
    }

    /* ===== 4. SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: #090e17 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    
    section[data-testid="stSidebarNav"] {
        display: none !important; /* Hide streamlit default nav */
    }

    /* ===== 5. INPUTS & CONTROLS ===== */
    .stTextInput input, 
    .stNumberInput input,
    .stDateInput input,
    .stPasswordInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1.05rem !important;
        transition: var(--transition) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* Selectbox */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        transition: var(--transition) !important;
    }

    /* Input Focus */
    .stTextInput input:focus, 
    .stNumberInput input:focus,
    .stDateInput input:focus,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.25) !important;
        background-color: #0f172a !important;
    }

    /* Input placeholders */
    ::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    /* Selectbox dropdown */
    ul[data-baseweb="menu"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
    }
    
    ul[data-baseweb="menu"] li {
        color: #ffffff !important;
        font-size: 1rem !important;
        padding: 0.75rem 1rem !important;
    }
    
    ul[data-baseweb="menu"] li:hover {
        background-color: rgba(14, 165, 233, 0.2) !important;
    }

    /* Fix invisible text in some cases */
    .stTextInput div[data-baseweb="base-input"] {
        background-color: transparent !important;
    }

    /* Fix label styling */
    .stTextInput label p, .stNumberInput label p, .stSelectbox label p, .stDateInput label p {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* ===== 6. BUTTONS ===== */
    /* Target button container and make gradient vibrant */
    .stButton > button, 
    .stFormSubmitButton > button {
        background: var(--accent-gradient) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        transition: var(--transition) !important;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3) !important;
    }
    
    /* CRITICAL: Target internal p tag of buttons to explicitly be WHITE */
    .stButton > button * , 
    .stFormSubmitButton > button * {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }

    .stButton > button:hover, 
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.5) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    
    .stButton > button:active, 
    .stFormSubmitButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.3) !important;
    }

    /* ===== 7. TABS ===== */
    div[data-baseweb="tab-list"] {
        gap: 3rem !important;
        background-color: transparent !important;
        justify-content: center !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.05) !important;
        margin-bottom: 2rem !important;
    }
    
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border-bottom: 3px solid transparent !important;
        transition: var(--transition) !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        border-radius: 0 !important;
    }
    
    button[data-baseweb="tab"] p {
        color: var(--text-secondary) !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
    }
    
    button[data-baseweb="tab"]:hover p {
        color: #ffffff !important;
    }
    
    button[aria-selected="true"] {
        border-bottom: 3px solid var(--accent-primary) !important;
    }
    
    button[aria-selected="true"] p {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    /* ===== 8. DATAFRAMES & EXPANDERS ===== */
    div[data-testid="stExpander"] {
        background: #111827 !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    }
    
    div[data-testid="stExpander"] summary {
        padding: 1rem !important;
    }
    
    div[data-testid="stExpander"] summary p {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }

    div[data-testid="stExpander"] summary:hover {
        background: rgba(255,255,255,0.02) !important;
    }
    
    [data-testid="stDataFrame"] {
        background-color: #111827 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Remove excessive top padding from main view */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)