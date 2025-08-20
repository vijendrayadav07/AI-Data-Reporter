import os
import streamlit as st
import requests
from file_handler import load_data
from eda import (
    show_basic_info,
    show_missing_values,
    show_summary_stats,
    show_correlation_heatmap,
    show_custom_plot
)

API_URL = "http://localhost:5000"

st.set_page_config(page_title="Data2Docs", layout="wide")
st.title("📊 Data2Docs – AI Report Generator from Any Data File")

# ---------- SESSION ----------
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "stats" not in st.session_state:
    st.session_state.stats = None
if "insights" not in st.session_state:
    st.session_state.insights = None

# ---------- SIDEBAR: Login / Signup ----------
st.sidebar.title("Account")

def safe_json(res):
    try:
        return res.json()
    except Exception:
        return {}

if not st.session_state.token:
    action = st.sidebar.radio("Choose", ["Login", "Sign up"])

    if action == "Sign up":
        with st.sidebar.form("signup", clear_on_submit=False):
            su_username = st.text_input("Username")
            su_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create account")
            if submitted:
                try:
                    res = requests.post(f"{API_URL}/signup", json={"username": su_username, "password": su_password})
                    if res.status_code == 201:
                        st.sidebar.success("✅ Account created! Please log in.")
                    else:
                        st.sidebar.error(safe_json(res).get("error", "Signup failed"))
                except Exception as e:
                    st.sidebar.error(f"❌ Signup failed: {e}")

    else:  # Login
        with st.sidebar.form("login", clear_on_submit=False):
            li_username = st.text_input("Username")
            li_password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button("Login")
            if login_clicked:
                try:
                    res = requests.post(f"{API_URL}/login", json={"username": li_username, "password": li_password})
                    if res.status_code == 200:
                        st.session_state.token = safe_json(res).get("access_token")
                        st.session_state.user = li_username
                        st.sidebar.success(f"Welcome {li_username}!")
                    else:
                        st.sidebar.error(safe_json(res).get("error", "Login failed"))
                except Exception as e:
                    st.sidebar.error(f"❌ Login failed: {e}")
else:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.session_state.stats = None
        st.session_state.insights = None
        st.experimental_rerun()

# ---------- MAIN CONTENT ----------
if not st.session_state.token:
    st.info("Please sign up or log in from the sidebar to continue.")
    st.stop()

st.markdown("Upload a **CSV**, **Excel**, or **JSON** file to begin:")

uploaded_file = st.file_uploader("📁 Choose a file", type=["csv", "xlsx", "json"])
df = None

if uploaded_file:
    try:
        df = load_data(uploaded_file)
        st.success(f"✅ File loaded successfully! Shape: {df.shape}")
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head())

        st.markdown("---")
        st.header("📈 Exploratory Data Analysis")

        with st.expander("📌 Basic Information"):
            if st.checkbox("Show Basic Info"):
                show_basic_info(df)

        with st.expander("🔎 Missing Values"):
            if st.checkbox("Check Missing Values"):
                show_missing_values(df)

        with st.expander("📊 Summary Statistics"):
            if st.checkbox("View Summary Stats"):
                show_summary_stats(df)

        with st.expander("🔥 Correlation Heatmap"):
            if st.checkbox("Show Correlation Heatmap"):
                show_correlation_heatmap(df)

        with st.expander("🛠️ Build Custom Plot"):
            if st.checkbox("Create a Custom Chart"):
                show_custom_plot(df)

        with st.expander("🧠 Generate AI Insights with Groq"):
            if st.button("Generate Insights"):
                with st.spinner("🤖 Groq is thinking..."):
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    try:
                        res = requests.post(
                            f"{API_URL}/insights",
                            json={"stats": df.describe(include='all').to_dict()},
                            headers=headers
                        )
                        data = safe_json(res)
                        if res.status_code == 200:
                            st.session_state.insights = data["insights"]
                            st.success("✅ Insights generated!")
                            st.markdown("### 💡 AI Insights")
                            st.markdown(st.session_state.insights)
                        else:
                            st.error(data.get("error", "Failed to generate insights"))
                    except Exception as e:
                        st.error(f"⚠️ Could not reach backend: {e}")

            if st.session_state.insights and st.button("📄 Download PDF Report"):
                with st.spinner("📦 Generating PDF..."):
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    try:
                        res = requests.post(f"{API_URL}/export", json={"insights": st.session_state.insights}, headers=headers)
                        data = safe_json(res)
                        if res.status_code == 200:
                            pdf_path = data.get("pdf_path")
                            if pdf_path and os.path.exists(pdf_path):
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        label="📥 Download PDF",
                                        data=f,
                                        file_name="data2docs_report.pdf",
                                        mime="application/pdf"
                                    )
                            else:
                                st.error("❌ PDF not found on server.")
                        else:
                            st.error(data.get("error", "PDF export failed"))
                    except Exception as e:
                        st.error(f"⚠️ Could not reach backend: {e}")

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
else:
    st.info("👆 Please upload a file to start.")

# ------------------------
# 💬 Chat with Groq AI
# ------------------------
st.markdown("---")
st.header("💬 Chat with Groq AI About Your Data")

if df is not None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "You're a helpful data analyst."},
            {"role": "user", "content": f"Here's a preview of the data:\n\n{df.head(3).to_string(index=False)}"}
        ]

    prompt = st.text_input("Ask something about your data:")

    if prompt:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("🤖 Thinking..."):
            try:
                res = requests.post(f"{API_URL}/chat", json={"history": st.session_state.chat_history}, headers=headers)
                data = safe_json(res)
                if res.status_code == 200:
                    reply = data["reply"]
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                else:
                    st.error(data.get("error", "Chat failed"))
            except Exception as e:
                st.error(f"⚠️ Could not reach backend: {e}")

    st.markdown("### 💬 Conversation History")
    for msg in st.session_state.chat_history[2:]:
        icon = "👤" if msg["role"] == "user" else "🤖"
        st.markdown(f"{icon} **{msg['role'].capitalize()}**: {msg['content']}")
else:
    st.warning("⚠️ Please upload a file first to enable chat.")
