"""
auth.py — Authentication: login, signup, session management
"""

import pandas as pd
import streamlit as st
import os

USERS_FILE = "users.csv"

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_users() -> pd.DataFrame:
    default_users = pd.DataFrame([
        {"username": "admin", "password": "admin123", "role": "Travel Agent", "email": "admin@tourism.com", "full_name": "Admin Account"},
        {"username": "user1", "password": "user123", "role": "User", "email": "user@tourism.com", "full_name": "Demo User"}
    ])
    
    if not os.path.exists(USERS_FILE):
        default_users.to_csv(USERS_FILE, index=False)
        return default_users
        
    df = pd.read_csv(USERS_FILE, dtype=str)
    
    # If file exists but is empty or missing admin, ensure demo accounts exist
    if df.empty or "admin" not in df["username"].values:
        df = pd.concat([df, default_users]).drop_duplicates(subset=["username"], keep="last")
        df.to_csv(USERS_FILE, index=False)
        
    return df


def _save_users(df: pd.DataFrame):
    df.to_csv(USERS_FILE, index=False)


# ── public API ────────────────────────────────────────────────────────────────

def authenticate(username: str, password: str):
    """Return user dict on success, None on failure."""
    df = _load_users()
    row = df[(df["username"] == username) & (df["password"] == password)]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def register_user(username: str, password: str, role: str,
                  email: str, full_name: str) -> tuple[bool, str]:
    """Register new user. Returns (success, message)."""
    df = _load_users()
    if username in df["username"].values:
        return False, "Username already exists."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    new_row = pd.DataFrame([{
        "username": username,
        "password": password,
        "role": role,
        "email": email,
        "full_name": full_name,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    _save_users(df)
    return True, "Account created successfully!"


def update_profile(username: str, new_username: str, new_password: str,
                   email: str, full_name: str) -> tuple[bool, str]:
    """Update user profile. Returns (success, message)."""
    df = _load_users()
    idx = df[df["username"] == username].index
    if idx.empty:
        return False, "User not found."
    if new_username != username and new_username in df["username"].values:
        return False, "New username already taken."
    df.loc[idx, "username"]  = new_username
    df.loc[idx, "email"]     = email
    df.loc[idx, "full_name"] = full_name
    if new_password:
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters."
        df.loc[idx, "password"] = new_password
    _save_users(df)
    # update session
    st.session_state.user["username"]  = new_username
    st.session_state.user["email"]     = email
    st.session_state.user["full_name"] = full_name
    return True, "Profile updated!"


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# ── UI pages ──────────────────────────────────────────────────────────────────
def show_login_page():
    
    # Inject page-specific CSS to unify tabs and form into one beautiful glass container
    st.markdown("""
    <style>
    /* Center the main block for login page */
    .block-container {
        max-width: 800px;
        padding-top: 4rem !important;
    }

    /* Style the tabs container to act as the main glass card */
    div[data-testid="stTabs"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.9)) !important;
        border-radius: 24px !important;
        padding: 2.5rem 3rem !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin: 0 auto !important;
    }

    /* Remove the default form background so it blends seamlessly into the tabs container */
    div[data-testid="stTabs"] div[data-testid="stForm"] {
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
        padding: 1rem 0 0 0 !important;
        backdrop-filter: none !important;
        max-width: 100% !important;
    }

    /* Tab Header alignment inside the glass card */
    div[data-baseweb="tab-list"] {
        margin-bottom: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Updated Title with styled HTML
    st.markdown("""
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h1 style='color: #ffffff; font-size: 3.8rem; font-weight: 800; margin-bottom: 0; padding-bottom: 0;'>
                ✈️ <span style='background: linear-gradient(135deg, #0ea5e9, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>TourismAI</span> 🌍
            </h1>
            <p style='color: #f8fafc; font-size: 1.4rem; font-weight: 700; margin-top: 20px; margin-bottom: 0; letter-spacing: 0.02em; line-height: 1.5; text-shadow: 0 4px 15px rgba(14, 165, 233, 0.2);'>
                AI-Driven Tourism Demand Forecasting and Destination Overcrowding Prediction System
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])

    # LOGIN
    with tab_login:
        st.markdown("<h3 style='text-align: center; font-size: 1.5rem; margin-bottom: 1.5rem;'>Welcome back 👋</h3>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.success(f"Welcome, {user['full_name'] or username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.caption("Demo: admin/admin123 | user1/user123")

    # SIGNUP
    with tab_signup:
        st.markdown("<h3 style='text-align: center; font-size: 1.5rem; margin-bottom: 1.5rem;'>Create your account 🚀</h3>", unsafe_allow_html=True)

        with st.form("signup_form"):
            col1, col2 = st.columns(2)

            with col1:
                full_name = st.text_input("Full Name")
                new_username = st.text_input("Username")
                role = st.selectbox("Role", ["User", "Travel Agent"])

            with col2:
                email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")

            st.markdown("<br>", unsafe_allow_html=True)
            reg_btn = st.form_submit_button("Create Account", use_container_width=True)
            
        if reg_btn:
            if new_password != confirm_pw:
                st.error("Passwords do not match.")
            elif not new_username or not new_password:
                st.error("Please fill in all required fields.")
            else:
                success, msg = register_user(new_username, new_password, role, email, full_name)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)