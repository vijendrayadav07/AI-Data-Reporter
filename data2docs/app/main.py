# app/main.py

import streamlit as st
from file_handler import load_data
from insights import generate_insights
from chat_with_groq import chat_with_groq
from eda import (
    show_basic_info,
    show_missing_values,
    show_summary_stats,
    show_correlation_heatmap,
    show_custom_plot
)

st.set_page_config(page_title="Data2Docs", layout="wide")
st.title("📊 Data2Docs – AI Report Generator from Any Data File")

st.markdown("Upload a **CSV**, **Excel**, or **JSON** file to begin:")

# Upload section
uploaded_file = st.file_uploader("📁 Choose a file", type=["csv", "xlsx", "json"])
df = None  # ✅ Define df early to avoid NameError

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

        with st.expander("🧠 Generate AI Insights"):
            if st.button("Generate Insights with Groq"):
                generate_insights(df)

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
else:
    st.info("👆 Please upload a file to start.")

# ------------------------------------------
# 💬 Chat Feature with Groq AI
# ------------------------------------------

st.markdown("---")
st.header("💬 Chat with Groq AI About Your Data")

if df is not None:
    # ✅ Add reset button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Reset Chat"):
            st.session_state.pop("chat_history", None)
            st.rerun()

    # ✅ Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": "You are a data analyst AI. Help the user understand the uploaded dataset in simple, clear language. Be concise, but insightful."
            },
            {
                "role": "user",
                "content": f"Here's a preview of the data:\n\n{df.head(3).to_string(index=False)}"
            }
        ]

    # ✅ Chat prompt input
    user_prompt = st.text_input("Ask something about your data:")

    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.spinner("🤖 Thinking..."):
            answer = chat_with_groq(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

    # ✅ Display chat history
    st.markdown("### 💬 Conversation History")
    for msg in st.session_state.chat_history[2:]:  # skip system + preview
        is_user = msg["role"] == "user"
        icon = "👤" if is_user else "🤖"
        st.markdown(f"{icon} **{msg['role'].capitalize()}**: {msg['content']}")

else:
    st.warning("⚠️ Please upload a file first to enable data-based chat.")
