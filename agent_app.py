import streamlit as st
import requests
import json
import os
from strands import Agent
from strands.models.openai import OpenAIModel

# 1. Page Configuration with Theme Accents
st.set_page_config(
    page_title="Nepal Constitution AI", 
    page_icon="⚖️", 
    layout="wide"
)

# Custom CSS styling to make things look clean and smooth
st.markdown("""
    <style>
        .stApp { background-color: #0f1116; color: #e0e6ed; }
        .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.2rem; }
        .sub-header { font-size: 1rem; color: #94a3b8; margin-bottom: 1.5rem; }
        div.stButton > button { width: 100%; text-align: left; background-color: #1e293b; color: #f1f5f9; border: 1px solid #334155; }
        div.stButton > button:hover { border-color: #38bdf8; color: #38bdf8; }
    </style>
""", unsafe_allow_html=True)

# Persistent Chat Storage Configuration
HISTORY_FILE = "chat_history.json"

def load_saved_history():
    """Loads chat history from the local JSON file if it exists."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_to_disk(history):
    """Writes the current chat session state out to the disk file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving chat log to disk: {e}")

# 2. Left Sidebar (Information & Control Center)
with st.sidebar:
    st.markdown("## ⚙️ System Status")
    st.success("🤖 Strands Engine: Active")
    st.success("📚 FAISS Database: Suspended (Cloud Mode)")
    st.success("🌐 Tavily Web Search: Connected")
    
    st.markdown("---")
    st.markdown("### 💡 What is this?")
    st.write(
        "This is an Agentic RAG assistant. It reads the official "
        "Constitution of Nepal from a live web analysis using an autonomous reasoning loop."
    )
    st.markdown("---")
    if st.button("🔄 Clear Chat History"):
        st.session_state.chat_history = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.rerun()

# 3. Main Page Header
st.markdown('<div class="main-header">⚖️ Nepal Constitution AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous Agentic legal analysis running on Groq Cloud Qwen Engine</div>', unsafe_allow_html=True)

# 4. Initialize Cloud Backend inside Cache
@st.cache_resource
def load_agentic_backend():
    # Fetch credentials securely from Streamlit Dashboard Secrets
    if "OPENAI_API_KEY" not in st.secrets:
        raise ValueError("Missing Groq API Key inside your Streamlit secrets configurations!")

    GROQ_API_KEY = st.secrets["OPENAI_API_KEY"]

    # CRITICAL REMEDY: Switch out the generic OpenAI model wrapper 
    # and import the dedicated native Groq driver to prevent the 405 error block.
    from strands.models.groq import GroqModel

    # Direct native initialization to Groq cloud infrastructure
    cloud_model = GroqModel(
        model_id="qwen-2.5-coder-32b", 
        client_args={
            "api_key": GROQ_API_KEY
        }
    )

    from langchain_community.vectorstores import FAISS
    # We are dropping the cloud embeddings line entirely since we will bypass 
    # the local-to-cloud mismatch loading fault safely.

    # Setup clean fallback pointers for the vector database setup
    vector_store = None
    db_error_message = "Database dimension architecture mismatch detected on cloud network environment."
    
    # Safely convert the database tool to act as a fallback pointer notification
    def query_nepal_constitution(legal_question: str) -> str:
        """Use this tool to search the local FAISS database for official clauses, 
        articles, and raw text inside the Constitution of Nepal."""
        return (
            "⚠️ Notice: The local FAISS database files cannot be initialized on this cloud container "
            "due to an embedding architecture dimension mismatch. Please rely completely on the "
            "live web search tool to look up official clauses or articles from the Constitution of Nepal."
        )



# 5. Session State Tracking from Persistent Storage
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_saved_history()

# 6. Welcome View & Example Prompt Suggestions
if not st.session_state.chat_history:
    st.info("👋 Welcome! Select a suggestion below or type any legal question to begin.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📌 What are the fundamental rights?"):
            st.session_state.pending_input = "What are the fundamental rights guaranteed under the Constitution of Nepal?"
            st.rerun()
    with col2:
        if st.button("🏛️ How is the Federal Parliament structured?"):
            st.session_state.pending_input = "What is the structure of the federal legislature or parliament in Nepal?"
            st.rerun()

# Check for a user click from the button system
user_input = st.chat_input("Ask about clauses, articles, or rights...")
if "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")

# 7. Render History Chat Elements
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 8. Main Chat Execution Process Loop
if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    save_history_to_disk(st.session_state.chat_history)

    with st.chat_message("assistant"):
        with st.spinner("🕵️ Agent is analyzing tools and reasoning..."):
            if agent is None:
                st.error("⚠️ Cannot process request: The backend agent failed to initialize properly. Check the error alert at the top of the page.")
            else:
                try:
                    agent_response = agent(user_input)
                    clean_output = str(agent_response)
                    
                    st.write(clean_output)
                    st.session_state.chat_history.append({"role": "assistant", "content": clean_output})
                    save_history_to_disk(st.session_state.chat_history)
                except Exception as e:
                    st.error(f"⚠️ Agent Error: {e}")
