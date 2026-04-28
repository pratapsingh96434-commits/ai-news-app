import streamlit as st
import requests
import json
import os

# ------------------ FILE SETUP ------------------
BOOKMARK_FILE = "bookmarks.json"

def load_bookmarks():
    if os.path.exists(BOOKMARK_FILE):
        with open(BOOKMARK_FILE, "r") as f:
            return json.load(f)
    return []

def save_bookmarks(bookmarks):
    with open(BOOKMARK_FILE, "w") as f:
        json.dump(bookmarks, f, indent=4)

# ------------------ SESSION ------------------
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = load_bookmarks()

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI News App", layout="wide")

# ------------------ CSS ------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    background-attachment: fixed;
    color: white;
}

/* Glass cards */
[data-testid="stContainer"] {
    background: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 15px;
    backdrop-filter: blur(12px);
    margin-bottom: 20px;
}

/* Buttons */
.stButton>button {
    background-color: #00c6ff;
    color: black;
    border-radius: 10px;
    padding: 10px 20px;
}

/* Input */
.stTextInput>div>div>input {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ------------------ API ------------------
API_KEY = st.secrets["API_KEY"]  # ⚠️ Replace this

# ------------------ SIDEBAR ------------------
st.sidebar.title("⚙️ Settings")

category = st.sidebar.selectbox(
    "Select Category",
    ["artificial intelligence", "technology", "business", "sports", "health"]
)

limit = st.sidebar.slider("Number of Articles", 5, 20, 10)

# ------------------ BOOKMARK SIDEBAR ------------------
st.sidebar.subheader("⭐ Saved Articles")

for i, saved in enumerate(st.session_state.bookmarks):
    col1, col2 = st.sidebar.columns([4,1])

    with col1:
        st.write(f"{i+1}. {saved['title']}")
        st.markdown(f"[Read]({saved['url']})")

    with col2:
        if st.button("❌", key=f"del_{i}"):
            st.session_state.bookmarks.pop(i)
            save_bookmarks(st.session_state.bookmarks)
            st.rerun()

if st.sidebar.button("🗑 Clear All"):
    st.session_state.bookmarks = []
    save_bookmarks([])
    st.rerun()

# ------------------ MAIN UI ------------------
st.title("📰 AI News App")
st.write("Get latest news with a modern UI 🚀")

query = st.text_input("Enter topic", category)

# ------------------ FETCH NEWS ------------------
if st.button("Get News"):

    url = f"https://newsapi.org/v2/everything?qInTitle={query}&sortBy=publishedAt&language=en&apiKey={API_KEY}"

    with st.spinner("Fetching latest news..."):
        r = requests.get(url)
        data = r.json()
        articles = data.get("articles", [])[:limit]

    # ------------------ DISPLAY ------------------
    for index, article in enumerate(articles):

        with st.container():

            # Image
            if article.get("urlToImage"):
                st.image(article["urlToImage"], use_container_width=True)

            # Title
            st.subheader(f"{index+1}. {article['title']}")

            # Date
            st.write(f"🕒 {article['publishedAt']}")

            # Description
            if article.get("description"):
                st.write(article["description"])

            # Link
            st.markdown(f"[🔗 Read Full Article]({article['url']})")

            # ⭐ Save Button
            if st.button(f"⭐ Save", key=f"save_{index}"):

                # Avoid duplicate
                if not any(b["url"] == article["url"] for b in st.session_state.bookmarks):
                    st.session_state.bookmarks.append(article)
                    save_bookmarks(st.session_state.bookmarks)
                    st.success("Saved!")
                else:
                    st.info("Already saved")

            st.write("---")