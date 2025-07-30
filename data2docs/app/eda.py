# app/eda.py

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

def show_basic_info(df):
    st.subheader("📌 Basic Info")
    st.write("**Shape:**", df.shape)
    st.write("**Columns:**", list(df.columns))
    st.write("**Data Types:**")
    st.dataframe(df.dtypes)

def show_missing_values(df):
    st.subheader("🔎 Missing Values")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        st.write("Found missing values:")
        st.dataframe(missing)
    else:
        st.success("✅ No missing values found!")

def show_summary_stats(df):
    st.subheader("📊 Summary Statistics")
    st.dataframe(df.describe())

def show_correlation_heatmap(df):
    st.subheader("📈 Correlation Heatmap")
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] < 2:
        st.info("Not enough numerical columns for correlation heatmap.")
        return

    corr = numeric_df.corr()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
    st.pyplot(fig)
