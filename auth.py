import streamlit as st
from db import register_user, authenticate_user
from password_reset import reset_password_ui

# ─── Custom Styling ───
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    .stApp {
        background: #f4f6f8;
        font-family: 'Inter', sans-serif;
    }

    h2 {
        color: #1a3c5e;
        font-weight: 600;
        font-size: 1.8em;
        margin-bottom: 20px;
    }

    .stTextInput > div > div > input {
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 12px;
        font-size: 1em;
        color: #1f2937;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 5px rgba(37, 99, 235, 0.3);
        outline: none;
    }

    .stTextInput > label {
        color: #374151;
        font-weight: 500;
        font-size: 0.9em;
        margin-bottom: 8px;
    }

    .stButton > button {
        background: #2563eb;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        font-size: 1em;
        transition: background 0.3s ease, transform 0.2s ease;
        width: 100%;
    }

    .stButton > button:hover {
        background: #1d4ed8;
        transform: translateY(-2px);
    }

    .stSuccess {
        background: #dcfce7;
        color: #15803d;
        border-radius: 8px;
        padding: 10px;
        font-weight: 500;
    }

    .stError {
        background: #fee2e2;
        color: #b91c1c;
        border-radius: 8px;
        padding: 10px;
        font-weight: 500;
    }

    .stForm {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Login Form ───
def login_form():
    with st.form("login_form"):
        st.subheader("🔐 Login")
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Password", type="password")

        col1, col2 = st.columns([2, 2])
        login_clicked = col1.form_submit_button("Login")

        if login_clicked:
            user = authenticate_user(email, password)
            if user:
                st.session_state.user = user
                st.success("🎉 Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")

    # Forgot password – outside the form
    if st.button("Forgot Password?"):
        st.session_state.show_reset_password = True
        st.rerun()


# ─── Sign Up Form ───
def signup_form():
    with st.form("signup_form"):
        st.subheader("👤 Create Account")
        name = st.text_input("👤 Name")
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Password", type="password")

        if st.form_submit_button("Sign Up"):
            try:
                register_user(email, name, password)
                st.session_state.user = {"email": email, "name": name}
                st.success("🎉 Registered and logged in!")
                st.rerun()
            except Exception:
                st.error("⚠️ Email already exists.")


# ─── Main Auth UI ───
def auth_ui():
    st.sidebar.title("🔐 Authentication")

    if "show_reset_password" not in st.session_state:
        st.session_state.show_reset_password = False

    if st.session_state.show_reset_password:
        reset_password_ui()
        if st.button("🔙 Back to Login"):
            st.session_state.show_reset_password = False
            st.rerun()
        st.stop()

    auth_mode = st.sidebar.radio("Choose", ["Login", "Sign Up"])

    if auth_mode == "Login":
        login_form()
    else:
        signup_form()
