import os
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

import requests
from file_handler import load_data
from eda import (
    show_basic_info,
    show_missing_values,
    show_summary_stats,
    show_correlation_heatmap,
    show_custom_plot
)
import pandas as pd

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
API_URL = os.getenv("API_URL", "http://localhost:5000")

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
# will store cleaned df when user clicks auto-handle
if "df_clean" not in st.session_state:
    st.session_state.df_clean = None

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
        st.session_state.df_clean = None
        st.experimental_rerun()

# ---------- MAIN CONTENT ----------
if not st.session_state.token:
    st.info("Please sign up or log in from the sidebar to continue.")
    st.stop()

st.markdown("Upload a **CSV**, **Excel**, or **JSON** file to begin:")

uploaded_file = st.file_uploader("📁 Choose a file", type=["csv", "xlsx", "json"])
df = None

# ---------- Missing Value Handler ----------
def auto_handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    df_filled = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            if df[col].isnull().sum() > 0:
                mode_val = df[col].mode()[0] if not df[col].mode().empty else "Unknown"
                df_filled[col] = df[col].fillna(mode_val)
        else:
            if df[col].isnull().sum() > 0:
                df_filled[col] = df[col].fillna(df[col].median())
    return df_filled

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

            if st.button("⚡ Auto Handle Missing Values"):
                df_clean = auto_handle_missing(df)
                st.session_state.df_clean = df_clean
                st.success("✅ Missing values handled automatically!")
                st.dataframe(df_clean.head())

                # download cleaned dataset
                st.download_button(
                    label="📥 Download Cleaned CSV",
                    data=df_clean.to_csv(index=False).encode("utf-8"),
                    file_name="cleaned_data.csv",
                    mime="text/csv"
                )

            if st.button("🤖 Ask AI for Handling Strategy"):
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                try:
                    res = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "history": [
                                {"role": "system", "content": "You're a data cleaning assistant."},
                                {"role": "user", "content": f"Suggest how to handle missing values in this dataset:\n\n{df.isnull().sum().to_dict()}"}
                            ]
                        },
                        headers=headers
                    )
                    data = safe_json(res)
                    if res.status_code == 200:
                        st.markdown("### 💡 AI Suggestion")
                        st.markdown(data["reply"])
                    else:
                        st.error(data.get("error", "AI handling failed"))
                except Exception as e:
                    st.error(f"⚠️ Could not reach backend: {e}")

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

# ---------------------------
# 📊 Dashboard Section
# ---------------------------
st.header("📊 Interactive Dashboard")

# Use cleaned data if available, else raw
data_for_viz = st.session_state.df_clean if st.session_state.df_clean is not None else df

if data_for_viz is None:
    st.info("Upload a file (and optionally clean it) to use the dashboard.")
else:
    # options
    chart_options = ["Histogram", "Boxplot", "Correlation Heatmap", "Scatter Plot", "Line Chart"]
    selected_charts = st.multiselect(
        "Select the charts you want to display:",
        chart_options,
        default=chart_options[:2]
    )

    # layout columns
    cols_per_row = st.slider("Columns per row", 1, 3, 2)

    # ---- chart renderer with collapsible settings ----
    # ---- chart renderer with customer-controlled labels/columns ----
    def render_chart(df_in, chart_type, key_prefix=""):
        numeric_cols = df_in.select_dtypes(include="number").columns.tolist()
        if chart_type in ("Histogram", "Boxplot", "Scatter Plot", "Line Chart") and len(numeric_cols) == 0:
            st.warning("No numeric columns found for this chart.")
            return

        with st.expander(f"Show {chart_type}"):
            # custom title for all charts
            custom_title = st.text_input(
                f"Title for {chart_type}:",
                value=chart_type,
                key=f"title_{key_prefix}_{chart_type}"
            )

            if chart_type == "Histogram":
                col = st.selectbox(
                    "Select column for Histogram:",
                    numeric_cols,
                    key=f"hist_col_{key_prefix}"
                )
                bins = st.slider("Bins:", 5, 100, 20, key=f"bins_{key_prefix}")
                x_label = st.text_input("X-axis label:", col, key=f"hist_xlabel_{key_prefix}")
                y_label = st.text_input("Y-axis label:", "Frequency", key=f"hist_ylabel_{key_prefix}")

                fig, ax = plt.subplots()
                df_in[col].hist(ax=ax, bins=bins)
                ax.set_title(custom_title)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                st.pyplot(fig)

            elif chart_type == "Boxplot":
                cols = st.multiselect(
                    "Select columns for Boxplot:",
                    numeric_cols,
                    default=numeric_cols[:1],
                    key=f"box_cols_{key_prefix}"
                )
                if cols:
                    fig, ax = plt.subplots()
                    sns.boxplot(data=df_in[cols], ax=ax)
                    ax.set_title(custom_title)
                    st.pyplot(fig)
                else:
                    st.info("Select at least one column for the Boxplot.")

            elif chart_type == "Correlation Heatmap":
                if len(df_in.select_dtypes(include="number").columns) < 2:
                    st.info("Need at least two numeric columns for a heatmap.")
                else:
                    fig, ax = plt.subplots(figsize=(5, 4))
                    sns.heatmap(df_in.corr(numeric_only=True), cmap="coolwarm", annot=True, ax=ax)
                    ax.set_title(custom_title)
                    st.pyplot(fig)

            elif chart_type == "Scatter Plot":
                if len(numeric_cols) < 2:
                    st.info("Need at least two numeric columns for a scatter plot.")
                else:
                    x_col = st.selectbox("X-axis column:", numeric_cols, key=f"xcol_{key_prefix}")
                    y_col = st.selectbox("Y-axis column:", numeric_cols, key=f"ycol_{key_prefix}")
                    x_label = st.text_input("X-axis label:", x_col, key=f"xlab_{key_prefix}")
                    y_label = st.text_input("Y-axis label:", y_col, key=f"ylab_{key_prefix}")

                    fig, ax = plt.subplots()
                    ax.scatter(df_in[x_col], df_in[y_col], alpha=0.6)
                    ax.set_xlabel(x_label)
                    ax.set_ylabel(y_label)
                    ax.set_title(custom_title)
                    st.pyplot(fig)

            elif chart_type == "Line Chart":
                x_col = st.selectbox("X-axis column:", numeric_cols, key=f"xline_{key_prefix}")
                y_col = st.selectbox("Y-axis column:", numeric_cols, key=f"yline_{key_prefix}")
                x_label = st.text_input("X-axis label:", x_col, key=f"xline_label_{key_prefix}")
                y_label = st.text_input("Y-axis label:", y_col, key=f"yline_label_{key_prefix}")

                fig, ax = plt.subplots()
                ax.plot(df_in[x_col], df_in[y_col], marker="o")
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                ax.set_title(custom_title)
                st.pyplot(fig)


    # render dashboard
    if selected_charts:
        st.subheader("Your Dashboard")
        for i in range(0, len(selected_charts), cols_per_row):
            row_charts = selected_charts[i:i + cols_per_row]
            cols = st.columns(len(row_charts))
            for idx, (col_area, chart) in enumerate(zip(cols, row_charts)):
                with col_area:
                    render_chart(data_for_viz, chart, key_prefix=f"{i}_{idx}")
# ---------------------------
## ---------------------------
# ---------------------------
# ---------------------------
# 📊 Dashboard & Analysis Section
# ---------------------------
st.header("📊 Interactive Dashboard")

# Use cleaned data if available, else raw
data_for_viz = st.session_state.df_clean if st.session_state.df_clean is not None else df

if data_for_viz is None:
    st.info("Upload a file (and optionally clean it) to use the dashboard.")
else:
    # ----- Select Charts -----
    chart_options = ["Histogram", "Boxplot", "Correlation Heatmap", "Scatter Plot", "Line Chart"]
    selected_charts = st.multiselect(
        "Select the charts you want to display:",
        chart_options,
        default=chart_options[:2],
        key="dashboard_selected_charts"
    )

    # layout columns
    cols_per_row = st.slider("Columns per row", 1, 3, 2, key="dashboard_cols_per_row")

    # ---- Chart Renderer ----
    def render_chart(df_in, chart_type, key_prefix=""):
        numeric_cols = df_in.select_dtypes(include="number").columns.tolist()
        if chart_type in ("Histogram", "Boxplot", "Scatter Plot", "Line Chart") and len(numeric_cols) == 0:
            st.warning("No numeric columns found for this chart.")
            return

        # custom title for all charts
        custom_title = st.text_input(
            f"Title for {chart_type}:",
            value=chart_type,
            key=f"title_{key_prefix}_{chart_type}"
        )

        # figure size controls
        fig_w = st.slider("Figure width", 4, 12, 6, key=f"figw_{key_prefix}_{chart_type}")
        fig_h = st.slider("Figure height", 3, 8, 4, key=f"figh_{key_prefix}_{chart_type}")

        if chart_type == "Histogram":
            col = st.selectbox(
                "Select column for Histogram:",
                numeric_cols,
                key=f"hist_col_{key_prefix}"
            )
            bins = st.slider("Bins:", 5, 100, 20, key=f"bins_{key_prefix}")
            x_label = st.text_input("X-axis label:", col, key=f"hist_xlabel_{key_prefix}")
            y_label = st.text_input("Y-axis label:", "Frequency", key=f"hist_ylabel_{key_prefix}")

            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            df_in[col].hist(ax=ax, bins=bins)
            ax.set_title(custom_title)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            st.pyplot(fig)

        elif chart_type == "Boxplot":
            cols = st.multiselect(
                "Select columns for Boxplot:",
                numeric_cols,
                default=numeric_cols[:1],
                key=f"box_cols_{key_prefix}"
            )
            if cols:
                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                sns.boxplot(data=df_in[cols], ax=ax)
                ax.set_title(custom_title)
                st.pyplot(fig)
            else:
                st.info("Select at least one column for the Boxplot.")

        elif chart_type == "Correlation Heatmap":
            if len(numeric_cols) < 2:
                st.info("Need at least two numeric columns for a heatmap.")
            else:
                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                sns.heatmap(df_in.corr(numeric_only=True), cmap="coolwarm", annot=True, ax=ax)
                ax.set_title(custom_title)
                st.pyplot(fig)

        elif chart_type == "Scatter Plot":
            if len(numeric_cols) < 2:
                st.info("Need at least two numeric columns for a scatter plot.")
            else:
                x_col = st.selectbox("X-axis column:", numeric_cols, key=f"xcol_{key_prefix}")
                y_col = st.selectbox("Y-axis column:", numeric_cols, key=f"ycol_{key_prefix}")
                x_label = st.text_input("X-axis label:", x_col, key=f"xlab_{key_prefix}")
                y_label = st.text_input("Y-axis label:", y_col, key=f"ylab_{key_prefix}")

                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                ax.scatter(df_in[x_col], df_in[y_col], alpha=0.6)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                ax.set_title(custom_title)
                st.pyplot(fig)

        elif chart_type == "Line Chart":
            x_col = st.selectbox("X-axis column:", df_in.columns, key=f"line_x_{key_prefix}")
            y_cols = st.multiselect(
                "Y-axis column(s):",
                numeric_cols,
                default=numeric_cols[:1],
                key=f"line_y_{key_prefix}"
            )
            x_label = st.text_input("X-axis label:", x_col, key=f"line_xlab_{key_prefix}")
            y_label = st.text_input("Y-axis label:", ", ".join(y_cols), key=f"line_ylab_{key_prefix}")

            if y_cols:
                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                for y in y_cols:
                    ax.plot(df_in[x_col], df_in[y], label=y)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                ax.set_title(custom_title)
                ax.legend()
                st.pyplot(fig)

    # ---- Render Dashboard ----
    import uuid


    def render_chart(df_in, chart_type, key_prefix=""):
        numeric_cols = df_in.select_dtypes(include="number").columns.tolist()
        if chart_type in ("Histogram", "Boxplot", "Scatter Plot", "Line Chart") and len(numeric_cols) == 0:
            st.warning("No numeric columns found for this chart.")
            return

        # generate a unique suffix
        unique_suffix = str(uuid.uuid4())[:8]

        # custom title for all charts
        custom_title = st.text_input(
            f"Title for {chart_type}:",
            value=chart_type,
            key=f"title_{key_prefix}_{chart_type}_{unique_suffix}"
        )

        # figure size controls
        fig_w = st.slider("Figure width", 4, 12, 6, key=f"figw_{key_prefix}_{chart_type}_{unique_suffix}")
        fig_h = st.slider("Figure height", 3, 8, 4, key=f"figh_{key_prefix}_{chart_type}_{unique_suffix}")

        if chart_type == "Histogram":
            col = st.selectbox(
                "Select column for Histogram:",
                numeric_cols,
                key=f"hist_col_{key_prefix}_{unique_suffix}"
            )
            bins = st.slider("Bins:", 5, 100, 20, key=f"bins_{key_prefix}_{unique_suffix}")
            x_label = st.text_input("X-axis label:", col, key=f"hist_xlabel_{key_prefix}_{unique_suffix}")
            y_label = st.text_input("Y-axis label:", "Frequency", key=f"hist_ylabel_{key_prefix}_{unique_suffix}")

            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            df_in[col].hist(ax=ax, bins=bins)
            ax.set_title(custom_title)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            st.pyplot(fig)

        elif chart_type == "Boxplot":
            cols = st.multiselect(
                "Select columns for Boxplot:",
                numeric_cols,
                default=numeric_cols[:1],
                key=f"box_cols_{key_prefix}_{unique_suffix}"
            )
            if cols:
                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                sns.boxplot(data=df_in[cols], ax=ax)
                ax.set_title(custom_title)
                st.pyplot(fig)

        elif chart_type == "Correlation Heatmap":
            if len(numeric_cols) < 2:
                st.info("Need at least two numeric columns for a heatmap.")
            else:
                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                sns.heatmap(df_in.corr(numeric_only=True), cmap="coolwarm", annot=True, ax=ax)
                ax.set_title(custom_title)
                st.pyplot(fig)

        elif chart_type == "Scatter Plot":
            if len(numeric_cols) < 2:
                st.info("Need at least two numeric columns for a scatter plot.")
            else:
                x_col = st.selectbox("X-axis column:", numeric_cols, key=f"xcol_{key_prefix}_{unique_suffix}")
                y_col = st.selectbox("Y-axis column:", numeric_cols, key=f"ycol_{key_prefix}_{unique_suffix}")
                x_label = st.text_input("X-axis label:", x_col, key=f"xlab_{key_prefix}_{unique_suffix}")
                y_label = st.text_input("Y-axis label:", y_col, key=f"ylab_{key_prefix}_{unique_suffix}")

                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                ax.scatter(df_in[x_col], df_in[y_col], alpha=0.6)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                ax.set_title(custom_title)
                st.pyplot(fig)

        elif chart_type == "Line Chart":
            x_col = st.selectbox("X-axis column:", df_in.columns, key=f"line_x_{key_prefix}_{unique_suffix}")
            y_cols = st.multiselect(
                "Y-axis column(s):",
                numeric_cols,
                default=numeric_cols[:1],
                key=f"line_y_{key_prefix}_{unique_suffix}"
            )
            x_label = st.text_input("X-axis label:", x_col, key=f"line_xlab_{key_prefix}_{unique_suffix}")
            y_label = st.text_input("Y-axis label:", ", ".join(y_cols), key=f"line_ylab_{key_prefix}_{unique_suffix}")

            if y_cols:
                fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                for y in y_cols:
                    ax.plot(df_in[x_col], df_in[y], label=y)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                ax.set_title(custom_title)
                ax.legend()
                st.pyplot(fig)

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
