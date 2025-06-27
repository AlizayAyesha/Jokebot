import streamlit as st
import asyncio
import json
import os
import random
from datetime import datetime
from agents import Agent, Runner, ItemHelpers
from db import init_db, register_user, authenticate_user
from password_reset import reset_password_ui
from dotenv import load_dotenv
import logging

# ─── SETUP LOGGING ───
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── LOAD ENVIRONMENT VARIABLES ───
if not load_dotenv():
    logger.error("Failed to load .env file. Check file format and path.")
    st.error("⚠️ Failed to load environment variables. Please check your .env file.")

# ─── SETUP ───
init_db()
st.set_page_config(page_title="JokeBot Pro", layout="centered", page_icon="🤖")

# ─── CUSTOM CSS FOR RED, BLACK, AND WHITE THEME ───
st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1A1A1A;
    }
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #FF0000 !important;
    }
    /* Text */
    .stMarkdown, .stText, .stTextInput > label, .stRadio > label, .stButton > label {
        color: #FFFFFF !important;
    }
    /* Buttons */
    .stButton > button {
        background-color: #FF0000;
        color: #FFFFFF;
        border: 1px solid #FF0000;
        border-radius: 5px;
        padding: 8px 16px;
    }
    .stButton > button:hover {
        background-color: #CC0000;
        border-color: #CC0000;
    }
    /* Chat input */
    .stChatInput input {
        background-color: #333333;
        color: #FFFFFF;
        border: 1px solid #FF0000;
        border-radius: 5px;
    }
    /* Chat messages */
    .stChatMessage {
        background-color: #222222;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stChatMessage[data-testid="stChatMessage-user"] {
        border-left: 4px solid #FF0000;
    }
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        border-left: 4px solid #FF6666;
    }
    /* Form containers */
    .stForm {
        background-color: #1A1A1A;
        border: 1px solid #FF0000;
        border-radius: 5px;
        padding: 10px;
    }
    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        margin-bottom: 5px;
    }
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1A1A1A;
    }
    ::-webkit-scrollbar-thumb {
        background: #FF0000;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #CC0000;
    }
    /* Input placeholders */
    input::placeholder {
        color: #AAAAAA !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── SESSION STATE ───
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "show_reset_password" not in st.session_state:
    st.session_state.show_reset_password = False

# ─── CREATE NEW CONVERSATION ───
def create_new_conversation(email):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    random_num = random.randint(1000, 9999)
    safe_id = f"chat_{timestamp}_{random_num}"
    file_path = os.path.join(f"user_data/{email}_conversations", f"{safe_id}.json")
    st.session_state.current_conversation_id = safe_id
    st.session_state.messages = []
    # Create an empty conversation file to avoid FileNotFoundError
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump([], f)
    st.session_state.conversations.append({
        "title": f"Chat - {timestamp}",
        "file": file_path,
        "id": safe_id
    })
    logger.info(f"Created new conversation {safe_id} for user {email}")
    return safe_id

# ─── LOAD OLD CONVERSATIONS ───
def load_conversations(email):
    conversation_dir = f"user_data/{email}_conversations"
    files = []
    try:
        files = sorted([f for f in os.listdir(conversation_dir) if f.endswith(".json")], key=lambda x: x)
    except FileNotFoundError:
        logger.warning(f"Conversation directory {conversation_dir} not found")
    conversations = []
    for f in files:
        file_path = os.path.join(conversation_dir, f)
        conv_id = f.replace(".json", "")
        try:
            with open(file_path, "r") as file:
                messages = json.load(file)
                title = messages[0]["content"][:30] + "..." if messages else f"Chat - {conv_id.split('_')[1]}"
        except (FileNotFoundError, json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to load conversation {f}: {e}")
            title = f"Chat - {conv_id.split('_')[1]}"
        conversations.append({"title": title, "file": file_path, "id": conv_id})
    st.session_state.conversations = conversations
    logger.info(f"Loaded {len(conversations)} conversations for user {email}")

# ─── SAVE CONVERSATION ───
def save_current_conversation():
    if st.session_state.current_conversation_id and st.session_state.messages:
        current_file = next((c["file"] for c in st.session_state.conversations
                            if c["id"] == st.session_state.current_conversation_id), None)
        if current_file:
            try:
                with open(current_file, "w") as f:
                    json.dump(st.session_state.messages, f, indent=2)
                first_message = st.session_state.messages[0]["content"][:30] + "..." if st.session_state.messages else f"Chat - {st.session_state.current_conversation_id.split('_')[1]}"
                for conv in st.session_state.conversations:
                    if conv["id"] == st.session_state.current_conversation_id:
                        conv["title"] = first_message
                        break
                logger.info(f"Saved conversation {st.session_state.current_conversation_id} to {current_file}")
            except Exception as e:
                logger.error(f"Failed to save conversation {st.session_state.current_conversation_id}: {e}")
                st.error("⚠️ Failed to save conversation. Please try again.")

# ─── AUTH ───
st.sidebar.title("🔐 JokeBot Login")

if not st.session_state.user:
    st.markdown(
        "<h1 style='text-align: center; margin-top: 120px;'>👋 Welcome to JokeBot!</h1>"
        "<h3 style='text-align: center; font-weight: normal;'>Please login to get started</h3>",
        unsafe_allow_html=True
    )

    if st.session_state.show_reset_password:
        reset_password_ui()
        if st.button("🔙 Back to Login"):
            st.session_state.show_reset_password = False
            st.rerun()
        st.stop()

    auth_mode = st.sidebar.radio("Choose", ["Login", "Sign Up"])
    if auth_mode == "Login":
        with st.sidebar.form("login_form"):
            st.subheader("🔐 Login")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                user = authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("🎉 Login successful!")
                    os.makedirs(f"user_data/{email}_conversations", exist_ok=True)
                    create_new_conversation(email)
                    load_conversations(email)
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")
        if st.sidebar.button("Forgot Password?"):
            st.session_state.show_reset_password = True
            st.rerun()
    else:
        with st.sidebar.form("signup_form"):
            st.subheader("👤 Create Account")
            name = st.text_input("👤 Name")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("Sign Up"):
                try:
                    register_user(email, name, password)
                    st.session_state.user = {"email": email, "name": name}
                    st.success("🎉 Registered and logged in!")
                    os.makedirs(f"user_data/{email}_conversations", exist_ok=True)
                    create_new_conversation(email)
                    load_conversations(email)
                    st.rerun()
                except Exception:
                    st.error("⚠️ Email already exists.")
    st.stop()

# ─── SETUP USER FOLDERS ───
email = st.session_state.user["email"]
name = st.session_state.user["name"]
conversation_dir = f"user_data/{email}_conversations"
os.makedirs(conversation_dir, exist_ok=True)

if not st.session_state.conversations:
    load_conversations(email)

# ─── SIDEBAR ───
st.sidebar.success(f"Welcome, {name}!")

col1, col2 = st.sidebar.columns([1, 1])
with col1:
    if st.button("➕ New Chat"):
        save_current_conversation()
        create_new_conversation(email)
        load_conversations(email)  # Reload conversations to update sidebar
        st.rerun()

with col2:
    if st.button("🚪 Logout"):
        save_current_conversation()
        for k in ["user", "messages", "current_conversation_id", "conversations"]:
            st.session_state.pop(k, None)
        st.rerun()

if st.sidebar.button("🗑️ Delete All Chats"):
    save_current_conversation()
    for conv in st.session_state.conversations:
        try:
            os.remove(conv["file"])
        except FileNotFoundError:
            pass
    st.session_state.conversations = []
    st.session_state.messages = []
    st.session_state.current_conversation_id = None
    st.success("🧹 All chats deleted.")
    logger.info(f"Deleted all chats for user {email}")
    st.rerun()

# ─── CHAT HISTORY ───
st.sidebar.subheader("📜 Chat History")
for conv in sorted(st.session_state.conversations, key=lambda x: x["id"], reverse=True):
    if st.sidebar.button(conv["title"], key=f"chat_btn_{conv['id']}"):
        save_current_conversation()
        st.session_state.current_conversation_id = conv["id"]
        try:
            with open(conv["file"], "r") as f:
                st.session_state.messages = json.load(f)
            logger.info(f"Loaded conversation {conv['id']}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load conversation {conv['id']}: {e}")
            st.session_state.messages = []
        st.rerun()

# ─── MAIN CHAT ───
user = st.session_state.user
st.title(f"💬 Chat with JokeBot, {user['name']}")

# Ensure a conversation is active
if not st.session_state.current_conversation_id:
    create_new_conversation(email)

# Display messages
chat_container = st.container()
with chat_container:
    for msg in sorted(st.session_state.messages, key=lambda x: x.get("timestamp", "")):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # Auto-scroll to the bottom
    st.markdown(
        """
        <script>
        const chatContainer = window.parent.document.querySelector('.stChatMessage:last-child');
        if (chatContainer) {
            chatContainer.scrollIntoView({ behavior: 'smooth' });
        }
        </script>
        """,
        unsafe_allow_html=True
    )

user_input = st.chat_input("Say something...", key="chatbox")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            agent = Agent(name="JokeBot", instructions="Be humorous")
            runner = Runner.run_streamed(agent, user_input, user['name'])

            response_holder = [""]  # Mutable container for response

            async def stream_response():
                try:
                    async for event in runner.stream_events():
                        content = ItemHelpers.text_message_output(event.item)
                        response_holder[0] += content
                        placeholder.markdown(response_holder[0])
                except Exception as e:
                    logger.error(f"Error streaming response: {e}")
                    placeholder.markdown("⚠️ Sorry, something went wrong. Please try again.")

            asyncio.run(stream_response())

            if response_holder[0]:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_holder[0],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                logger.info(f"Appended assistant response for input: {user_input[:30]}...")
            else:
                logger.warning("No response received from API")

    save_current_conversation()
    load_conversations(email)  # Reload conversations to update sidebar
    st.rerun()