import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.1-8b-instant"


def call_llm(messages, temperature=0):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Groq Error:", str(e))
        return "I'm currently unable to process that request. Please try again shortly."