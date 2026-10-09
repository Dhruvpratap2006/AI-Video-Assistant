import os
import time
import html
import json
import traceback
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Core Pipeline Imports
from utils.audio_process import process_input
from core.transcribers import transcribe_all
from core.summarize import get_summary, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

# Export Utilities
from utils.export_helper import (
    generate_pdf,
    generate_markdown,
    parse_action_items_structured,
    parse_key_decisions_list,
    parse_open_questions_list,
)

load_dotenv()

# ─── Page Configuration ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Video AI — Meeting & Video Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Design System: Deep Teal + Coral (simple Inter font, mobile responsive) ─────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-base:        #0a1214;
    --bg-surface:     #0f1b1e;
    --bg-surface-2:   #142427;
    --bg-surface-3:   #1b3034;
    --border-subtle:  rgba(255, 255, 255, 0.08);
    --border-medium:  rgba(255, 255, 255, 0.14);
    --border-glow:    rgba(45, 212, 191, 0.40);

    --accent:         #2dd4bf;
    --accent-glow:    #5eead4;
    --accent-dim:     rgba(45, 212, 191, 0.13);

    --sky:            #38bdf8;
    --sky-dim:        rgba(56, 189, 248, 0.13);

    --gold:           #facc15;
    --gold-dim:       rgba(250, 204, 21, 0.12);

    --coral:          #fb7185;
    --coral-dim:      rgba(251, 113, 133, 0.13);

    --lime:           #a3e635;
    --lime-dim:       rgba(163, 230, 53, 0.12);

    --text-primary:   #f1f5f4;
    --text-secondary: #c5d3d1;
    --text-muted:     #6f8785;

    --radius-xl:      20px;
    --radius-lg:      14px;
    --radius-md:      10px;
    --radius-full:    9999px;

    --shadow-glass:   0 10px 36px rgba(0, 0, 0, 0.55);
    --shadow-glow:    0 0 32px rgba(45, 212, 191, 0.20);
}

/* ── Global Canvas ── */
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 50% at 15% -10%, rgba(45, 212, 191, 0.16), transparent 70%),
        radial-gradient(ellipse 60% 60% at 90% 95%, rgba(251, 113, 133, 0.10), transparent 70%);
    pointer-events: none;
    z-index: -2;
}
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
    background-size: 36px 36px;
    pointer-events: none;
    z-index: -1;
}

header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }

.block-container { padding-top: 2rem !important; max-width: 1200px; }

/* ── Navbar ── */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    padding: 0.95rem 1.6rem;
    background: rgba(15, 27, 30, 0.8);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(18px);
    box-shadow: var(--shadow-glass);
    margin-bottom: 1.75rem;
}
.nav-brand { display: flex; align-items: center; gap: 12px; }
.brand-icon {
    width: 42px; height: 42px;
    border-radius: var(--radius-md);
    background: linear-gradient(135deg, var(--accent), var(--sky));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 0 18px rgba(45, 212, 191, 0.4);
}
.brand-info h1 {
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em;
    margin: 0 !important; padding: 0 !important;
    color: #fff !important;
}
.brand-info p {
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent) !important;
    margin: 0 !important;
}
.nav-status-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 14px;
    border-radius: var(--radius-full);
    background: var(--bg-surface-2);
    border: 1px solid var(--border-subtle);
    font-size: 0.74rem; font-weight: 600;
    color: var(--lime);
}
.pulse-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--lime);
    box-shadow: 0 0 10px var(--lime);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(0.75); opacity: 0.4; }
}

/* ── Hero ── */
.hero-section {
    padding: 2.4rem 2.1rem;
    border-radius: var(--radius-xl);
    background: linear-gradient(135deg, rgba(20, 36, 39, 0.85) 0%, rgba(10, 18, 20, 0.95) 100%);
    border: 1px solid var(--border-glow);
    box-shadow: var(--shadow-glass), var(--shadow-glow);
    backdrop-filter: blur(22px);
    margin-bottom: 1.75rem;
    position: relative;
    overflow: hidden;
}
.hero-section::before {
    content: '';
    position: absolute;
    top: 0; left: 15%; right: 15%; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-glow), var(--sky), transparent);
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px;
    border-radius: var(--radius-full);
    background: var(--accent-dim);
    color: var(--accent-glow);
    border: 1px solid rgba(45, 212, 191, 0.35);
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    margin-bottom: 0.85rem;
}
.hero-title {
    font-size: clamp(1.7rem, 4vw, 3rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 0.8rem;
    background: linear-gradient(135deg, #ffffff 35%, var(--accent-glow) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    max-width: 840px;
    margin-bottom: 1.3rem;
    line-height: 1.65;
}
.hero-features-strip { display: flex; gap: 10px; flex-wrap: wrap; }
.feature-tag {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 13px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-full);
    font-size: 0.74rem; font-weight: 600;
    color: var(--text-secondary);
}

/* ── Panels ── */
.panel-header-badge {
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--accent-glow);
    margin-bottom: 0.9rem;
    display: flex; align-items: center; gap: 6px;
}
.engine-card {
    background: var(--bg-surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 1.1rem;
    height: 100%;
    transition: all 0.25s ease;
}
.engine-card:hover { border-color: var(--accent-glow); transform: translateY(-2px); }

/* ── Neural pipeline visualizer ── */
.neural-pipeline-box {
    background: linear-gradient(145deg, #0d1a1d 0%, #070e10 100%);
    border: 1px solid rgba(45, 212, 191, 0.4);
    border-radius: 1.25rem;
    padding: 2.1rem 1.6rem;
    margin: 1.5rem 0;
    text-align: center;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.7), 0 0 32px rgba(45, 212, 191, 0.2);
    position: relative;
    overflow: hidden;
    animation: fadeInBox 0.4s ease-out forwards;
}
@keyframes fadeInBox {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
.neural-pipeline-box::after {
    content: '';
    position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle at center, rgba(45, 212, 191, 0.09), transparent 60%);
    pointer-events: none;
    animation: rotate-radial 15s linear infinite;
}
@keyframes rotate-radial { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.waveform-equalizer {
    display: flex; align-items: center; justify-content: center;
    gap: 6px; height: 52px;
    margin: 1.25rem 0 1.5rem 0;
}
.wave-bar {
    width: 5px;
    background: linear-gradient(180deg, #5eead4, #38bdf8, #fb7185);
    border-radius: 9999px;
    animation: equalize 1.1s ease-in-out infinite alternate;
    box-shadow: 0 0 12px rgba(45, 212, 191, 0.5);
}
.wave-bar:nth-child(1)  { height: 18px; animation-delay: 0.1s; }
.wave-bar:nth-child(2)  { height: 34px; animation-delay: 0.25s; }
.wave-bar:nth-child(3)  { height: 48px; animation-delay: 0.4s; }
.wave-bar:nth-child(4)  { height: 28px; animation-delay: 0.15s; }
.wave-bar:nth-child(5)  { height: 52px; animation-delay: 0.5s; }
.wave-bar:nth-child(6)  { height: 42px; animation-delay: 0.3s; }
.wave-bar:nth-child(7)  { height: 50px; animation-delay: 0.45s; }
.wave-bar:nth-child(8)  { height: 30px; animation-delay: 0.2s; }
.wave-bar:nth-child(9)  { height: 44px; animation-delay: 0.35s; }
.wave-bar:nth-child(10) { height: 24px; animation-delay: 0.1s; }
.wave-bar:nth-child(11) { height: 38px; animation-delay: 0.55s; }
.wave-bar:nth-child(12) { height: 18px; animation-delay: 0.25s; }
.wave-bar:nth-child(13) { height: 46px; animation-delay: 0.35s; }
.wave-bar:nth-child(14) { height: 26px; animation-delay: 0.45s; }
.wave-bar:nth-child(15) { height: 50px; animation-delay: 0.15s; }
.wave-bar:nth-child(16) { height: 20px; animation-delay: 0.3s; }
@keyframes equalize {
    0%   { transform: scaleY(0.25); opacity: 0.4; }
    50%  { transform: scaleY(1.0); opacity: 1; filter: drop-shadow(0 0 8px #5eead4); }
    100% { transform: scaleY(0.4); opacity: 0.6; }
}

.step-chips-grid {
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 9px; max-width: 820px; margin: 1.25rem auto 0 auto;
}
.step-badge {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 7px 15px;
    border-radius: var(--radius-full);
    font-size: 0.74rem; font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: #0f1a1c;
    color: #8aa3a0;
    transition: all 0.3s ease;
}
.step-badge.done {
    background: rgba(163, 230, 53, 0.13);
    border-color: rgba(163, 230, 53, 0.35);
    color: var(--lime);
}
.step-badge.active {
    background: rgba(45, 212, 191, 0.2);
    border-color: var(--accent);
    color: #fff;
    box-shadow: 0 0 16px rgba(45, 212, 191, 0.35);
    animation: activeStepPulse 1.8s infinite;
}
@keyframes activeStepPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.03); } }

/* ── Results banner ── */
.brief-banner {
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.14) 0%, rgba(56, 189, 248, 0.08) 100%);
    border: 1px solid var(--border-glow);
    border-radius: var(--radius-lg);
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-glow);
    position: relative;
    overflow: hidden;
}
.brief-banner::after {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(45, 212, 191, 0.12), transparent 70%);
    pointer-events: none;
}
.brief-label {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.45rem;
}
.brief-title {
    font-size: clamp(1.2rem, 3vw, 1.6rem);
    font-weight: 800; color: #fff;
    letter-spacing: -0.02em;
    margin-bottom: 0.8rem;
    word-break: break-word;
}
.metric-pill-row { display: flex; gap: 8px; flex-wrap: wrap; }
.metric-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px;
    border-radius: var(--radius-full);
    font-size: 0.72rem; font-weight: 600;
    border: 1px solid;
}
.pill-accent { background: var(--accent-dim); color: var(--accent-glow); border-color: rgba(45, 212, 191, 0.3); }
.pill-sky    { background: var(--sky-dim);    color: var(--sky);         border-color: rgba(56, 189, 248, 0.3); }
.pill-lime   { background: var(--lime-dim);   color: var(--lime);        border-color: rgba(163, 230, 53, 0.3); }
.pill-gold   { background: var(--gold-dim);   color: var(--gold);        border-color: rgba(250, 204, 21, 0.3); }
.pill-coral  { background: var(--coral-dim);  color: var(--coral);       border-color: rgba(251, 113, 133, 0.3); }

/* ── Content cards ── */
.content-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.4rem;
    line-height: 1.75;
    font-size: 0.92rem;
    color: var(--text-primary);
    box-shadow: var(--shadow-glass);
    word-break: break-word;
}
.action-card {
    background: var(--bg-surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 0.6rem 1rem 0.85rem 1rem;
    margin-bottom: 0.6rem;
}
.action-meta { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; padding-left: 1.9rem; }
.decision-card {
    background: var(--bg-surface-2);
    border-left: 3px solid var(--gold);
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    font-size: 0.9rem; line-height: 1.6;
    color: var(--text-primary);
}
.question-card {
    background: var(--bg-surface-2);
    border-left: 3px solid var(--sky);
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    padding: 1rem 1.25rem;
    margin-bottom: 0.4rem;
    font-size: 0.9rem; line-height: 1.6;
    color: var(--text-primary);
}
.transcript-terminal {
    background: #070e10;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 1.25rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.8rem;
    line-height: 1.8;
    color: var(--text-secondary);
    max-height: 420px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── RAG chat studio ── */
.chat-studio-head {
    background: var(--bg-surface);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-lg);
    padding: 1.2rem 1.5rem;
    margin: 2rem 0 1rem 0;
    box-shadow: var(--shadow-glass);
}
.chat-studio-title { font-size: 1.1rem; font-weight: 800; color: #fff; margin-bottom: 0.2rem; }
.chat-studio-sub { font-size: 0.85rem; color: var(--text-secondary); }

.chat-bubble-user {
    background: var(--accent-dim);
    border: 1px solid rgba(45, 212, 191, 0.35);
    border-radius: 14px 14px 2px 14px;
    padding: 0.85rem 1.2rem;
    margin-left: auto;
    max-width: 80%;
    margin-bottom: 0.75rem;
    color: #fff; font-size: 0.9rem;
    word-break: break-word;
}
.chat-bubble-assistant {
    background: rgba(20, 36, 39, 0.9);
    border: 1px solid var(--border-subtle);
    border-radius: 14px 14px 14px 2px;
    padding: 0.95rem 1.3rem;
    margin-right: auto;
    max-width: 85%;
    margin-bottom: 0.75rem;
    color: var(--text-primary);
    font-size: 0.9rem; line-height: 1.65;
    word-break: break-word;
}

/* ── Buttons ── */
div.stButton > button,
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #14b8a6 0%, #0ea5e9 100%) !important;
    color: #041316 !important;
    font-weight: 700 !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    box-shadow: 0 4px 18px rgba(20, 184, 166, 0.35) !important;
    transition: all 0.25s cubic-bezier(.4,0,.2,1) !important;
    padding: 0.6rem 1.2rem !important;
}
div.stButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(20, 184, 166, 0.55) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
}
div.stButton > button:active,
div[data-testid="stFormSubmitButton"] > button:active,
div[data-testid="stDownloadButton"] > button:active { transform: scale(.97) !important; }

div.stButton > button::after,
div[data-testid="stFormSubmitButton"] > button::after,
div[data-testid="stDownloadButton"] > button::after {
    content: ''; position: absolute; inset: 0; pointer-events: none;
    background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,.28) 50%, transparent 70%);
    background-size: 200% 100%; background-position: -200% 0;
}
div.stButton > button:hover::after,
div[data-testid="stFormSubmitButton"] > button:hover::after,
div[data-testid="stDownloadButton"] > button:hover::after { animation: shimmer 1s ease; }

/* Secondary (reset / clear) buttons */
div[data-testid="stButton"] button[kind="secondary"],
div[data-testid="stFormSubmitButton"] button[kind="secondary"] {
    background: var(--bg-surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-secondary) !important;
    box-shadow: none !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="secondary"]:hover {
    border-color: var(--accent) !important;
    color: #fff !important;
}

[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }

/* ── Inputs ── */
.stTextInput > div > div > input {
    background: #070e10 !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: #fff !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 1rem !important;
    transition: box-shadow .25s, border-color .25s, transform .2s;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent-glow) !important;
    box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.2) !important;
    transform: translateY(-1px);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background: transparent !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    padding-bottom: 6px !important;
    overflow-x: auto;
}
.stTabs [data-baseweb="tab"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    padding: 8px 16px !important;
    white-space: nowrap;
}
.stTabs [aria-selected="true"] {
    background: var(--accent-dim) !important;
    border-color: var(--accent-glow) !important;
    color: #fff !important;
}

/* ── Motion & micro-interactions ── */
@keyframes fadeUp { from {opacity:0; transform:translateY(14px);} to {opacity:1; transform:none;} }
@keyframes shimmer { 0% {background-position:-200% 0;} 100% {background-position:200% 0;} }
@keyframes typingDot { 0%,80%,100% {transform:translateY(0); opacity:.35;} 40% {transform:translateY(-5px); opacity:1;} }
@keyframes sweep { 0% {left:-35%;} 100% {left:100%;} }
@keyframes msgIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.navbar, .hero-section, .engine-card, .brief-banner, .content-card, .chat-studio-head, .action-card {
    animation: fadeUp .6s cubic-bezier(.2,.7,.2,1) both;
}
.hero-section { animation-delay: .08s; }
.stTabs [data-baseweb="tab-panel"] { animation: fadeUp .4s ease both; }
.decision-card, .question-card { animation: fadeUp .45s ease both; }

.chat-bubble-user, .chat-bubble-assistant { animation: none; }
.chat-bubble-user.is-new, .chat-bubble-assistant.is-new { animation: msgIn .35s ease both; }

.typing-bubble {
    display: inline-flex; align-items: center; gap: 5px;
    padding: .85rem 1.1rem; margin-bottom: .75rem;
    border-radius: 14px 14px 14px 2px;
    background: rgba(20,36,39,.9); border: 1px solid var(--border-subtle);
}
.typing-bubble span {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent-glow); animation: typingDot 1.2s infinite;
}
.typing-bubble span:nth-child(2) { animation-delay: .15s; }
.typing-bubble span:nth-child(3) { animation-delay: .3s; }

.top-loader {
    position: fixed; top: 0; left: 0; right: 0; height: 3px;
    background: rgba(255,255,255,.04); z-index: 9999; overflow: hidden;
}
.top-loader::after {
    content: ''; position: absolute; top: 0; height: 100%; width: 35%;
    background: linear-gradient(90deg, transparent, var(--sky), var(--accent-glow), transparent);
    animation: sweep 1.2s linear infinite;
}
.progress-track {
    height: 6px; border-radius: 9999px; background: rgba(255,255,255,.07);
    overflow: hidden; max-width: 560px; margin: 0 auto .5rem auto;
}
.progress-fill {
    height: 100%; border-radius: 9999px;
    background: linear-gradient(90deg, var(--sky), var(--accent), var(--coral));
    background-size: 200% 100%; animation: shimmer 2s linear infinite;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: rgba(45,212,191,.35); border-radius: 9999px; }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.8rem 2rem 0.8rem !important; }
    .navbar { padding: 0.8rem 1rem; }
    .hero-section { padding: 1.5rem 1.15rem; }
    .hero-subtitle { font-size: 0.88rem; }
    .brief-banner { padding: 1.2rem 1.1rem; }
    .content-card { padding: 1.05rem; }
    .chat-studio-head { padding: 1rem 1.1rem; }
    .chat-bubble-user { max-width: 94%; }
    .chat-bubble-assistant { max-width: 96%; }
    .neural-pipeline-box { padding: 1.5rem 1rem; }
    .waveform-equalizer { gap: 4px; }
    .wave-bar { width: 4px; }
    .step-badge { font-size: 0.68rem; padding: 6px 11px; }
    .action-meta { padding-left: 0; }
    .stTabs [data-baseweb="tab"] { padding: 7px 12px !important; font-size: 0.78rem !important; }
}
@media (max-width: 480px) {
    .nav-status-pill { font-size: 0.68rem; }
    .brand-info h1 { font-size: 1rem !important; }
    .feature-tag { font-size: 0.68rem; padding: 4px 10px; }
}

@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── Initialize Session State ────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "pipeline_steps" not in st.session_state:
    st.session_state.pipeline_steps = {}
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""


def clear_action_checks():
    for k in [k for k in st.session_state.keys() if k.startswith("action_chk_")]:
        del st.session_state[k]


# ─── Top Navigation Bar ──────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <div class="nav-brand">
        <div class="brand-icon">⚡</div>
        <div class="brand-info">
            <h1>NEXUS VIDEO AI</h1>
            <p>MEETING &amp; VIDEO INTELLIGENCE PLATFORM</p>
        </div>
    </div>
    <div class="nav-status-pill">
        <div class="pulse-dot"></div>
        <span>Groq LPU (Llama 3.3 70B) • ONLINE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Hero Section ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="hero-badge">⚡ POWERED BY GROQ LPU™ &amp; WHISPER NEURAL SPEECH</div>
    <div class="hero-title">Turn Spoken Meetings Into Executable Wisdom</div>
    <div class="hero-subtitle">
        Ingest any YouTube URL or recorded meeting file. Our automated neural pipeline extracts 16kHz audio chunks,
        runs speech-to-text, drafts executive summaries via Groq LPU (500 tokens/sec), indexes decisions,
        and empowers you to converse with the recording via ChromaDB RAG.
    </div>
    <div class="hero-features-strip">
        <div class="feature-tag"><span>⚡</span> Ultra-Fast Groq Inference</div>
        <div class="feature-tag"><span>🎙️</span> Local Whisper STT</div>
        <div class="feature-tag"><span>🌐</span> Hindi &amp; Hinglish Support</div>
        <div class="feature-tag"><span>🗄️</span> ChromaDB Vector RAG</div>
        <div class="feature-tag"><span>📄</span> Executive PDF &amp; Markdown Report</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Ingestion & Engine Configuration Panel ──────────────────────────────────────
st.markdown('<div class="panel-header-badge">📥 INGESTION &amp; ENGINE CONFIGURATION</div>', unsafe_allow_html=True)

with st.form("ingest_form", clear_on_submit=False):
    ingest_tabs = st.tabs(["🔗 YouTube / Remote URL", "📁 Upload Local Audio / Video"])

    with ingest_tabs[0]:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        url_input_val = st.text_input(
            "YouTube or Video URL",
            placeholder="https://www.youtube.com/watch?v=... or remote MP4 link",
            label_visibility="collapsed",
            key="main_url_field",
        )
        st.markdown(
            "<div style='font-size:0.72rem;color:var(--text-muted);margin-top:4px;'>"
            "Paste the link and press <b>Enter</b> or click <b>Initialize Neural Analysis</b> below.</div>",
            unsafe_allow_html=True,
        )

    with ingest_tabs[1]:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload recording",
            type=["mp4", "mp3", "wav", "m4a", "mov", "mkv"],
            label_visibility="collapsed",
            key="file_uploader_field",
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    eng_col1, eng_col2, eng_col3 = st.columns([1.4, 1.4, 1.2])

    with eng_col1:
        st.markdown("""
        <div class="engine-card">
            <div style="font-size:0.7rem;font-weight:700;color:var(--sky);text-transform:uppercase;margin-bottom:4px;">
                🎙️ Speech-to-Text Engine
            </div>
            <div style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:8px;">
                Whisper (Local) or Sarvam Saaras
            </div>
        </div>
        """, unsafe_allow_html=True)
        language_choice = st.selectbox(
            "Language Engine",
            options=["english", "hinglish"],
            index=0,
            format_func=lambda x: "English (Whisper Neural STT • Free)" if x == "english" else "Hindi / Hinglish (Sarvam AI Direct • Translate)",
            label_visibility="collapsed",
            key="lang_select",
        )

    with eng_col2:
        st.markdown("""
        <div class="engine-card">
            <div style="font-size:0.7rem;font-weight:700;color:var(--gold);text-transform:uppercase;margin-bottom:4px;">
                ⚡ Reasoning &amp; Extraction
            </div>
            <div style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:8px;">
                Groq LPU Acceleration • Llama 3.3 70B
            </div>
            <div style="font-size:0.72rem;color:var(--lime);font-weight:600;">
                ● 500+ tok/s Ultra-Low Latency
            </div>
        </div>
        """, unsafe_allow_html=True)

    with eng_col3:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        start_analysis_btn = st.form_submit_button("⚡ Initialize Neural Analysis", use_container_width=True, type="primary")
        reset_app_btn = st.form_submit_button("🗑️ Reset Workspace", use_container_width=True)

if reset_app_btn:
    st.session_state.result = None
    st.session_state.chat_history = []
    st.session_state.is_processing = False
    st.session_state.pipeline_steps = {}
    st.session_state.pending_question = ""
    clear_action_checks()
    st.rerun()

# ─── Execution Logic with Live Waveform Visualizer ──────────────────────────────
if uploaded_file is not None:
    temp_dir = os.path.join(os.getcwd(), "dowonolades")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    target_source = temp_file_path
elif url_input_val and url_input_val.strip():
    target_source = url_input_val.strip()
else:
    target_source = ""

STEPS_ORDER = [
    ("audio",      "🔊 Audio Processing (16kHz Mono)"),
    ("transcript", "🎙️ Neural Transcription (Whisper/Sarvam)"),
    ("title",      "🏷️ Executive Title Synthesis"),
    ("summary",    "📋 Map-Reduce Summarization (Groq LPU)"),
    ("extract",    "🔍 Action Items & Decisions Matrix"),
    ("rag",        "🧠 ChromaDB Vector RAG Ingestion"),
]


def log_step(msg):
    print(f"[Nexus] {msg}", flush=True)


if start_analysis_btn:
    log_step(f"Analysis requested. Source: {target_source or 'EMPTY'} | Language: {language_choice}")
    if not target_source:
        st.error("⚠️ Please specify a YouTube URL, remote video link, or upload an audio/video file.")
    else:
        st.session_state.is_processing = True
        st.toast("Pipeline started", icon="⚡")
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pending_question = ""
        clear_action_checks()
        st.session_state.pipeline_steps = {k: "pending" for k, _ in STEPS_ORDER}

        visualizer_placeholder = st.empty()

        def update_visualizer(active_step_key, step_message):
            chips_html = ""
            for skey, slabel in STEPS_ORDER:
                status = st.session_state.pipeline_steps.get(skey, "pending")
                chip_class = "done" if status == "done" else "active" if status == "active" else ""
                icon = "✓ " if status == "done" else "⚡ " if status == "active" else "○ "
                chips_html += f'<div class="step-badge {chip_class}">{icon}{slabel}</div>'

            log_step(step_message)
            done_count = sum(1 for s in st.session_state.pipeline_steps.values() if s == "done")
            pct = int(done_count / len(STEPS_ORDER) * 100)
            waveform_bars_html = "".join(['<div class="wave-bar"></div>' for _ in range(16)])

            visualizer_placeholder.markdown(f"""
            <div class="top-loader"></div>
            <div class="neural-pipeline-box">
                <div style="font-size:0.75rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:var(--accent-glow);margin-bottom:0.4rem;">
                    NEURAL PROCESSING ENGINE IN PROGRESS
                </div>
                <div style="font-size:1.3rem;font-weight:800;color:#fff;margin-bottom:0.25rem;">
                    {step_message}
                </div>
                <div class="waveform-equalizer">
                    {waveform_bars_html}
                </div>
                <div class="progress-track"><div class="progress-fill" style="width:{max(pct, 6)}%"></div></div>
                <div style="font-size:0.72rem;color:var(--text-muted);font-weight:600;">{pct}% complete</div>
                <div class="step-chips-grid">
                    {chips_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        try:
            # 1 & 2. Ingest & Transcribe via local yt-dlp/pydub audio extraction & Whisper/Sarvam
            st.session_state.pipeline_steps["audio"] = "active"
            update_visualizer("audio", "Extracting 16kHz audio chunks from media stream…")
            chunks = process_input(target_source)
            st.session_state.pipeline_steps["audio"] = "done"

            st.session_state.pipeline_steps["transcript"] = "active"
            update_visualizer("transcript", f"Transcribing audio segments via {language_choice.title()} engine…")
            transcript = transcribe_all(chunks, language_choice)
            st.session_state.pipeline_steps["transcript"] = "done"

            # 3. Title
            st.session_state.pipeline_steps["title"] = "active"
            update_visualizer("title", "Synthesizing executive session title…")
            title = generate_title(transcript)
            st.session_state.pipeline_steps["title"] = "done"

            # 4. Summary
            st.session_state.pipeline_steps["summary"] = "active"
            update_visualizer("summary", "Drafting structured executive summary…")
            summary = get_summary(transcript)
            st.session_state.pipeline_steps["summary"] = "done"

            # 5. Extraction
            st.session_state.pipeline_steps["extract"] = "active"
            update_visualizer("extract", "Extracting action items, key decisions, and open questions…")
            raw_action_items = extract_action_items(transcript)
            raw_decisions = extract_key_decisions(transcript)
            raw_questions = extract_questions(transcript)
            st.session_state.pipeline_steps["extract"] = "done"

            # 6. RAG
            st.session_state.pipeline_steps["rag"] = "active"
            update_visualizer("rag", "Building ChromaDB vector embeddings and LCEL RAG chain…")
            rag_chain = build_rag_chain(transcript)
            st.session_state.pipeline_steps["rag"] = "done"

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": raw_action_items,
                "action_items_parsed": parse_action_items_structured(raw_action_items),
                "key_decisions": raw_decisions,
                "key_decisions_list": parse_key_decisions_list(raw_decisions),
                "open_questions": raw_questions,
                "open_questions_list": parse_open_questions_list(raw_questions),
                "rag_chain": rag_chain,
                "duration_str": f"~{max(1, len(transcript.split()) // 130)}m",
                "word_count": len(transcript.split()),
            }
            st.session_state.is_processing = False
            time.sleep(0.5)
            visualizer_placeholder.empty()
            st.rerun()

        except Exception as err:
            st.session_state.is_processing = False
            visualizer_placeholder.empty()
            log_step(f"Pipeline error: {err}")
            traceback.print_exc()
            st.error(f"❌ Pipeline Execution Error: {str(err)}")

# ─── Results Dashboard ───────────────────────────────────────────────────────────
if st.session_state.result:
    res = st.session_state.result
    word_count = res.get("word_count", len(res.get("transcript", "").split()))
    duration = res.get("duration_str", f"~{max(1, word_count // 130)}m")

    st.markdown(f"""
    <div class="brief-banner">
        <div class="brief-label">⚡ EXECUTIVE INTELLIGENCE BRIEF • GROQ ACCELERATED</div>
        <div class="brief-title">{html.escape(res.get('title', 'Session Intelligence Brief'))}</div>
        <div class="metric-pill-row">
            <span class="metric-pill pill-accent">✅ Analysed</span>
            <span class="metric-pill pill-sky">📝 {word_count:,} Words</span>
            <span class="metric-pill pill-gold">⏱️ {duration} Spoken</span>
            <span class="metric-pill pill-lime">🧠 RAG Engine Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    res_tabs = st.tabs([
        "Summary",
        "Action Items",
        "Key Decisions",
        "Open Questions",
        "Full Transcript",
        "Export Documents",
    ])

    # 1. Summary
    with res_tabs[0]:
        st.markdown("""
        <div class="panel-header-badge">📋 SYNTHESIZED EXECUTIVE SUMMARY</div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="content-card">
            {html.escape(res.get('summary', '')).replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # 2. Action Items
    with res_tabs[1]:
        st.markdown("""
        <div class="panel-header-badge" style="color:var(--lime);">✅ DESIGNATED ACTION ITEMS &amp; TASKS</div>
        """, unsafe_allow_html=True)

        parsed_items = res.get("action_items_parsed") or parse_action_items_structured(res.get("action_items", ""))
        if parsed_items:
            for idx, item in enumerate(parsed_items, 1):
                item_id = item.get("id", idx)
                task_text = str(item.get("task", ""))
                owner = str(item.get("owner", "Unassigned"))
                deadline = str(item.get("deadline", "Flexible"))
                priority = str(item.get("priority", "Medium"))

                p_class = "pill-coral" if priority.lower() == "high" else "pill-gold" if priority.lower() == "medium" else "pill-sky"
                chk_key = f"action_chk_{item_id}_{idx}"
                is_done = st.session_state.get(chk_key, False)
                label = f"~~{task_text}~~" if is_done else task_text

                with st.container():
                    st.checkbox(label, key=chk_key)
                    st.markdown(f"""
                    <div class="action-meta" style="margin-bottom:0.7rem;{'opacity:0.5;' if is_done else ''}">
                        <span class="metric-pill {p_class}" style="font-size:0.65rem;padding:2px 8px;">{html.escape(priority)}</span>
                        <span class="metric-pill pill-accent" style="font-size:0.65rem;padding:2px 8px;">👤 {html.escape(owner)}</span>
                        <span class="metric-pill pill-sky" style="font-size:0.65rem;padding:2px 8px;">📅 {html.escape(deadline)}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No explicit action items extracted for this session.")

    # 3. Key Decisions
    with res_tabs[2]:
        st.markdown("""
        <div class="panel-header-badge" style="color:var(--gold);">🔑 RATIFIED STRATEGIC DECISIONS</div>
        """, unsafe_allow_html=True)

        decisions_list = res.get("key_decisions_list") or parse_key_decisions_list(res.get("key_decisions", ""))
        if decisions_list:
            for idx, dec in enumerate(decisions_list, 1):
                st.markdown(f"""
                <div class="decision-card">
                    <strong>Decision #{idx}:</strong> {html.escape(str(dec))}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="content-card">
                {html.escape(res.get('key_decisions', 'No key decisions found.'))}
            </div>
            """, unsafe_allow_html=True)

    # 4. Open Questions
    with res_tabs[3]:
        st.markdown("""
        <div class="panel-header-badge" style="color:var(--sky);">❓ UNRESOLVED TOPICS &amp; OPEN QUESTIONS</div>
        """, unsafe_allow_html=True)

        questions_list = res.get("open_questions_list") or parse_open_questions_list(res.get("open_questions", ""))
        if questions_list:
            for q_idx, quest in enumerate(questions_list, 1):
                q_col1, q_col2 = st.columns([4, 1.2])
                with q_col1:
                    st.markdown(f"""
                    <div class="question-card">
                        <strong>Q{q_idx}:</strong> {html.escape(str(quest))}
                    </div>
                    """, unsafe_allow_html=True)
                with q_col2:
                    if st.button("💬 Ask Assistant ↓", key=f"ask_q_{q_idx}", use_container_width=True):
                        st.session_state.pending_question = str(quest)
                        st.rerun()
        else:
            st.info("No open questions identified.")

    # 5. Full Transcript
    with res_tabs[4]:
        st.markdown("""
        <div class="panel-header-badge" style="color:var(--text-muted);">📝 VERBATIM TRANSCRIPT</div>
        """, unsafe_allow_html=True)

        transcript_text = res.get("transcript", "")
        search_kw = st.text_input(
            "Search transcript",
            placeholder="🔍 Filter by speaker or keyword…",
            label_visibility="collapsed",
            key="tr_search",
        )
        if search_kw.strip():
            matching_lines = [line for line in transcript_text.split("\n") if search_kw.lower() in line.lower()]
            display_text = "\n".join(matching_lines) if matching_lines else f"No matches found for '{search_kw}'"
        else:
            display_text = transcript_text

        st.markdown(f"""
        <div class="transcript-terminal">
            {html.escape(display_text)}
        </div>
        """, unsafe_allow_html=True)

    # 6. Export Documents
    with res_tabs[5]:
        st.markdown("""
        <div class="panel-header-badge">📥 REPORT GENERATOR</div>
        """, unsafe_allow_html=True)

        stamp = datetime.now().strftime('%Y%m%d')
        exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)

        with exp_col1:
            try:
                pdf_bytes = generate_pdf(res)
                if pdf_bytes:
                    st.download_button(
                        label="📄 Executive PDF",
                        data=pdf_bytes,
                        file_name=f"nexus_report_{stamp}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.button("📄 PDF (Install fpdf2)", disabled=True, use_container_width=True)
            except Exception:
                st.button("📄 PDF Unavailable", disabled=True, use_container_width=True)

        with exp_col2:
            st.download_button(
                label="📝 Markdown (.md)",
                data=generate_markdown(res),
                file_name=f"nexus_brief_{stamp}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with exp_col3:
            txt_content = (
                f"{res.get('title','')}\n\nSUMMARY:\n{res.get('summary','')}"
                f"\n\nACTION ITEMS:\n{res.get('action_items','')}"
                f"\n\nDECISIONS:\n{res.get('key_decisions','')}"
            )
            st.download_button(
                label="📋 Text Summary",
                data=txt_content,
                file_name=f"nexus_summary_{stamp}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with exp_col4:
            json_payload = {
                "title": res.get("title", ""),
                "summary": res.get("summary", ""),
                "action_items": res.get("action_items", ""),
                "key_decisions": res.get("key_decisions", ""),
                "open_questions": res.get("open_questions", ""),
                "word_count": word_count,
                "exported_at": datetime.now().isoformat(),
            }
            st.download_button(
                label="📦 JSON Payload",
                data=json.dumps(json_payload, indent=2),
                file_name=f"nexus_data_{stamp}.json",
                mime="application/json",
                use_container_width=True,
            )

    # ── Conversational RAG Studio (very bottom) ──────────────────────────────────
    st.markdown("""
    <div class="chat-studio-head">
        <div class="chat-studio-title">💬 Interrogate Transcript with AI</div>
        <div class="chat-studio-sub">Ask specific questions grounded strictly in the session recording.</div>
    </div>
    """, unsafe_allow_html=True)

    # Chat history
    if st.session_state.chat_history:
        last_idx = len(st.session_state.chat_history) - 1
        for i, msg in enumerate(st.session_state.chat_history):
            new_cls = " is-new" if i >= last_idx - 1 else ""
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-bubble-user{new_cls}">
                    <div style="font-size:0.65rem;color:var(--accent-glow);font-weight:700;margin-bottom:2px;">YOU</div>
                    {html.escape(msg["content"])}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-bubble-assistant{new_cls}">
                    <div style="font-size:0.65rem;color:var(--sky);font-weight:700;margin-bottom:2px;">⚡ NEXUS INTELLIGENCE</div>
                    {html.escape(msg["content"]).replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

    # Chat input (Enter key submits the form)
    with st.form("chat_form", clear_on_submit=True):
        chat_col1, chat_col2 = st.columns([5, 1])
        with chat_col1:
            user_query = st.text_input(
                "Ask question about meeting",
                placeholder="Ask anything grounded strictly in the meeting transcript…",
                label_visibility="collapsed",
                key="chat_query_field",
            )
        with chat_col2:
            send_query_btn = st.form_submit_button("Send →", use_container_width=True)

    q_text = (user_query.strip() if send_query_btn else "") or st.session_state.pending_question.strip()
    if q_text:
        st.session_state.pending_question = ""
        typing_slot = st.empty()
        typing_slot.markdown(f"""
        <div class="chat-bubble-user is-new">
            <div style="font-size:0.65rem;color:var(--accent-glow);font-weight:700;margin-bottom:2px;">YOU</div>
            {html.escape(q_text)}
        </div>
        <div class="typing-bubble"><span></span><span></span><span></span></div>
        """, unsafe_allow_html=True)

        try:
            answer = ask_question(res["rag_chain"], q_text)
        except Exception as err:
            traceback.print_exc()
            answer = f"⚠️ Could not get an answer: {err}"

        st.session_state.chat_history.append({"role": "user", "content": q_text})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
            st.session_state.chat_history = []
            st.rerun()

# ─── Empty State ─────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="background:var(--bg-surface);border:1px solid var(--border-subtle);border-radius:var(--radius-xl);padding:3rem 1.5rem;text-align:center;box-shadow:var(--shadow-glass);margin-top:1.5rem;">
        <div style="width:72px;height:72px;border-radius:20px;background:var(--accent-dim);border:1px solid rgba(45,212,191,0.3);display:flex;align-items:center;justify-content:center;font-size:2rem;margin:0 auto 1.25rem auto;box-shadow:0 0 25px rgba(45,212,191,0.3);">
            🎬
        </div>
        <div style="font-size:1.3rem;font-weight:800;color:#fff;margin-bottom:0.4rem;">
            Ready to Analyze Video &amp; Meeting Audio
        </div>
        <div style="font-size:0.86rem;color:var(--text-secondary);max-width:480px;margin:0 auto 2rem auto;line-height:1.6;">
            Paste a YouTube link or upload a recording above, then click <strong>Initialize Neural Analysis</strong> to generate your executive dashboard and interactive RAG chat.
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:1rem;max-width:750px;margin:0 auto;text-align:left;">
            <div style="background:var(--bg-surface-2);border:1px solid var(--border-subtle);border-radius:12px;padding:1.1rem;">
                <div style="font-size:1.25rem;margin-bottom:6px;">🎙️</div>
                <div style="font-weight:700;font-size:0.82rem;color:#fff;margin-bottom:2px;">Whisper &amp; Sarvam STT</div>
                <div style="font-size:0.72rem;color:var(--text-muted);line-height:1.4;">Automatic 16kHz chunking for English &amp; Hinglish speech.</div>
            </div>
            <div style="background:var(--bg-surface-2);border:1px solid var(--border-subtle);border-radius:12px;padding:1.1rem;">
                <div style="font-size:1.25rem;margin-bottom:6px;">⚡</div>
                <div style="font-weight:700;font-size:0.82rem;color:#fff;margin-bottom:2px;">Groq LPU Llama 3.3 70B</div>
                <div style="font-size:0.72rem;color:var(--text-muted);line-height:1.4;">Near-instant 500+ tok/s map-reduce executive synthesis.</div>
            </div>
            <div style="background:var(--bg-surface-2);border:1px solid var(--border-subtle);border-radius:12px;padding:1.1rem;">
                <div style="font-size:1.25rem;margin-bottom:6px;">🧠</div>
                <div style="font-weight:700;font-size:0.82rem;color:#fff;margin-bottom:2px;">ChromaDB Neural RAG</div>
                <div style="font-size:0.72rem;color:var(--text-muted);line-height:1.4;">Dense semantic vector retrieval for conversational Q&amp;A.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
