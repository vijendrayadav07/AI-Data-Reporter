import os
import streamlit as st
from openai import OpenAI

# Set up Groq endpoint and API key
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets["api_keys"]["groq"]

client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1",  # Groq's endpoint
)

def generate_insights(df):
    try:
        user_message = f"""You are a data analyst AI that explains datasets in simple terms.
Here is a preview of my data:
{df.head().to_string(index=False)}

Please provide insights and observations based on this dataset."""

        response = client.chat.completions.create(
            model="llama3-70b-8192",  # or another model Groq supports
            messages=[
                {"role": "system", "content": "You are a helpful data analysis assistant."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )

        result = response.choices[0].message.content
        st.subheader("🧠 AI-Generated Insights")
        st.markdown(result.strip())

    except Exception as e:
        st.error(f"❌ Failed to generate insights:\n\n{e}")
