from openai import OpenAI

def chat_with_groq(messages):
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key="your_key")
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return resp.choices[0].message.content
