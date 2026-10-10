"""
ResearchFlow AI - Streamlit front end for the multi-agent research pipeline.

The AI logic stays in agents.py / pipeline.py. This file only handles the UI:
it calls run_research_pipeline(topic, on_stage=...) and renders real progress.
"""
import html
import inspect
import json
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(
    page_title="ResearchFlow AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()

# --------------------------------------------------------------------------
# Configuration  (EDIT REQUIRED_ENV_KEYS to match the keys your agents.py uses)
# --------------------------------------------------------------------------
REQUIRED_ENV_KEYS = ["GROQ_API_KEY", "TAVILY_API_KEY"]
HISTORY_DIR = Path(__file__).resolve().parent / "history"
MAX_PREVIEW_CHARS = 6000

SUGGESTED_TOPICS = [
    "Impact of War on Stock Markets",
    "Applications of Vision-Language Models in Medical Imaging",
    "Future of Generative AI",
    "AI in Cybersecurity",
    "Renewable Energy Trends",
]

STAGES = [
    {"key": "search", "name": "Search Agent", "icon": "🔍", "desc": "Finds recent, reliable sources"},
    {"key": "reader", "name": "Reader Agent", "icon": "📖", "desc": "Scrapes the most relevant URL"},
    {"key": "writer", "name": "Writer Chain", "icon": "✍️", "desc": "Drafts a structured report"},
    {"key": "critic", "name": "Critic Chain", "icon": "🧐", "desc": "Reviews quality and completeness"},
]
STAGE_NAME = {s["key"]: s["name"] for s in STAGES}
STATE_FIELD = {
    "search": "search_results",
    "reader": "scraped_content",
    "writer": "report",
    "critic": "feedback",
}
NAV = [
    ("dashboard", "🏠  Dashboard"),
    ("workspace", "🧪  Research Workspace"),
    ("history", "🗂️  Research History"),
    ("about", "ℹ️  About Project"),
]

# Make Streamlit Cloud secrets available as environment variables.
try:
    for _k in REQUIRED_ENV_KEYS:
        if not os.getenv(_k) and _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, .stApp, [data-testid="stMarkdownContainer"] { font-family: 'Inter', sans-serif; }
.stApp {
  color: #E5E7EB;
  background:
    radial-gradient(900px 520px at 88% -8%, rgba(139,92,246,.30), transparent 60%),
    radial-gradient(700px 520px at -8% 22%, rgba(34,211,238,.14), transparent 60%),
    radial-gradient(800px 500px at 60% 110%, rgba(236,72,153,.12), transparent 60%),
    #0B1020;
  background-attachment: fixed;
}
[data-testid="stMarkdownContainer"] { color: #E5E7EB; }
[data-testid="stMain"] a { color: #67E8F9; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1150px; }
header[data-testid="stHeader"] { background: transparent; }
header[data-testid="stHeader"] * { color: #CBD5E1 !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] { color: #C7D2FE !important; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] * { color: #C7D2FE !important; }
hr { border-color: rgba(255,255,255,.1) !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0A0E1F 0%, #160F33 100%);
  border-right: 1px solid rgba(255,255,255,.07); }
section[data-testid="stSidebar"] * { color: #E2E8F0; }
.brand { display:flex; align-items:center; gap:.7rem; margin: .4rem 0 1.2rem 0; }
.brand-logo { width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center;
  font-size:1.3rem; background: linear-gradient(135deg,#6366F1,#A855F7 55%,#EC4899); box-shadow:0 6px 20px rgba(168,85,247,.5); }
.brand-name { font-weight:700; font-size:1.12rem; color:#fff !important; line-height:1.1; }
.brand-tag { font-size:.74rem; color:#67E8F9 !important; }
.nav-label { font-size:.68rem; letter-spacing:.12em; color:#7C879E !important; margin:1.2rem 0 .4rem .3rem; }
section[data-testid="stSidebar"] .stButton > button { width:100%; justify-content:flex-start; background:transparent;
  border:1px solid transparent; color:#CBD5E1; border-radius:10px; font-weight:500; text-align:left; }
section[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.12); }
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
  background: rgba(139,92,246,.22); border: 1px solid rgba(167,139,250,.45); color:#fff; }
section[data-testid="stSidebar"] .st-key-newbtn button { background: linear-gradient(135deg,#6366F1,#A855F7 60%,#EC4899) !important;
  color:#fff !important; border:none !important; justify-content:center; font-weight:600; box-shadow:0 8px 22px rgba(168,85,247,.4); }
.sys-status { display:flex; align-items:center; gap:.5rem; font-size:.8rem; padding:.55rem .75rem; border-radius:10px;
  background: rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.08); margin-top:1.2rem; }
.dot { width:9px; height:9px; border-radius:50%; display:inline-block; }
.dot.ok { background:#34D399; box-shadow:0 0 8px #34D399; }
.dot.warn { background:#FBBF24; box-shadow:0 0 8px #FBBF24; }
.dot.busy { background:#22D3EE; box-shadow:0 0 8px #22D3EE; }
.side-foot { font-size:.72rem; color:#7C879E !important; margin-top:1.5rem; line-height:1.5; }

/* Hero + cards */
.hero { background: linear-gradient(135deg,#4F46E5 0%,#7C3AED 48%,#DB2777 100%); border-radius:22px; padding:2.5rem 2.4rem;
  box-shadow:0 20px 50px rgba(124,58,237,.35); border:1px solid rgba(255,255,255,.18); margin-bottom:1.4rem; }
.hero-eyebrow { font-size:.72rem; letter-spacing:.14em; color:#A5F3FC; font-weight:700; margin-bottom:.5rem; }
.hero h1 { color:#fff !important; font-size:2rem !important; font-weight:700 !important; margin:0 0 .6rem 0 !important; padding:0 !important; }
.hero p { color:#F5F3FF !important; font-size:1rem; max-width:680px; margin:0; line-height:1.55; }
.card { background: rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.1); border-radius:16px; padding:1.1rem 1.4rem;
  box-shadow:0 10px 30px rgba(0,0,0,.25); backdrop-filter: blur(8px); color:#E5E7EB; }
.card h3 { margin:0 0 .4rem 0; font-size:1.05rem; color:#fff; }
.card p, .card li { color:#B6C0D4; font-size:.93rem; line-height:1.6; }
.card b { color:#E9D5FF; }
.section-title { font-size:1.05rem; font-weight:600; color:#F1F5F9; margin:1.6rem 0 .7rem 0; }
.muted { color:#94A3B8; font-size:.85rem; }

/* Inputs + buttons (main area) */
[data-testid="stForm"] { border:none !important; padding:0 !important; background:transparent; }
.stTextInput [data-baseweb="input"], .stTextInput [data-baseweb="base-input"] { background:#111731 !important; border-radius:14px !important; }
.stTextInput [data-baseweb="input"] { border:1px solid rgba(255,255,255,.18) !important; }
.stTextInput [data-baseweb="input"]:focus-within { border-color:#A78BFA !important; box-shadow:0 0 0 3px rgba(139,92,246,.30) !important; }
.stTextInput input { font-size:1.05rem; padding:.95rem 1.05rem; background:transparent !important; color:#F8FAFC !important;
  -webkit-text-fill-color:#F8FAFC !important; caret-color:#22D3EE; }
.stTextInput input::placeholder { color:#7C879E !important; -webkit-text-fill-color:#7C879E !important; opacity:1; }
.stApp [data-testid="stMain"] button[kind="secondary"], .stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondary"] {
  background: rgba(255,255,255,.06); color:#E5E7EB; border:1px solid rgba(255,255,255,.16); border-radius:12px; }
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondary"]:hover { background: rgba(255,255,255,.12); border-color:#A78BFA; color:#fff; }
.stApp [data-testid="stMain"] .stButton > button[kind="primary"],
.stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] button[kind="primary"],
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primary"],
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: linear-gradient(135deg,#6366F1,#A855F7 60%,#EC4899); border:none; color:#fff; border-radius:12px; font-weight:600;
  padding:.55rem 1.4rem; box-shadow:0 8px 22px rgba(168,85,247,.35); }
.st-key-chips .stButton > button { border-radius:999px; font-size:.84rem; background:rgba(139,92,246,.14) !important;
  color:#DDD6FE !important; border:1px solid rgba(167,139,250,.38) !important; }
.st-key-chips .stButton > button:hover { background:rgba(139,92,246,.30) !important; border-color:#C4B5FD !important; color:#fff !important; }

/* Tabs, expanders, bordered containers */
.stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid rgba(255,255,255,.1); }
.stTabs [data-baseweb="tab"] { color:#94A3B8; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color:#fff; }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg,#8B5CF6,#22D3EE); }
.stTabs [data-baseweb="tab-border"] { background: transparent; }
[data-testid="stExpander"] details { background: rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.1); border-radius:14px; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color:#E5E7EB !important; }
.stApp [data-testid="stVerticalBlockBorderWrapper"] { border-color: rgba(255,255,255,.1) !important; border-radius:14px; background: rgba(255,255,255,.03); }
[data-testid="stCaptionContainer"] { color:#94A3B8; }

/* Workflow tracker */
.workflow { display:flex; align-items:stretch; gap:.6rem; margin:.4rem 0 1rem 0; }
.workflow .arrow { display:flex; align-items:center; color:#8B5CF6; font-size:1.3rem; }
.stage { flex:1; background: rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.1); border-radius:16px; padding:1rem .8rem;
  text-align:center; transition:all .3s ease; box-shadow:0 8px 24px rgba(0,0,0,.22); }
.stage-icon { font-size:1.6rem; margin-bottom:.2rem; }
.stage-name { font-weight:600; color:#F8FAFC; font-size:.95rem; }
.stage-desc { color:#94A3B8; font-size:.78rem; margin:.15rem 0 .5rem 0; }
.stage-status { display:inline-flex; align-items:center; gap:.4rem; font-size:.78rem; font-weight:600; border-radius:999px; padding:.2rem .65rem;
  background: rgba(255,255,255,.08); color:#CBD5E1; }
.stage.running { border-color:#22D3EE; box-shadow:0 0 0 4px rgba(34,211,238,.12), 0 0 28px rgba(34,211,238,.25); }
.stage.running .stage-status { background: rgba(34,211,238,.16); color:#67E8F9; }
.stage.completed { border-color: rgba(52,211,153,.6); background: rgba(16,185,129,.09); }
.stage.completed .stage-status { background: rgba(16,185,129,.2); color:#6EE7B7; }
.stage.failed { border-color: rgba(248,113,113,.7); background: rgba(239,68,68,.09); }
.stage.failed .stage-status { background: rgba(239,68,68,.2); color:#FCA5A5; }
.spinner { width:11px; height:11px; border:2px solid rgba(34,211,238,.3); border-top-color:#22D3EE; border-radius:50%; display:inline-block; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Workspace header */
.ws-head { background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); border-radius:16px; padding:1rem 1.4rem;
  box-shadow:0 10px 30px rgba(0,0,0,.25); }
.ws-topic { font-size:1.25rem; font-weight:700; color:#fff; margin-bottom:.4rem; }
.ws-meta { display:flex; flex-wrap:wrap; gap:1.1rem; color:#94A3B8; font-size:.85rem; align-items:center; }
.badge { padding:.18rem .65rem; border-radius:999px; font-weight:600; font-size:.78rem; }
.badge.running { background:rgba(34,211,238,.16); color:#67E8F9; } .badge.completed { background:rgba(16,185,129,.2); color:#6EE7B7; }
.badge.failed { background:rgba(239,68,68,.2); color:#FCA5A5; } .badge.interrupted { background:rgba(251,191,36,.18); color:#FCD34D; }

@media (max-width: 900px) {
  .workflow { flex-direction:column; }
  .workflow .arrow { justify-content:center; transform:rotate(90deg); }
  .hero { padding:1.6rem 1.3rem; } .hero h1 { font-size:1.55rem !important; }
}
"""
st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def missing_keys():
    return [k for k in REQUIRED_ENV_KEYS if not os.getenv(k, "").strip()]


def redact(text: str) -> str:
    """Strip any secret values from text before it is shown."""
    for name, value in os.environ.items():
        if value and len(value) >= 8 and any(t in name.upper() for t in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            text = text.replace(value, "[redacted]")
    return text


def to_text(value) -> str:
    """Normalise whatever a chain/agent returned into plain text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    content = getattr(value, "content", None)
    if content is not None:
        return to_text(content)
    if isinstance(value, list):
        return "\n".join(to_text(v.get("text") if isinstance(v, dict) else v) for v in value).strip()
    return str(value)


def extract_urls(text: str):
    """Pull http(s) URLs out of text. Only checks URL structure; it does not visit the links."""
    seen, urls = set(), []
    for raw in re.findall(r"https?://[^\s<>\"'\)\]\[]+", text or ""):
        url = raw.rstrip(".,;:!?*`")
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and "." in parsed.netloc and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def fmt_duration(seconds) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "research"


def clip(text: str):
    if len(text) <= MAX_PREVIEW_CHARS:
        return text, False
    return text[:MAX_PREVIEW_CHARS], True


# --------------------------------------------------------------------------
# History (JSON files in ./history)
# --------------------------------------------------------------------------
def _valid_id(rec_id: Optional[str]) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", rec_id or ""))


def save_record(rec) -> bool:
    try:
        HISTORY_DIR.mkdir(exist_ok=True)
        payload = {k: rec[k] for k in ("id", "topic", "started_at", "duration", "state")}
        tmp = HISTORY_DIR / f"{rec['id']}.json.tmp"
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(HISTORY_DIR / f"{rec['id']}.json")
        return True
    except OSError:
        return False


def list_history():
    items = []
    if HISTORY_DIR.exists():
        for path in HISTORY_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if _valid_id(data.get("id", "")) and "state" in data:
                    items.append(data)
            except (OSError, ValueError, AttributeError):
                continue
    return sorted(items, key=lambda d: d.get("started_at", ""), reverse=True)


def record_from_saved(data) -> dict:
    state = {f: to_text(data["state"].get(f)) for f in STATE_FIELD.values()}
    return {
        "id": data["id"],
        "topic": data["topic"],
        "started_at": data.get("started_at", ""),
        "started_ts": None,
        "duration": data.get("duration"),
        "status": "completed",
        "error": None,
        "stage_status": {s["key"]: "completed" for s in STAGES},
        "stage_output": {k: state[f] for k, f in STATE_FIELD.items()},
        "state": state,
    }


def new_record(topic: str) -> dict:
    now = datetime.now()
    return {
        "id": f"{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}",
        "topic": topic,
        "started_at": now.isoformat(timespec="seconds"),
        "started_ts": time.time(),
        "duration": None,
        "status": "running",
        "error": None,
        "stage_status": {s["key"]: "pending" for s in STAGES},
        "stage_output": {},
        "state": None,
    }


# --------------------------------------------------------------------------
# Navigation callbacks
# --------------------------------------------------------------------------
def goto(page: str):
    st.session_state.page = page


def go_new():
    st.session_state.page = "dashboard"
    st.session_state.pop("topic_input", None)


def set_topic(topic: str):
    st.session_state.topic_input = topic


def open_record(rec_id: str):
    if not _valid_id(rec_id):
        return
    try:
        data = json.loads((HISTORY_DIR / f"{rec_id}.json").read_text(encoding="utf-8"))
        st.session_state.current = record_from_saved(data)
        st.session_state.pending_topic = None
        st.session_state.page = "workspace"
    except (OSError, ValueError, KeyError, AttributeError):
        st.session_state.history_error = "That saved research could not be opened."


def delete_record(rec_id: str):
    if _valid_id(rec_id):
        try:
            (HISTORY_DIR / f"{rec_id}.json").unlink(missing_ok=True)
        except OSError:
            st.session_state.history_error = "That saved research could not be deleted."


# --------------------------------------------------------------------------
# HTML builders (only static strings and html-escaped user text go in here)
# --------------------------------------------------------------------------
def tracker_html(statuses: dict, show_status: bool = True) -> str:
    labels = {"pending": "Pending", "running": "Running", "completed": "Completed", "failed": "Failed"}
    marks = {"pending": "•", "completed": "✓", "failed": "✕"}
    cards = []
    for i, s in enumerate(STAGES, start=1):
        status = statuses.get(s["key"], "pending")
        if show_status:
            ind = '<span class="spinner"></span>' if status == "running" else marks[status]
            tail = f'<div class="stage-status">{ind} {labels[status]}</div>'
            cls = status
        else:
            tail = f'<div class="stage-status">Step {i}</div>'
            cls = "pending"
        cards.append(
            f'<div class="stage {cls}"><div class="stage-icon">{s["icon"]}</div>'
            f'<div class="stage-name">{s["name"]}</div><div class="stage-desc">{s["desc"]}</div>{tail}</div>'
        )
    return '<div class="workflow">' + '<div class="arrow">→</div>'.join(cards) + "</div>"


def header_html(rec: dict) -> str:
    status = rec["status"]
    label = {"running": "Running", "completed": "Completed", "failed": "Failed", "interrupted": "Interrupted"}[status]
    try:
        started = datetime.fromisoformat(rec["started_at"]).strftime("%d %b %Y, %H:%M:%S")
    except (ValueError, TypeError):
        started = "—"
    if rec.get("duration") is not None:
        elapsed = fmt_duration(rec["duration"])
    elif rec.get("started_ts"):
        elapsed = fmt_duration(time.time() - rec["started_ts"])
    else:
        elapsed = "—"
    return (
        '<div class="ws-head">'
        f'<div class="ws-topic">{html.escape(rec["topic"])}</div>'
        '<div class="ws-meta">'
        f'<span class="badge {status}">{label}</span>'
        f"<span>🕒 Started {started}</span><span>⏱ Elapsed {elapsed}</span>"
        "</div></div>"
    )


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
def render_sidebar():
    ss = st.session_state
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-logo">🔬</div><div>'
            '<div class="brand-name">ResearchFlow AI</div>'
            '<div class="brand-tag">Multi-Agent Research Workspace</div></div></div>',
            unsafe_allow_html=True,
        )
        with st.container(key="newbtn"):
            st.button("＋  New Research", on_click=go_new, use_container_width=True, key="side_new")

        st.markdown('<div class="nav-label">NAVIGATION</div>', unsafe_allow_html=True)
        for key, label in NAV:
            st.button(
                label,
                key=f"nav_{key}",
                on_click=goto,
                args=(key,),
                type="primary" if ss.page == key else "secondary",
                use_container_width=True,
            )

        if ss.running:
            dot, text = "busy", "Research in progress"
        elif missing_keys():
            dot, text = "warn", "Setup needed: API keys missing"
        else:
            dot, text = "ok", "System ready"
        st.markdown(f'<div class="sys-status"><span class="dot {dot}"></span>{text}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="side-foot">Built with<br>Python · Streamlit · LangChain</div>',
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def page_dashboard():
    ss = st.session_state
    st.markdown(
        '<div class="hero"><div class="hero-eyebrow">MULTI-AGENT RESEARCH</div>'
        "<h1>Turn Any Topic Into Actionable Research</h1>"
        "<p>Enter a topic and a team of AI agents will search the web, read the best source, "
        "write a structured report, and critique it, all in one workflow.</p></div>",
        unsafe_allow_html=True,
    )

    missing = missing_keys()
    if missing:
        st.warning(
            "Missing environment variables: " + ", ".join(f"`{k}`" for k in missing)
            + ". Add them to your `.env` file (or Streamlit secrets) and restart the app."
        )

    with st.form("research_form", border=False):
        topic = st.text_input(
            "Research topic",
            key="topic_input",
            placeholder="e.g. How will AI change drug discovery over the next decade?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("🚀  Start Research", type="primary", disabled=ss.running)

    if submitted:
        if not topic.strip():
            st.error("Please enter a research topic first.")
        elif missing:
            st.error("Cannot start: some required API keys are not configured.")
        elif not ss.running:
            ss.pending_topic = topic.strip()
            ss.page = "workspace"
            st.rerun()

    st.markdown('<div class="section-title">Try a suggested topic</div>', unsafe_allow_html=True)
    with st.container(key="chips"):
        for row_start in range(0, len(SUGGESTED_TOPICS), 3):
            row = SUGGESTED_TOPICS[row_start:row_start + 3]
            cols = st.columns(3)
            for col, t in zip(cols, row):
                col.button(t, key=f"chip_{t}", on_click=set_topic, args=(t,), use_container_width=True)

    st.markdown('<div class="section-title">The research pipeline</div>', unsafe_allow_html=True)
    st.markdown(tracker_html({}, show_status=False), unsafe_allow_html=True)

    st.markdown(
        '<div class="card"><h3>How it works</h3><ol>'
        "<li><b>Search Agent</b> looks up recent, reliable information about your topic.</li>"
        "<li><b>Reader Agent</b> picks the most relevant URL and extracts deeper content.</li>"
        "<li><b>Writer Chain</b> combines both into a structured research report.</li>"
        "<li><b>Critic Chain</b> reviews the report and suggests improvements.</li>"
        "</ol></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Workspace
# --------------------------------------------------------------------------
class RunView:
    """Placeholders for the workspace so they can be redrawn as stages finish."""

    def __init__(self):
        left, right = st.columns([4, 1], vertical_alignment="center")
        self.header = left.empty()
        right.button("＋  New research", on_click=go_new, key="ws_new", use_container_width=True)
        self.error = st.empty()
        self.tracker = st.empty()
        self.results = st.empty()
        st.markdown('<div class="section-title">Agent outputs</div>', unsafe_allow_html=True)
        self.outputs = {s["key"]: st.empty() for s in STAGES}

    def refresh(self, rec: dict):
        self.header.markdown(header_html(rec), unsafe_allow_html=True)
        self.tracker.markdown(tracker_html(rec["stage_status"]), unsafe_allow_html=True)
        if rec.get("error"):
            self.error.error(rec["error"])
        else:
            self.error.empty()
        for s in STAGES:
            text = rec["stage_output"].get(s["key"])
            if text:
                preview, truncated = clip(text)
                with self.outputs[s["key"]].container():
                    with st.expander(f'{s["icon"]} {s["name"]} output'):
                        st.markdown(preview)
                        if truncated:
                            st.caption("Preview truncated. See the results tabs for the full text.")


def run_stages_directly(topic: str, on_stage) -> dict:
    """Same four steps as pipeline.py, used only when pipeline.py has no on_stage callback.

    This lets the UI show live progress with your original, unmodified pipeline.py.
    """
    from agents import build_reader_agent, build_search_agent, critic_chain, writer_chain

    state, stage = {}, None
    try:
        stage = "search"
        on_stage(stage, "running", None)
        result = build_search_agent().invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        state["search_results"] = result["messages"][-1].content
        on_stage(stage, "completed", state["search_results"])

        stage = "reader"
        on_stage(stage, "running", None)
        result = build_reader_agent().invoke({
            "messages": [(
                "user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{to_text(state['search_results'])[:800]}",
            )]
        })
        state["scraped_content"] = result["messages"][-1].content
        on_stage(stage, "completed", state["scraped_content"])

        stage = "writer"
        on_stage(stage, "running", None)
        research_combined = (
            f"SEARCH RESULTS : \n {state['search_results']} \n\n"
            f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})
        on_stage(stage, "completed", state["report"])

        stage = "critic"
        on_stage(stage, "running", None)
        state["feedback"] = critic_chain.invoke({"report": state["report"]})
        on_stage(stage, "completed", state["feedback"])
    except Exception as exc:
        if stage:
            on_stage(stage, "failed", f"{type(exc).__name__}: {exc}")
        raise
    return state


def execute_research(topic: str):
    ss = st.session_state
    if ss.running:
        return
    ss.running = True
    rec = new_record(topic)
    ss.current = rec
    view = RunView()
    view.refresh(rec)

    def on_stage(stage, status, payload):
        if stage not in rec["stage_status"]:
            return
        rec["stage_status"][stage] = status
        if status == "completed" and payload is not None:
            rec["stage_output"][stage] = to_text(payload)
        elif status == "failed":
            rec["error"] = redact(f"{STAGE_NAME[stage]} failed: {payload}")
        view.refresh(rec)

    try:
        from pipeline import run_research_pipeline  # lazy import so config errors show in the UI

        if "on_stage" in inspect.signature(run_research_pipeline).parameters:
            result = run_research_pipeline(topic, on_stage=on_stage)
        else:  # original pipeline.py without the callback
            result = run_stages_directly(topic, on_stage)
        rec["state"] = {f: to_text(result.get(f)) for f in STATE_FIELD.values()}
        for key, field in STATE_FIELD.items():
            rec["stage_output"][key] = rec["state"][field]
        rec["status"] = "completed"
    except Exception as exc:  # noqa: BLE001 - surface any agent/network/config failure to the user
        rec["status"] = "failed"
        if not rec["error"]:
            rec["error"] = redact(f"{type(exc).__name__}: {exc}")
    finally:
        rec["duration"] = time.time() - rec["started_ts"]
        ss.running = False
        if rec["status"] == "running":  # script was interrupted (e.g. user navigated away)
            rec["status"] = "interrupted"

    saved = rec["status"] == "completed" and save_record(rec)
    view.refresh(rec)
    if rec["status"] == "completed":
        with view.results.container():
            render_results(rec)
        if not saved:
            st.warning("Research finished, but it could not be saved to history (disk not writable).")


def page_workspace():
    ss = st.session_state
    if ss.pending_topic and not ss.running:
        topic, ss.pending_topic = ss.pending_topic, None
        execute_research(topic)
        return

    rec = ss.current
    if not rec:
        st.markdown(
            '<div class="card"><h3>No research yet</h3><p>Start a new research task from the dashboard '
            "or reopen one from Research History.</p></div>",
            unsafe_allow_html=True,
        )
        st.button("Go to dashboard", on_click=go_new, key="empty_go")
        return

    view = RunView()
    view.refresh(rec)
    if rec["status"] == "completed":
        with view.results.container():
            render_results(rec)
    elif rec["status"] == "interrupted":
        st.info("This run was interrupted before it finished. Start a new research task to try again.")


def render_results(rec: dict):
    state = rec.get("state") or {}
    report = state.get("report", "")
    search = state.get("search_results", "")
    scraped = state.get("scraped_content", "")
    feedback = state.get("feedback", "")

    st.markdown('<div class="section-title">Results</div>', unsafe_allow_html=True)
    tab_report, tab_search, tab_scraped, tab_critic = st.tabs(
        ["📝 Final Report", "🔍 Search Results", "📖 Extracted Research", "🧐 Critic Review"]
    )

    with tab_report:
        if not report.strip():
            st.info("The Writer Chain returned an empty report.")
        else:
            st.markdown(report)  # raw HTML is not rendered (Streamlit default)
            st.divider()
            st.download_button(
                "⬇️  Download report (.md)",
                data=report,
                file_name=f"{slugify(rec['topic'])}-report.md",
                mime="text/markdown",
                key=f"dl_md_{rec['id']}",
            )
            with st.expander("📋 Copy report (use the copy icon on the code block)"):
                st.code(report, language="markdown")

    with tab_search:
        if not search.strip():
            st.info("The Search Agent returned no content.")
        else:
            urls = extract_urls(search)
            if urls:
                st.markdown("**Sources detected**")
                st.markdown("\n".join(f"- [{u}]({u})" for u in urls))
            with st.expander("Raw search agent output", expanded=not urls):
                st.markdown(search)

    with tab_scraped:
        if not scraped.strip():
            st.info("The Reader Agent returned no content.")
        else:
            preview, truncated = clip(scraped)
            with st.expander("Extracted content", expanded=True):
                st.markdown(preview)
                if truncated:
                    st.caption("Showing the first part only. The JSON export contains the full text.")

    with tab_critic:
        if not feedback.strip():
            st.info("The Critic Chain returned no feedback.")
        else:
            st.markdown(feedback)

    all_present = all(str(state.get(f, "")).strip() for f in STATE_FIELD.values())
    export = {
        "topic": rec["topic"],
        "started_at": rec["started_at"],
        "search_results": search,
        "scraped_content": scraped,
        "report": report,
        "feedback": feedback,
    }
    st.download_button(
        "⬇️  Download full output (.json)",
        data=json.dumps(export, indent=2, ensure_ascii=False),
        file_name=f"{slugify(rec['topic'])}-research.json",
        mime="application/json",
        disabled=not all_present,
        help=None if all_present else "Available when all four outputs contain content.",
        key=f"dl_json_{rec['id']}",
    )


# --------------------------------------------------------------------------
# History + About
# --------------------------------------------------------------------------
def page_history():
    st.markdown('<div class="section-title" style="margin-top:0">Research History</div>', unsafe_allow_html=True)
    st.caption(
        f"Saved as JSON files in `{HISTORY_DIR.name}/` on the machine running this app. "
        "On Streamlit Community Cloud this storage is temporary and is cleared when the app restarts."
    )
    err = st.session_state.pop("history_error", None)
    if err:
        st.error(err)

    items = list_history()
    if not items:
        st.markdown(
            '<div class="card"><h3>Nothing saved yet</h3><p>Completed research runs will appear here.</p></div>',
            unsafe_allow_html=True,
        )
        return

    for data in items:
        try:
            when = datetime.fromisoformat(data["started_at"]).strftime("%d %b %Y, %H:%M")
        except (ValueError, KeyError, TypeError):
            when = "—"
        dur = fmt_duration(data["duration"]) if data.get("duration") is not None else "—"
        with st.container(border=True):
            c1, c2, c3 = st.columns([6, 1.3, 1.3], vertical_alignment="center")
            c1.markdown(f"**{data.get('topic', 'Untitled')}**  \n:gray[{when} · {dur}]")
            c2.button("Open", key=f"open_{data['id']}", on_click=open_record, args=(data["id"],), use_container_width=True)
            c3.button("Delete", key=f"del_{data['id']}", on_click=delete_record, args=(data["id"],), use_container_width=True)


def page_about():
    st.markdown(
        '<div class="card"><h3>About ResearchFlow AI</h3>'
        "<p>ResearchFlow AI is a user interface for a multi-agent research system. "
        "A topic goes through four stages and every output is shown exactly as the backend produced it.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(tracker_html({}, show_status=False), unsafe_allow_html=True)
    st.markdown(
        '<div class="card"><h3>Good to know</h3><ul>'
        "<li>Reports and critic feedback are AI-generated. The app does not verify facts or score quality.</li>"
        "<li>The Reader Agent scrapes one URL chosen from the search results.</li>"
        "<li>Research history is stored locally in JSON files.</li>"
        "<li>Leaving the workspace while a run is in progress cancels that run's display.</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
for _key, _default in {"page": "dashboard", "current": None, "pending_topic": None, "running": False}.items():
    st.session_state.setdefault(_key, _default)

render_sidebar()

PAGES = {
    "dashboard": page_dashboard,
    "workspace": page_workspace,
    "history": page_history,
    "about": page_about,
}
PAGES.get(st.session_state.page, page_dashboard)()