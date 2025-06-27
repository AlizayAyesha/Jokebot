# password_reset.py
import streamlit as st
import random
import re
import sqlite3
from bcrypt import hashpw, gensalt
from otp_sender import send_otp_email

otp_store = {}

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def update_password(email, new_password):
    """Update the user's password in the database."""
    try:
        hashed = hashpw(new_password.encode(), gensalt())
        conn = sqlite3.connect("users.db")
        conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed, email))
        conn.commit()
        conn.close()
        print(f"✅ Password updated successfully for {email}")
        return True
    except Exception as e:
        print(f"❌ Error updating password for {email}: {str(e)}")
        return False

def reset_password_ui():
    st.title("🔐 Reset Password")

    email = st.text_input("Enter your email to reset password")

    if st.button("Send OTP"):
        if not is_valid_email(email):
            st.error("❌ Please enter a valid email address.")
            return
        print(f"Attempting to send OTP to {email}")  # Debug
        otp = str(random.randint(100000, 999999))
        otp_store[email] = otp
        success = send_otp_email(email, otp)
        print(f"Send OTP result: {success}")  # Debug
        if success:
            print("Setting session state to verify")  # Debug
            st.success("✅ OTP sent to your email.")
            st.session_state.email_for_reset = email
            st.session_state.step = "verify"
        else:
            st.error("❌ Failed to send OTP. Check email configuration.")
            return

    if st.session_state.get("step") == "verify":
        entered_otp = st.text_input("Enter OTP")
        new_password = st.text_input("New Password", type="password")

        if st.button("Reset Password"):
            if otp_store.get(st.session_state.email_for_reset) == entered_otp:
                success = update_password(st.session_state.email_for_reset, new_password)
                if success:
                    st.success("✅ Password reset successful!")
                    st.session_state.step = None
                    st.session_state.show_reset_password = False
                    del otp_store[st.session_state.email_for_reset]  
                    st.rerun()
                else:
                    st.error("❌ Failed to update password. Please try again.")
            else:
                st.error("❌ Incorrect OTP.")