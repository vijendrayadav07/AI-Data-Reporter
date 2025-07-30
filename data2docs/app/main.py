# app/main.py

import streamlit as st
from file_handler import load_data
from eda import show_basic_info, show_missing_values, show_summary_stats, show_correlation_heatmap


st.set_page_config(page_title="Data2Docs", layout="wide")
st.title("📊 Data2Docs – AI Report Generator from Any Data File")

st.markdown("Upload a **CSV**, **Excel**, or **JSON** file to begin:")

uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json"])

if uploaded_file:
    try:
        df = load_data(uploaded_file)
        st.success(f"✅ File loaded successfully! Shape: {df.shape}")
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head())

        # Step2: Auto eda
        show_basic_info(df)
        show_missing_values(df)
        show_summary_stats(df)
        show_correlation_heatmap(df)
    except Exception as e:
        st.error(f"❌ Error: {e}")
