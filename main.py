import streamlit as st
import requests
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  FILE HELPERS
# ─────────────────────────────────────────────
BOOKMARK_FILE = "bookmarks.json"


def load_bookmarks() -> list:
    """Load saved bookmarks from disk."""
    if os.path.exists(BOOKMARK_FILE):
        with open(BOOKMARK_FILE, "r") as f:
            return json.load(f)
    return []


def save_bookmarks(bookmarks: list) -> None:
    """Persist bookmarks list to disk."""
    with open(BOOKMARK_FILE, "w") as f:
        json.dump(bookmarks, f, indent=4)


def format_date(iso_string: str) -> str:
    """Convert ISO 8601 date string to a human-friendly format."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y · %H:%M UTC")
    except Exception:
        return iso_string


# ─────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pulse — AI News",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = load_bookmarks()

if "articles" not in st.session_state:
    st.session_state.articles = []

if "fetched" not in st.session_state:
    st.session_state.fetched = False

if "fetch_error" not in st.session_state:
    st.session_state.fetch_error = ""

# ─────────────────────────────────────────────
#  API KEY
# ─────────────────────────────────────────────
try:
    API_KEY = st.secrets["API_KEY"]
except (KeyError, FileNotFoundError):
    API_KEY = os.getenv("NEWS_API_KEY", "")

# ─────────────────────────────────────────────
#  PREMIUM CSS — LIGHT THEME
# ─────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── CSS Variables ── */
:root {
    --bg:          #F5F7FA;
    --bg-alt:      #EEF2F7;
    --card:        #FFFFFF;
    --card-hover:  #FAFBFF;
    --primary:     #2563EB;
    --primary-lt:  #3B82F6;
    --primary-dim: #EFF6FF;
    --text:        #1F2937;
    --text-muted:  #6B7280;
    --border:      #E5E7EB;
    --shadow-sm:   0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md:   0 4px 16px rgba(0,0,0,.08), 0 2px 6px rgba(0,0,0,.04);
    --shadow-lg:   0 12px 32px rgba(37,99,235,.12), 0 4px 12px rgba(0,0,0,.06);
    --radius:      14px;
    --radius-sm:   8px;
    --transition:  0.25s cubic-bezier(.4,0,.2,1);
}

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}

/* ── Custom Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-alt); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #CBD5E1; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Main layout padding ── */
.block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1280px !important;
}

/* ── HERO ── */
.hero-wrap {
    background: linear-gradient(135deg, #EFF6FF 0%, #F0F7FF 50%, #F5F7FA 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3rem 3.5rem;
    margin-bottom: 2.5rem;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 60% 80% at 80% 50%, rgba(37,99,235,.06), transparent);
    pointer-events: none;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--primary);
    background: var(--primary-dim);
    padding: 4px 12px;
    border-radius: 99px;
    margin-bottom: 1rem;
}
.hero-eyebrow .dot {
    width: 6px; height: 6px;
    background: var(--primary);
    border-radius: 50%;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.5; transform:scale(1.3); }
}
.hero-title {
    font-family: 'Lora', serif !important;
    font-size: clamp(1.8rem, 3.5vw, 2.8rem) !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    line-height: 1.2 !important;
    margin: 0 0 .75rem !important;
}
.hero-sub {
    font-size: 1rem;
    color: var(--text-muted);
    font-weight: 400;
    max-width: 520px;
    line-height: 1.65;
}

/* ── SEARCH BAR ── */
.stTextInput > div > div > input {
    background: var(--card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 99px !important;
    padding: 0.7rem 1.4rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    color: var(--text) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: border-color var(--transition), box-shadow var(--transition) !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #9CA3AF !important; }

/* ── PRIMARY BUTTON ── */
.stButton > button {
    background: var(--primary) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 99px !important;
    padding: .6rem 1.6rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: .88rem !important;
    letter-spacing: .02em !important;
    box-shadow: 0 2px 8px rgba(37,99,235,.25) !important;
    transition: transform var(--transition), box-shadow var(--transition), background var(--transition) !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: #1D4ED8 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,.35) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    background: var(--card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── SLIDER ── */
.stSlider .st-bx { background: var(--primary-dim) !important; }
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
}

/* ── NEWS CARD ── */
.news-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition);
    animation: fadeSlideUp .4s ease both;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.news-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
    border-color: #BFDBFE;
}
@keyframes fadeSlideUp {
    from { opacity:0; transform:translateY(18px); }
    to   { opacity:1; transform:translateY(0); }
}
.card-img-wrap {
    width: 100%;
    height: 200px;
    overflow: hidden;
    background: var(--bg-alt);
    flex-shrink: 0;
}
.card-img-wrap img {
    width: 100%; height: 100%;
    object-fit: cover;
    transition: transform .5s ease;
}
.news-card:hover .card-img-wrap img { transform: scale(1.04); }
.card-img-placeholder {
    width:100%; height:100%;
    display:flex; align-items:center; justify-content:center;
    background: linear-gradient(135deg, #EEF2F7, #E5E7EB);
    font-size: 2.5rem;
    color: #9CA3AF;
}
.card-body {
    padding: 1.3rem 1.4rem 1.5rem;
    display: flex;
    flex-direction: column;
    flex: 1;
}
.card-source-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: .65rem;
}
.card-source-badge {
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--primary);
    background: var(--primary-dim);
    padding: 2px 9px;
    border-radius: 99px;
}
.card-date {
    font-size: .75rem;
    color: var(--text-muted);
    font-weight: 400;
}
.card-title {
    font-family: 'Lora', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.45;
    margin-bottom: .6rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.card-desc {
    font-size: .84rem;
    color: var(--text-muted);
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: 1.1rem;
    flex: 1;
}
.card-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: auto;
}
.btn-read {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    text-decoration: none !important;
    background: var(--primary);
    color: #fff !important;
    font-size: .8rem;
    font-weight: 600;
    padding: 7px 16px;
    border-radius: 99px;
    transition: background var(--transition), transform var(--transition), box-shadow var(--transition);
    box-shadow: 0 2px 8px rgba(37,99,235,.2);
}
.btn-read:hover {
    background: #1D4ED8;
    transform: translateY(-1px);
    box-shadow: 0 5px 16px rgba(37,99,235,.32);
}
.btn-save {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    text-decoration: none !important;
    background: transparent;
    color: var(--primary) !important;
    font-size: .8rem;
    font-weight: 600;
    padding: 6px 15px;
    border-radius: 99px;
    border: 1.5px solid var(--primary);
    cursor: pointer;
    transition: background var(--transition), transform var(--transition);
}
.btn-save:hover {
    background: var(--primary-dim);
    transform: translateY(-1px);
}
.btn-saved {
    background: #ECFDF5 !important;
    border-color: #10B981 !important;
    color: #065F46 !important;
}

/* ── SECTION HEADER ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.section-title {
    font-family: 'Lora', serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text);
    margin: 0;
}
.section-count {
    font-size: .78rem;
    font-weight: 600;
    color: var(--primary);
    background: var(--primary-dim);
    padding: 3px 10px;
    border-radius: 99px;
}

/* ── SKELETON LOADER ── */
.skeleton-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}
.skeleton-img {
    height: 200px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
}
.skeleton-body { padding: 1.3rem 1.4rem; }
.skeleton-line {
    height: 12px;
    border-radius: 99px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
    margin-bottom: 10px;
}
@keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* ── EMPTY STATE ── */
.empty-state {
    text-align: center;
    padding: 5rem 2rem;
    background: var(--card);
    border: 1px dashed var(--border);
    border-radius: var(--radius);
}
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-title {
    font-family: 'Lora', serif;
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: .5rem;
}
.empty-sub { font-size: .9rem; color: var(--text-muted); max-width: 340px; margin: 0 auto; }

/* ── ALERTS ── */
.alert {
    padding: .85rem 1.2rem;
    border-radius: var(--radius-sm);
    font-size: .88rem;
    font-weight: 500;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: fadeSlideUp .3s ease;
}
.alert-success { background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; }
.alert-error   { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }
.alert-info    { background: var(--primary-dim); border: 1px solid #BFDBFE; color: #1E40AF; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding: 1.5rem 1rem; }

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: .5rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.sidebar-logo-icon { font-size: 1.6rem; }
.sidebar-logo-text {
    font-family: 'Lora', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
}
.sidebar-logo-text span { color: var(--primary); }

.sidebar-stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: .75rem;
    text-align: center;
}
.stat-number {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--primary);
    line-height: 1;
    margin-bottom: .2rem;
}
.stat-label { font-size: .7rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: .05em; }

.sidebar-section-label {
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 1.2rem 0 .6rem;
}

.bookmark-item {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: .7rem .9rem;
    margin-bottom: .5rem;
    transition: border-color var(--transition);
}
.bookmark-item:hover { border-color: #BFDBFE; }
.bookmark-title {
    font-size: .8rem;
    font-weight: 500;
    color: var(--text);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: .3rem;
}
.bookmark-link {
    font-size: .75rem;
    color: var(--primary);
    text-decoration: none;
    font-weight: 600;
}
.bookmark-link:hover { text-decoration: underline; }

/* ── GLASS DIVIDER ── */
.glass-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 2rem 0;
}

/* Stagger card animation delays */
.card-delay-0  { animation-delay: 0.05s; }
.card-delay-1  { animation-delay: 0.10s; }
.card-delay-2  { animation-delay: 0.15s; }
.card-delay-3  { animation-delay: 0.20s; }
.card-delay-4  { animation-delay: 0.25s; }
.card-delay-5  { animation-delay: 0.30s; }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">📡</div>
            <div class="sidebar-logo-text">Pulse<span>News</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section-label">⚙️ Filters</div>', unsafe_allow_html=True)

    category = st.selectbox(
        "Category",
        ["artificial intelligence", "technology", "business", "sports", "health", "science"],
        label_visibility="collapsed",
    )
    limit = st.slider("Articles to load", 3, 20, 9, label_visibility="visible")

    # Stats
    n_bookmarks = len(st.session_state.bookmarks)
    n_articles  = len(st.session_state.articles)
    st.markdown(
        f"""
        <div class="sidebar-section-label">📊 Session Stats</div>
        <div class="sidebar-stat-grid">
            <div class="stat-card">
                <div class="stat-number">{n_articles}</div>
                <div class="stat-label">Loaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{n_bookmarks}</div>
                <div class="stat-label">Saved</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bookmarks
    st.markdown('<div class="sidebar-section-label">🔖 Saved Articles</div>', unsafe_allow_html=True)

    if not st.session_state.bookmarks:
        st.markdown(
            '<p style="font-size:.8rem;color:#9CA3AF;padding:.5rem 0;">No bookmarks yet.</p>',
            unsafe_allow_html=True,
        )
    else:
        for i, saved in enumerate(st.session_state.bookmarks):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"""
                    <div class="bookmark-item">
                        <div class="bookmark-title">{saved.get('title', 'Untitled')}</div>
                        <a class="bookmark-link" href="{saved.get('url','#')}" target="_blank">↗ Read</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("✕", key=f"del_{i}", help="Remove bookmark"):
                    st.session_state.bookmarks.pop(i)
                    save_bookmarks(st.session_state.bookmarks)
                    st.rerun()

        st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)
        if st.button("🗑 Clear All Bookmarks"):
            st.session_state.bookmarks = []
            save_bookmarks([])
            st.rerun()


# ─────────────────────────────────────────────
#  HERO SECTION
# ─────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-eyebrow"><span class="dot"></span>Live Intelligence Feed</div>
        <h1 class="hero-title">Your World.<br>Curated &amp; Clear.</h1>
        <p class="hero-sub">
            Stay ahead with AI-powered news discovery. Search any topic and get
            the freshest stories delivered in a clean, distraction-free reading experience.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
#  SEARCH ROW
# ─────────────────────────────────────────────
col_search, col_btn = st.columns([5, 1], gap="small")
with col_search:
    query = st.text_input(
        "search",
        value=category,
        placeholder="🔍  Search any topic — AI, climate, markets…",
        label_visibility="collapsed",
    )
with col_btn:
    fetch_clicked = st.button("Search →", use_container_width=True)

st.markdown("<div class='glass-divider'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  FETCH NEWS
# ─────────────────────────────────────────────
def fetch_news(topic: str, n: int) -> tuple[list, str]:
    """Call NewsAPI and return (articles, error_message)."""
    if not API_KEY:
        return [], "No API key found. Add `API_KEY` to `.streamlit/secrets.toml` or set the `NEWS_API_KEY` env variable."
    url = (
        f"https://newsapi.org/v2/everything"
        f"?qInTitle={requests.utils.quote(topic)}"
        f"&sortBy=publishedAt"
        f"&language=en"
        f"&pageSize={n}"
        f"&apiKey={API_KEY}"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "error":
            return [], data.get("message", "API error.")
        articles = [a for a in data.get("articles", []) if a.get("title") and a["title"] != "[Removed]"]
        return articles[:n], ""
    except requests.exceptions.ConnectionError:
        return [], "Network error — check your internet connection."
    except requests.exceptions.Timeout:
        return [], "Request timed out. Please try again."
    except Exception as exc:
        return [], f"Unexpected error: {exc}"


if fetch_clicked:
    # Show skeletons
    st.markdown(
        """
        <div class="section-header">
            <p class="section-title">Loading results…</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    sk_cols = st.columns(3, gap="large")
    for sc in sk_cols:
        with sc:
            st.markdown(
                """
                <div class="skeleton-card">
                    <div class="skeleton-img"></div>
                    <div class="skeleton-body">
                        <div class="skeleton-line" style="width:40%;margin-bottom:14px"></div>
                        <div class="skeleton-line" style="width:100%"></div>
                        <div class="skeleton-line" style="width:90%"></div>
                        <div class="skeleton-line" style="width:70%;margin-top:14px"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    articles, error = fetch_news(query.strip() or category, limit)
    st.session_state.articles  = articles
    st.session_state.fetch_error = error
    st.session_state.fetched   = True
    st.rerun()


# ─────────────────────────────────────────────
#  DISPLAY ARTICLES
# ─────────────────────────────────────────────
if st.session_state.fetch_error:
    st.markdown(
        f'<div class="alert alert-error">⚠️ {st.session_state.fetch_error}</div>',
        unsafe_allow_html=True,
    )

elif st.session_state.fetched and not st.session_state.articles:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🔭</div>
            <div class="empty-title">Nothing found</div>
            <p class="empty-sub">Try a different search term or broaden your query.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif st.session_state.articles:
    articles = st.session_state.articles

    st.markdown(
        f"""
        <div class="section-header">
            <p class="section-title">Latest Stories</p>
            <span class="section-count">{len(articles)} articles</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3-column grid
    COLS = 3
    saved_urls = {b["url"] for b in st.session_state.bookmarks}

    for row_start in range(0, len(articles), COLS):
        row_articles = articles[row_start: row_start + COLS]
        cols = st.columns(COLS, gap="large")

        for col_idx, article in enumerate(row_articles):
            global_idx = row_start + col_idx
            delay_cls  = f"card-delay-{min(global_idx, 5)}"

            with cols[col_idx]:
                img_url     = article.get("urlToImage", "")
                title       = article.get("title", "Untitled")
                description = article.get("description") or "No description available."
                article_url = article.get("url", "#")
                pub_date    = format_date(article.get("publishedAt", ""))
                source      = article.get("source", {}).get("name", "Unknown")
                is_saved    = article_url in saved_urls
                save_cls    = "btn-save btn-saved" if is_saved else "btn-save"
                save_label  = "✓ Saved" if is_saved else "🔖 Save"

                # Card HTML
                img_html = (
                    f'<img src="{img_url}" alt="Article image" loading="lazy"/>'
                    if img_url
                    else '<div class="card-img-placeholder">📰</div>'
                )

                st.markdown(
                    f"""
                    <div class="news-card {delay_cls}">
                        <div class="card-img-wrap">{img_html}</div>
                        <div class="card-body">
                            <div class="card-source-row">
                                <span class="card-source-badge">{source}</span>
                                <span class="card-date">{pub_date}</span>
                            </div>
                            <div class="card-title">{title}</div>
                            <div class="card-desc">{description}</div>
                            <div class="card-actions">
                                <a class="btn-read" href="{article_url}" target="_blank">Read More ↗</a>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Save button (must be a real Streamlit widget)
                st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)
                if st.button(save_label, key=f"save_{global_idx}", use_container_width=True):
                    if is_saved:
                        st.session_state.bookmarks = [
                            b for b in st.session_state.bookmarks if b["url"] != article_url
                        ]
                        save_bookmarks(st.session_state.bookmarks)
                        st.rerun()
                    else:
                        st.session_state.bookmarks.append(article)
                        save_bookmarks(st.session_state.bookmarks)
                        st.markdown(
                            '<div class="alert alert-success">✅ Article bookmarked!</div>',
                            unsafe_allow_html=True,
                        )
                        st.rerun()

        st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)

else:
    # First visit — prompt
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">✨</div>
            <div class="empty-title">Ready when you are</div>
            <p class="empty-sub">Enter a topic above and hit <strong>Search →</strong> to load the latest stories.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
