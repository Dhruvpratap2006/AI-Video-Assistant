import streamlit as st
import time
import html
from dotenv import load_dotenv
from utils.audio_process import process_input
from core.transcribers import transcribe_all
from core.summarize import get_summary, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant — Meeting Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ── Root Variables ── */
:root {
    --bg:          #06060c;
    --surface:     #0d0d16;
    --surface-2:   #14141f;
    --surface-3:   #1c1c2b;
    --border:      #23233a;
    --border-hover:#3a3a5c;
    --accent:      #8b5cf6;
    --accent-glow: #a78bfa;
    --accent-dim:  rgba(139,92,246,0.12);
    --cyan:        #22d3ee;
    --cyan-dim:    rgba(34,211,238,0.10);
    --emerald:     #34d399;
    --emerald-dim: rgba(52,211,153,0.10);
    --amber:       #fbbf24;
    --amber-dim:   rgba(251,191,36,0.10);
    --rose:        #fb7185;
    --rose-dim:    rgba(251,113,133,0.10);
    --text:        #ececf4;
    --text-2:      #b0b0cc;
    --text-muted:  #6b6b94;
    --radius:      14px;
    --radius-sm:   8px;
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
}

/* Noise-grain overlay */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 50% -20%, rgba(139,92,246,0.08), transparent),
        radial-gradient(ellipse 60% 50% at 80% 110%, rgba(34,211,238,0.05), transparent);
    pointer-events: none;
    z-index: 0;
}

/* Subtle dot grid */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(139,92,246,0.06) 1px, transparent 1px);
    background-size: 24px 24px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 { font-family: 'Inter', sans-serif !important; color: var(--text) !important; }

/* ── Hero ── */
.hero-wrap {
    padding: 2.5rem 0 1rem 0;
    position: relative;
}
.hero-eyebrow {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--accent-glow);
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.hero-eyebrow::before {
    content: '';
    width: 20px;
    height: 2px;
    background: var(--accent);
    border-radius: 1px;
}
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: clamp(2.2rem, 4.5vw, 3.4rem);
    font-weight: 900;
    letter-spacing: -0.03em;
    line-height: 1.05;
    background: linear-gradient(135deg, #fff 0%, var(--accent-glow) 60%, var(--cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-top: 0.6rem;
    font-weight: 400;
    line-height: 1.5;
}

/* ── Glass Card ── */
.g-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
    backdrop-filter: blur(12px);
}
.g-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 8px 40px rgba(139,92,246,0.06);
    transform: translateY(-2px);
}

/* Colored left accent stripe */
.g-card[data-accent="purple"]::before { background: linear-gradient(180deg, var(--accent), var(--cyan)); }
.g-card[data-accent="cyan"]::before   { background: linear-gradient(180deg, var(--cyan), var(--emerald)); }
.g-card[data-accent="emerald"]::before{ background: linear-gradient(180deg, var(--emerald), var(--cyan)); }
.g-card[data-accent="amber"]::before  { background: linear-gradient(180deg, var(--amber), var(--rose)); }
.g-card[data-accent="rose"]::before   { background: linear-gradient(180deg, var(--rose), var(--accent)); }
.g-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px;
    height: 100%;
    border-radius: 3px 0 0 3px;
    background: linear-gradient(180deg, var(--accent), var(--cyan));
}

.g-card-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.g-card-body {
    font-size: 0.88rem;
    line-height: 1.75;
    color: var(--text-2);
}

/* ── Metric Pill ── */
.metric-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin: 0.75rem 0 0.25rem 0;
}
.metric-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.8rem;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 600;
    border: 1px solid;
}
.pill-purple  { background: var(--accent-dim); color: var(--accent-glow); border-color: rgba(139,92,246,0.2); }
.pill-cyan    { background: var(--cyan-dim);   color: var(--cyan);        border-color: rgba(34,211,238,0.2); }
.pill-emerald { background: var(--emerald-dim);color: var(--emerald);     border-color: rgba(52,211,153,0.2); }
.pill-amber   { background: var(--amber-dim);  color: var(--amber);       border-color: rgba(251,191,36,0.2); }
.pill-rose    { background: var(--rose-dim);    color: var(--rose);        border-color: rgba(251,113,133,0.2); }

/* ── Badges ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.22rem 0.65rem;
    border-radius: 6px;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.badge-purple  { background: var(--accent-dim); color: var(--accent-glow); border: 1px solid rgba(139,92,246,0.25); }
.badge-cyan    { background: var(--cyan-dim);   color: var(--cyan);        border: 1px solid rgba(34,211,238,0.25); }
.badge-emerald { background: var(--emerald-dim);color: var(--emerald);     border: 1px solid rgba(52,211,153,0.25); }

/* ── Inputs & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stFileUploader > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, #6d28d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
    text-transform: uppercase !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 30px rgba(139,92,246,0.35) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Pipeline Steps ── */
.step-item {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.6rem 0.85rem;
    margin: 0.3rem 0;
    border-radius: var(--radius-sm);
    background: var(--surface-2);
    border: 1px solid var(--border);
    font-size: 0.78rem;
    font-weight: 500;
    transition: all 0.3s ease;
}
.step-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    transition: all 0.3s;
}
.step-active  .step-dot { background: var(--accent-glow); box-shadow: 0 0 10px var(--accent-glow); animation: step-pulse 1.4s ease-in-out infinite; }
.step-done    .step-dot { background: var(--emerald); box-shadow: 0 0 6px rgba(52,211,153,0.4); }
.step-pending .step-dot { background: var(--border); }
.step-active  { border-color: rgba(139,92,246,0.3); background: rgba(139,92,246,0.05); }
.step-done    { border-color: rgba(52,211,153,0.2); }

@keyframes step-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

/* ── Chat ── */
.chat-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    max-height: 440px;
    overflow-y: auto;
    margin-bottom: 1rem;
}
.chat-msg {
    margin-bottom: 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    animation: msg-in 0.35s cubic-bezier(.4,0,.2,1);
}
@keyframes msg-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
.chat-tag {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}
.chat-bubble {
    display: inline-block;
    padding: 0.65rem 1rem;
    border-radius: 12px;
    font-size: 0.84rem;
    line-height: 1.65;
    max-width: 88%;
}
.user-tag    { color: var(--accent-glow); }
.bot-tag     { color: var(--cyan); }
.user-bubble { background: var(--accent-dim); border: 1px solid rgba(139,92,246,0.2); align-self: flex-end; }
.bot-bubble  { background: var(--cyan-dim);   border: 1px solid rgba(34,211,238,0.15); align-self: flex-start; }

/* ── Transcript Expander ── */
.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.25rem;
    font-size: 0.8rem;
    line-height: 1.85;
    max-height: 320px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Empty State ── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6rem 2rem;
    text-align: center;
}
.empty-icon {
    width: 80px; height: 80px;
    border-radius: 20px;
    background: var(--accent-dim);
    border: 1px solid rgba(139,92,246,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    margin-bottom: 1.5rem;
    animation: float 4s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-8px); }
}
.empty-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.4rem;
    letter-spacing: -0.02em;
}
.empty-desc {
    color: var(--text-muted);
    font-size: 0.85rem;
    max-width: 400px;
    line-height: 1.65;
}

/* ── Title Banner ── */
.title-banner {
    background: linear-gradient(135deg, var(--accent-dim), var(--cyan-dim));
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: var(--radius);
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.title-banner::after {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(139,92,246,0.08), transparent 70%);
    pointer-events: none;
}
.title-banner-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent-glow);
    margin-bottom: 0.5rem;
}
.title-banner-text {
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.02em;
}

/* ── Inline Input Bar ── */
.inline-input-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.5rem 0.6rem 0.5rem 1.25rem;
    margin-top: 1.5rem;
    max-width: 700px;
    transition: border-color 0.3s, box-shadow 0.3s;
}
.inline-input-bar:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(139,92,246,0.12);
}
.inline-input-bar .iib-icon {
    font-size: 1.1rem;
    opacity: 0.5;
    flex-shrink: 0;
}
.inline-input-bar .iib-hint {
    font-size: 0.72rem;
    color: var(--text-muted);
    white-space: nowrap;
}

/* ── Progress Dashboard ── */
.progress-dash {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2.5rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.progress-dash::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 50% 40% at 50% 30%, rgba(139,92,246,0.06), transparent);
    pointer-events: none;
}
.orbit-wrap {
    width: 100px; height: 100px;
    margin: 0 auto 1.5rem auto;
    position: relative;
}
.orbit-ring {
    position: absolute;
    inset: 0;
    border: 2px solid var(--border);
    border-top-color: var(--accent-glow);
    border-radius: 50%;
    animation: orbit-spin 1.2s linear infinite;
}
.orbit-ring-2 {
    position: absolute;
    inset: 8px;
    border: 2px solid transparent;
    border-bottom-color: var(--cyan);
    border-radius: 50%;
    animation: orbit-spin 1.8s linear infinite reverse;
}
.orbit-center {
    position: absolute;
    inset: 20px;
    background: var(--accent-dim);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    animation: orbit-pulse 2s ease-in-out infinite;
}
@keyframes orbit-spin {
    to { transform: rotate(360deg); }
}
@keyframes orbit-pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50%      { transform: scale(0.9); opacity: 0.7; }
}
.progress-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.3rem;
    letter-spacing: -0.02em;
}
.progress-sub {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-bottom: 1.75rem;
}
.prog-steps {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem;
    max-width: 580px;
    margin: 0 auto;
}
.prog-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.85rem;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-muted);
    transition: all 0.35s ease;
}
.prog-chip.chip-done {
    background: var(--emerald-dim);
    border-color: rgba(52,211,153,0.25);
    color: var(--emerald);
}
.prog-chip.chip-active {
    background: var(--accent-dim);
    border-color: rgba(139,92,246,0.3);
    color: var(--accent-glow);
    animation: chip-glow 1.5s ease-in-out infinite;
}
@keyframes chip-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139,92,246,0); }
    50%      { box-shadow: 0 0 12px 2px rgba(139,92,246,0.15); }
}
.prog-chip-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--border);
    flex-shrink: 0;
}
.chip-done .prog-chip-dot  { background: var(--emerald); }
.chip-active .prog-chip-dot { background: var(--accent-glow); animation: step-pulse 1.4s ease-in-out infinite; }

/* ── Misc ── */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.75rem 0 !important; }
.stProgress > div > div > div { background: linear-gradient(90deg, var(--accent), var(--cyan)) !important; border-radius: 4px !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.78rem !important; font-weight: 500 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Section Header ── */
.section-header {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
}

/* ── Feature card for empty state ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 2.5rem;
    max-width: 700px;
}
.feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    transition: all 0.3s ease;
}
.feature-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}
.feature-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}
.feature-name {
    font-weight: 700;
    font-size: 0.78rem;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.feature-desc {
    font-size: 0.68rem;
    color: var(--text-muted);
    line-height: 1.4;
}

/* ── Sidebar branding ── */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0 1.5rem 0;
}
.sidebar-logo {
    width: 40px; height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--accent), var(--cyan));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.sidebar-name {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: -0.02em;
    line-height: 1.15;
}
.sidebar-name span {
    display: block;
    font-size: 0.6rem;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.15rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State ───────────────────────────────────────────────────────────────
defaults = {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
    "active_tab": "summary",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helpers ─────────────────────────────────────────────────────────────────────
def step_class(key):
    s = st.session_state.pipeline_steps.get(key, "pending")
    return f"step-{s}"

def render_step(label, key, icon):
    cls = step_class(key)
    st.markdown(f"""
    <div class="step-item {cls}">
        <div class="step-dot"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

def safe(text):
    """Escape HTML but preserve line breaks."""
    return html.escape(str(text)).replace("\n", "<br>")

# ─── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">🎬</div>
        <div class="sidebar-name">
            AI Video
            <span>Meeting Intelligence</span>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<span class="badge badge-purple">⚡ Input Source</span>', unsafe_allow_html=True)
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    source = st.text_input(
        "Source",
        placeholder="https://youtube.com/watch?v=... or C:\\path\\to\\video.mp4",
        label_visibility="collapsed",
    )

    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("⚡  Analyse Video", use_container_width=True)

    # Pipeline steps — always visible in sidebar
    if st.session_state.pipeline_steps:
        st.markdown("---")
        st.markdown('<span class="badge badge-emerald">🔄 Pipeline Status</span>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
        steps_config = [
            ("audio",      "🔊", "Audio Extraction"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Data Extraction"),
            ("rag",        "🧠", "RAG Engine Build"),
        ]
        for key, icon, label in steps_config:
            render_step(label, key, icon)

    # Sidebar footer
    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.65rem;color:var(--text-muted);line-height:1.6;padding:0.5rem 0">
        <strong>Powered by</strong><br>
        Whisper · MistralAI · LangChain<br>
        ChromaDB · Streamlit
    </div>""", unsafe_allow_html=True)


# ─── Main Content ────────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">AI-Powered Analysis</div>
    <div class="hero-title">Video Assistant</div>
    <div class="hero-sub">Transcribe, summarise, extract insights, and chat with any video or meeting recording.</div>
</div>""", unsafe_allow_html=True)

# Inline input bar in the main area
if not st.session_state.result:
    in_col1, in_col2, in_col3 = st.columns([4, 1.2, 1], gap="small")
    with in_col1:
        main_source = st.text_input(
            "main_source",
            value=source if source else "",
            placeholder="🔗  Paste a YouTube URL or local file path here…",
            label_visibility="collapsed",
            key="main_source_input",
        )
    with in_col2:
        main_lang = st.selectbox("Lang", ["english", "hinglish"], index=0, label_visibility="collapsed", key="main_lang")
    with in_col3:
        main_run = st.button("🚀 Analyse", use_container_width=True, key="main_run_btn")
else:
    main_source = None
    main_lang = None
    main_run = False

st.markdown("---")

# ─── Run Pipeline ────────────────────────────────────────────────────────────────
# Accept trigger from either the sidebar button or the main-area button
final_source = (main_source.strip() if main_source else "") or (source.strip() if source else "")
final_lang = main_lang if main_lang else language
should_run = run_btn or main_run

if should_run:
    if not final_source:
        st.error("⚠️ Please enter a YouTube URL or local file path.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_area = st.empty()

        STEPS_META = [
            ("audio",      "🔊", "Audio Extraction"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Data Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]

        def mark(key, state):
            st.session_state.pipeline_steps[key] = state

        def render_progress_dashboard(current_label):
            chips_html = ""
            for skey, sicon, slabel in STEPS_META:
                s = st.session_state.pipeline_steps.get(skey, "pending")
                cls = "chip-done" if s == "done" else "chip-active" if s == "active" else ""
                chips_html += f'<div class="prog-chip {cls}"><div class="prog-chip-dot"></div>{sicon} {slabel}</div>'
            with progress_area.container():
                st.markdown(f"""
                <div class="progress-dash">
                    <div class="orbit-wrap">
                        <div class="orbit-ring"></div>
                        <div class="orbit-ring-2"></div>
                        <div class="orbit-center">🎬</div>
                    </div>
                    <div class="progress-title">Analysing your video…</div>
                    <div class="progress-sub">{current_label}</div>
                    <div class="prog-steps">{chips_html}</div>
                </div>""", unsafe_allow_html=True)

        try:
            render_progress_dashboard("Preparing pipeline…")

            mark("audio", "active")
            render_progress_dashboard("Extracting audio from source…")
            chunks = process_input(final_source)
            mark("audio", "done")

            mark("transcript", "active")
            render_progress_dashboard("Transcribing audio with Whisper…")
            transcript = transcribe_all(chunks, final_lang)
            mark("transcript", "done")

            mark("title", "active")
            render_progress_dashboard("Generating a meeting title…")
            title = generate_title(transcript)
            mark("title", "done")

            mark("summary", "active")
            render_progress_dashboard("Summarising the transcript…")
            summary = get_summary(transcript)
            mark("summary", "done")

            mark("extract", "active")
            render_progress_dashboard("Extracting action items, decisions & questions…")
            action_items = extract_action_items(transcript)
            decisions    = extract_key_decisions(transcript)
            questions    = extract_questions(transcript)
            mark("extract", "done")

            mark("rag", "active")
            render_progress_dashboard("Building RAG knowledge engine…")
            rag_chain = build_rag_chain(transcript)
            mark("rag", "done")

            st.session_state.result = {
                "title":          title,
                "transcript":     transcript,
                "summary":        summary,
                "action_items":   action_items,
                "key_decisions":  decisions,
                "open_questions": questions,
                "rag_chain":      rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_area.success("✅ Analysis complete — results ready below!")
            time.sleep(0.8)
            progress_area.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_area.error(f"❌ Pipeline error: {e}")

# ─── Results Dashboard ──────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # ── Title Banner
    st.markdown(f"""
    <div class="title-banner">
        <div class="title-banner-label">📌 Session Title</div>
        <div class="title-banner-text">{safe(r['title'])}</div>
        <div class="metric-row">
            <span class="metric-pill pill-purple">✅ Analysed</span>
            <span class="metric-pill pill-cyan">📝 {len(r['transcript'].split())} words</span>
            <span class="metric-pill pill-emerald">🧠 RAG Ready</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Tabs for results
    tab_summary, tab_actions, tab_decisions, tab_questions, tab_transcript = st.tabs([
        "📋 Summary",
        "✅ Action Items",
        "🔑 Key Decisions",
        "❓ Open Questions",
        "📝 Full Transcript",
    ])

    with tab_summary:
        st.markdown(f"""
        <div class="g-card" data-accent="purple">
            <div class="g-card-label">📋 Meeting Summary</div>
            <div class="g-card-body">{safe(r['summary'])}</div>
        </div>""", unsafe_allow_html=True)

    with tab_actions:
        st.markdown(f"""
        <div class="g-card" data-accent="emerald">
            <div class="g-card-label">✅ Action Items</div>
            <div class="g-card-body">{safe(r['action_items'])}</div>
        </div>""", unsafe_allow_html=True)

    with tab_decisions:
        st.markdown(f"""
        <div class="g-card" data-accent="cyan">
            <div class="g-card-label">🔑 Key Decisions</div>
            <div class="g-card-body">{safe(r['key_decisions'])}</div>
        </div>""", unsafe_allow_html=True)

    with tab_questions:
        st.markdown(f"""
        <div class="g-card" data-accent="amber">
            <div class="g-card-label">❓ Open Questions</div>
            <div class="g-card-body">{safe(r['open_questions'])}</div>
        </div>""", unsafe_allow_html=True)

    with tab_transcript:
        st.markdown(f'<div class="transcript-box">{safe(r["transcript"])}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    # Chat history
    if st.session_state.chat_history:
        chat_html = '<div class="chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-tag user-tag">You</span>
                    <div class="chat-bubble user-bubble">{safe(msg['content'])}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-tag bot-tag">🤖 Assistant</span>
                    <div class="chat-bubble bot-bubble">{safe(msg['content'])}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="g-card" style="text-align:center;padding:2.5rem">
            <div style="font-size:2.5rem;margin-bottom:0.6rem;opacity:0.6">💬</div>
            <div style="color:var(--text-muted);font-size:0.82rem;line-height:1.6">
                Ask anything about your video — key takeaways, specific topics,<br>or follow-up questions.
            </div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_q = st.text_input(
            "Ask a question",
            placeholder="What were the main decisions made in this meeting?",
            label_visibility="collapsed",
            key="chat_input",
        )
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True, key="send_chat")

    if send_btn and user_q.strip():
        with st.spinner("🤖 Thinking…"):
            answer = ask_question(r["rag_chain"], user_q.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_q.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️  Clear Chat History", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

# ─── Empty State ─────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🎬</div>
        <div class="empty-title">Ready to Analyse</div>
        <div class="empty-desc">
            Paste a YouTube URL or local file path in the sidebar, select your language, and hit <strong>Analyse Video</strong> to unlock AI-powered insights.
        </div>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <div class="feature-name">Transcription</div>
                <div class="feature-desc">Whisper-powered speech to text</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📋</div>
                <div class="feature-name">Summarisation</div>
                <div class="feature-desc">LLM-driven meeting summaries</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <div class="feature-name">RAG Chat</div>
                <div class="feature-desc">Ask questions about your video</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
