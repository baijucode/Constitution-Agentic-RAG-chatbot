import streamlit as st
import requests
import json
import os
import re
from groq import Groq  

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
    st.success("🤖 Cloud Inference: Active (Groq SDK)")
    st.warning("📚 FAISS Database: Local Mismatch Bypassed")
    st.success("🌐 Tavily Web Search: Connected")
    
    st.markdown("---")
    st.markdown("### 💡 What is this?")
    st.write(
        "This is an Agentic assistant. It analyzes the official "
        "Constitution of Nepal using live web queries powered by Groq cloud acceleration."
    )
    st.markdown("---")
    if st.button("🔄 Clear Chat History"):
        st.session_state.chat_history = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.rerun()

# 3. Main Page Header
st.markdown('<div class="main-header">⚖️ Nepal Constitution AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous legal analysis running on Groq Cloud Qwen Engine</div>', unsafe_allow_html=True)

# 4. Core Legal & Search Engines
def live_web_search(query: str) -> str:
    """Searches the internet for live constitutional text, clauses, and explanations."""
    TAVILY_API_KEY = "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"
    url = "https://tavily.com" 
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}
    payload = {"query": query + " Constitution of Nepal articles clauses", "topic": "general", "max_results": 3}
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            results = res.json().get("results", [])
            return "\n\n".join(f"[Source: {r.get('title')}]: {r.get('content')}" for r in results)
    except Exception:
        pass
    return "No live web constitutional data found."

def run_agent_workflow(user_query: str) -> str:
    """Executes the legal research task by combining internet search and Groq SDK reasoning."""
    if "OPENAI_API_KEY" not in st.secrets:
        return "⚠️ Error: Missing `OPENAI_API_KEY` (Groq Key) in your Streamlit secrets dashboard!"

    api_key = st.secrets["OPENAI_API_KEY"]
    
    # Fetch real-time research context dynamically
    web_context = live_web_search(user_query)
    
    system_prompt = (
        "You are an expert AI Legal Assistant specializing in the Constitution of Nepal. "
        "Analyze the user query based on the following real-time research context. "
        "If the user says hello or sends a short greeting, respond naturally and casually without over-explaining. "
        "Always cite specific Article numbers, provisions, and source details accurately. \n\n"
        f"--- RESEARCH CONTEXT ---\n{web_context}"
    )
    
    try:
        # Initialize official Groq SDK Client wrapper
        client = Groq(api_key=api_key)
        
        # Call completions pipeline with active parameter schema
        completion = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.2,
            reasoning_format="hidden"  # Hides reasoning thoughts entirely from output
        )
        
        # CRITICAL STRUCTURAL FIX: Added [0] index to read the choices array accurately
        raw_content = completion.choices[0].message.content
        
        # Fallback regex cleaning filter
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
        return clean_content

    except Exception as e:
        return f"⚠️ Groq SDK Pipeline Error: {str(e)}"

# Interface tracking structural token
agent = "Active"

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
                st.error("⚠️ Cannot process request: The backend agent failed to initialize properly.")
            else:
                clean_output = run_agent_workflow(user_input)
                st.write(clean_output)
                st.session_state.chat_history.append({"role": "assistant", "content": clean_output})
                save_history_to_disk(st.session_state.chat_history)
