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




def show_custom_plot(df):
    st.subheader("🛠️ Custom Chart Builder")

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    chart_type = st.selectbox("📊 Select chart type", ["Scatter Plot", "Line Chart", "Bar Chart", "Pie Chart"])

    if chart_type == "Pie Chart":
        if not categorical_cols or not numeric_cols:
            st.warning("Need at least one categorical and one numerical column for a pie chart.")
            return
        pie_labels = st.selectbox("🧩 Select category for Pie Chart", categorical_cols)
        pie_values = st.selectbox("🔢 Select values for Pie Chart", numeric_cols)

        data = df.groupby(pie_labels)[pie_values].sum().sort_values(ascending=False)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(data.values, labels=data.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig)

    else:
        x_axis = st.selectbox("🧭 Select X-axis", df.columns.tolist())
        y_axis = st.selectbox("📐 Select Y-axis", numeric_cols)
        label_column = st.selectbox("🏷️ Add labels (optional)", ["None"] + categorical_cols)

        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "Scatter Plot":
            sns.scatterplot(data=df, x=x_axis, y=y_axis, ax=ax)
            if label_column != "None":
                for i in range(len(df)):
                    ax.text(df[x_axis].iloc[i], df[y_axis].iloc[i], str(df[label_column].iloc[i]), fontsize=8)

        elif chart_type == "Line Chart":
            sns.lineplot(data=df, x=x_axis, y=y_axis, ax=ax)

        elif chart_type == "Bar Chart":
            sns.barplot(data=df, x=x_axis, y=y_axis, ax=ax)

        # 🔁 Rotate X-axis labels
        plt.xticks(rotation=90)
        ax.set_xlabel(x_axis)
        ax.set_ylabel(y_axis)
        st.pyplot(fig)
