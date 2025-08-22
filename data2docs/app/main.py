import os
import streamlit as st
import pandas as pd
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
# ---------------- CONFIG ----------------
# API_URL = "http://127.0.0.1:5000/api"  # Local testing
API_URL = "https://ai-data-reporter.onrender.com/api"  # For deployment

st.set_page_config(page_title="Data2Docs - Vijendra", layout="wide")
st.title("📊 Data2Docs – AI Report Generator (by **Vijendra**)")

# ---------------- SESSION STATE ----------------
for key in ["token", "user", "stats", "insights", "df_clean"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ---------------- HELPERS ----------------
def safe_json(res):
    try:
        return res.json()
    ##
    except Exception:
        return {}


def auto_handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Auto-fill missing values with mode for categorical & median for numeric"""
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


# ---------------- SIDEBAR: LOGIN / SIGNUP ----------------
st.sidebar.title("🔐 Account")

if not st.session_state.token:
    action = st.sidebar.radio("Choose", ["Login", "Sign up"])

    if action == "Sign up":
        with st.sidebar.form("signup"):
            su_username = st.text_input("Username")
            su_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create account")

            if submitted:
                try:
                    res = requests.post(f"{API_URL}/signup", json={
                        "username": su_username,
                        "password": su_password
                    })
                    if res.status_code == 201:
                        st.sidebar.success("✅ Account created! Please log in.")
                    else:
                        st.sidebar.error(safe_json(res).get("error", "Signup failed"))
                except Exception as e:
                    st.sidebar.error(f"❌ Signup failed: {e}")

    else:  # Login
        with st.sidebar.form("login"):
            li_username = st.text_input("Username")
            li_password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button("Login")

            if login_clicked:
                try:
                    res = requests.post(f"{API_URL}/login", json={
                        "username": li_username,
                        "password": li_password
                    })
                    if res.status_code == 200:
                        st.session_state.token = safe_json(res).get("access_token")
                        st.session_state.user = li_username
                        st.sidebar.success(f"✅ Welcome {li_username}!")
                        st.rerun()
                    else:
                        st.sidebar.error(safe_json(res).get("error", "Login failed"))
                except Exception as e:
                    st.sidebar.error(f"❌ Login failed: {e}")

else:
    st.sidebar.markdown(f"👤 **Logged in as:** {st.session_state.user}")
    if st.sidebar.button("Logout"):
        for key in ["token", "user", "stats", "insights", "df_clean"]:
            st.session_state[key] = None
        st.rerun()

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

        # Basic Info
        with st.expander("📌 Basic Information"):
            if st.checkbox("Show Basic Info"):
                show_basic_info(df)

        # Missing Values
        with st.expander("🔎 Missing Values"):
            if st.checkbox("Check Missing Values"):
                show_missing_values(df)

            if st.button("⚡ Auto Handle Missing Values"):
                df_clean = auto_handle_missing(df)
                st.session_state.df_clean = df_clean
                st.success("✅ Missing values handled automatically!")
                st.dataframe(df_clean.head())
                st.download_button(
                    label="📥 Download Cleaned CSV",
                    data=df_clean.to_csv(index=False).encode("utf-8"),
                    file_name="cleaned_data.csv",
                    mime="text/csv"
                )

        # Summary Stats
        with st.expander("📊 Summary Statistics"):
            if st.checkbox("View Summary Stats"):
                show_summary_stats(df)

        # Correlation Heatmap
        with st.expander("🔥 Correlation Heatmap"):
            if st.checkbox("Show Correlation Heatmap"):
                show_correlation_heatmap(df)

        # Custom Plot
        with st.expander("🛠️ Build Custom Plot"):
            if st.checkbox("Create a Custom Chart"):
                show_custom_plot(df)

        # AI Insights
        with st.expander("🧠 Generate AI Insights with Groq"):
            if st.button("Generate Insights"):
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                with st.spinner("🤖 Generating AI insights..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/insights",
                            json={"stats": df.describe(include='all').to_dict()},
                            headers=headers
                        )
                        data = safe_json(res)
                        if res.status_code == 200:
                            st.session_state.insights = data["insights"]
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
                        pdf_path = data.get("pdf_path")
                        if res.status_code == 200 and pdf_path:
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=f,
                                    file_name="data2docs_report.pdf",
                                    mime="application/pdf"
                                )
                        else:
                            st.error(data.get("error", "PDF export failed"))
                    except Exception as e:
                        st.error(f"⚠️ Could not reach backend: {e}")

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
else:
    st.info("👆 Please upload a file to start.")
# ---------------------------
# 📊 Dashboard & Analysis Section
# ---------------------------
st.header("📊 Interactive Dashboard")

# Use cleaned data if available, else raw
data_for_viz = st.session_state.df_clean if st.session_state.df_clean is not None else df

if data_for_viz is None:
    st.info("Upload a file (and optionally clean it) to use the dashboard.")
else:
    # ---------------------------
    # Chart options
    # ---------------------------
    chart_options = [
        "Histogram",
        "Boxplot",
        "Correlation Heatmap",
        "Scatter Plot",
        "Line Chart",
        "Bar Chart (Categorical)",
        "Pie Chart (Categorical)"
    ]

    # ---------------------------
    # Chart rendering function
    # ---------------------------
    def render_chart(df_in, chart_type, key_prefix=""):
        numeric_cols = df_in.select_dtypes(include="number").columns.tolist()
        cat_cols = df_in.select_dtypes(exclude="number").columns.tolist()

        with st.expander(f"📊 {chart_type}"):
            custom_title = st.text_input(
                f"Title for {chart_type}:",
                value=chart_type,
                key=f"title_{key_prefix}_{chart_type}"
            )

            try:
                if chart_type == "Histogram":
                    if not numeric_cols:
                        st.warning("⚠️ No numeric columns available.")
                        return
                    col = st.selectbox("Select column:", numeric_cols, key=f"hist_col_{key_prefix}")
                    bins = st.slider("Bins:", 5, 100, 20, key=f"bins_{key_prefix}")
                    fig, ax = plt.subplots()
                    df_in[col].hist(ax=ax, bins=bins)
                    ax.set_title(custom_title)
                    st.pyplot(fig)

                elif chart_type == "Boxplot":
                    if not numeric_cols:
                        st.warning("⚠️ No numeric columns available.")
                        return
                    cols = st.multiselect("Select columns:", numeric_cols, default=numeric_cols[:1],
                                          key=f"box_cols_{key_prefix}")
                    if cols:
                        fig, ax = plt.subplots()
                        sns.boxplot(data=df_in[cols], ax=ax)
                        ax.set_title(custom_title)
                        st.pyplot(fig)

                elif chart_type == "Correlation Heatmap":
                    if len(numeric_cols) < 2:
                        st.info("ℹ️ Need at least two numeric columns.")
                        return
                    fig, ax = plt.subplots(figsize=(5, 4))
                    sns.heatmap(df_in[numeric_cols].corr(), cmap="coolwarm", annot=True, ax=ax)
                    ax.set_title(custom_title)
                    st.pyplot(fig)

                elif chart_type == "Scatter Plot":
                    if len(numeric_cols) < 2:
                        st.info("ℹ️ Need at least two numeric columns.")
                        return
                    x_col = st.selectbox("X-axis column:", numeric_cols, key=f"xcol_{key_prefix}")
                    y_col = st.selectbox("Y-axis column:", numeric_cols, key=f"ycol_{key_prefix}")
                    fig, ax = plt.subplots()
                    ax.scatter(df_in[x_col], df_in[y_col], alpha=0.6)
                    ax.set_title(custom_title)
                    st.pyplot(fig)

                elif chart_type == "Line Chart":
                    if len(numeric_cols) < 2:
                        st.info("ℹ️ Need at least two numeric columns.")
                        return
                    x_col = st.selectbox("X-axis column:", numeric_cols, key=f"xline_{key_prefix}")
                    y_col = st.selectbox("Y-axis column:", numeric_cols, key=f"yline_{key_prefix}")
                    fig, ax = plt.subplots()
                    ax.plot(df_in[x_col], df_in[y_col], marker="o")
                    ax.set_title(custom_title)
                    st.pyplot(fig)

                elif chart_type == "Bar Chart (Categorical)":
                    if not cat_cols:
                        st.warning("⚠️ No categorical columns available.")
                        return
                    col = st.selectbox("Select column:", cat_cols, key=f"bar_col_{key_prefix}")
                    counts = df_in[col].value_counts().reset_index()
                    counts.columns = [col, "Count"]
                    fig, ax = plt.subplots()
                    sns.barplot(x=col, y="Count", data=counts, ax=ax)
                    ax.set_title(custom_title)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

                elif chart_type == "Pie Chart (Categorical)":
                    if not cat_cols:
                        st.warning("⚠️ No categorical columns available.")
                        return
                    col = st.selectbox("Select column:", cat_cols, key=f"pie_col_{key_prefix}")
                    counts = df_in[col].value_counts()
                    fig, ax = plt.subplots()
                    ax.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90)
                    ax.set_title(custom_title)
                    st.pyplot(fig)

            except Exception as e:
                st.error(f"❌ Error rendering {chart_type}: {e}")

    # ---------------------------
    # Unified Dashboard (AI + Manual)
    # ---------------------------
    st.subheader("📊 Unified Dashboard")

    ai_charts = []
    if st.button("🤖 Get AI Chart Suggestions"):
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        try:
            res = requests.post(
                f"{API_URL}/chat",
                json={
                    "history": [
                        {"role": "system", "content": "You are a data visualization expert."},
                        {"role": "user",
                         "content": f"Suggest the most suitable set of charts for this dataset with columns: {list(data_for_viz.columns)} and dtypes: {data_for_viz.dtypes.astype(str).to_dict()}. Reply ONLY with chart names from this list: {chart_options}"}
                    ]
                },
                headers=headers
            )
            data = safe_json(res)
            if res.status_code == 200:
                suggestion_text = data["reply"]
                st.markdown("### 💡 AI Suggested Charts")
                st.write(suggestion_text)
                ai_charts = [c for c in chart_options if c.lower() in suggestion_text.lower()]
            else:
                st.error(data.get("error", "AI suggestion failed"))
        except Exception as e:
            st.error(f"⚠️ Could not reach backend: {e}")

    # Manual selection
    manual_charts = st.multiselect(
        "👤 Select additional charts to include:",
        chart_options,
        default=chart_options[:2]
    )

    # Merge AI + Manual (unique, ordered)
    all_charts = list(dict.fromkeys(ai_charts + manual_charts))

    # Render
    cols_per_row = st.slider("Columns per row", 1, 3, 2)
    if all_charts:
        for i in range(0, len(all_charts), cols_per_row):
            row_charts = all_charts[i:i + cols_per_row]
            cols = st.columns(len(row_charts))
            for idx, (col_area, chart) in enumerate(zip(cols, row_charts)):
                with col_area:
                    render_chart(data_for_viz, chart, key_prefix=f"merged_{i}_{idx}")

    # ---------------------------
    # AI Insights Section
    # ---------------------------
    st.subheader("🤖 AI Insights")
    if st.button("Generate AI Summary"):
        with st.spinner("Analyzing data..."):
            summary = f"""
            Dataset shape: {data_for_viz.shape}
            Numeric columns: {len(data_for_viz.select_dtypes(include='number').columns)}
            Categorical columns: {len(data_for_viz.select_dtypes(exclude='number').columns)}
            Missing values: {data_for_viz.isna().sum().sum()}
            """
            st.write("**Quick Summary:**")
            st.code(summary)

            if len(data_for_viz.select_dtypes(include='number').columns) > 0:
                desc = data_for_viz.describe().T
                st.write("**Statistical Overview:**")
                st.dataframe(desc)
# ---------------------------
# 🤖 AutoML Section
# ---------------------------
st.header("🤖 AutoML – Automatic Prediction")

if data_for_viz is not None:
    target_col = st.selectbox("🎯 Select target column for prediction:", data_for_viz.columns)

    if target_col:
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
        from sklearn.linear_model import LogisticRegression, LinearRegression
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        import numpy as np
        import pickle

        df_ml = data_for_viz.copy()

        # Encode categorical target if needed
        if df_ml[target_col].dtype == "object":
            le = LabelEncoder()
            df_ml[target_col] = le.fit_transform(df_ml[target_col].astype(str))

        X = df_ml.drop(columns=[target_col])
        y = df_ml[target_col]

        # Handle categorical predictors
        X = pd.get_dummies(X, drop_first=True)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Detect problem type
        problem_type = "classification" if y.nunique() <= 10 and y.dtype != "float" else "regression"
        st.write(f"Detected task: **{problem_type.capitalize()}**")

        results = {}
        best_model = None
        best_score = -np.inf

        if problem_type == "classification":
            models = {
                "Logistic Regression": LogisticRegression(max_iter=1000),
                "Random Forest": RandomForestClassifier()
            }
            for name, model in models.items():
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                acc = accuracy_score(y_test, preds)
                results[name] = acc
                if acc > best_score:
                    best_score = acc
                    best_model = model

            st.subheader("📊 Model Performance")
            st.json(results)
            st.text("Detailed report (best model):")
            st.text(classification_report(y_test, best_model.predict(X_test)))

        else:  # Regression
            models = {
                "Linear Regression": LinearRegression(),
                "Random Forest": RandomForestRegressor()
            }
            for name, model in models.items():
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                rmse = np.sqrt(mean_squared_error(y_test, preds))
                r2 = r2_score(y_test, preds)
                results[name] = {"RMSE": rmse, "R2": r2}
                if r2 > best_score:
                    best_score = r2
                    best_model = model

            st.subheader("📊 Model Performance")
            st.json(results)

        # Save best model
        if best_model:
            with open("best_model.pkl", "wb") as f:
                pickle.dump(best_model, f)
            st.download_button(
                label="📥 Download Best Model",
                data=open("best_model.pkl", "rb").read(),
                file_name="best_model.pkl"
            )

        # AI Explanation of results
        if st.button("💡 Explain Results with AI"):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            res = requests.post(
                f"{API_URL}/chat",
                json={"history": [
                    {"role": "system", "content": "You are a data scientist explaining AutoML results."},
                    {"role": "user", "content": f"Explain these results:\n{results}"}
                ]},
                headers=headers
            )
            data = safe_json(res)
            if res.get("status_code", 200) == 200:
                st.write("### 🤖 AI Explanation")
                st.write(data.get("reply", "No response"))

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
