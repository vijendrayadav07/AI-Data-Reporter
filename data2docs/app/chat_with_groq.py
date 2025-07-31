from openai import OpenAI
import os
import streamlit as st

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY") or st.secrets["api_keys"]["groq"],
    base_url="https://api.groq.com/openai/v1",
)

def chat_with_groq(messages, model="llama3-70b-8192"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"
