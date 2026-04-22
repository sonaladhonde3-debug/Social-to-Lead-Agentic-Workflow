import json
import re
from agent.llm import call_llm

PROMPT = """
Extract the following from the user message:

- name
- email
- platform (YouTube, Instagram, TikTok)

Rules:
- If not present → null
- Only return JSON
- Do NOT guess values

Return format:
{
 "name": "...",
 "email": "...",
 "platform": "..."
}
"""

def safe_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None
    return None


def extract_all(message):
    response = call_llm([
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": message}
    ])

    data = safe_json(response)

    if not data:
        return {"name": None, "email": None, "platform": None}

    # 🔥 CLEAN NAME
    if data.get("name"):
        data["name"] = data["name"].strip().title()

    # 🔥 VALIDATE EMAIL
    if data.get("email"):
        if "@" not in data["email"]:
            data["email"] = None

    # 🔥 VALIDATE PLATFORM (CRITICAL FIX)
    valid_platforms = ["youtube", "instagram", "tiktok"]

    if data.get("platform"):
        if data["platform"].lower() not in valid_platforms:
            data["platform"] = None
        else:
            data["platform"] = data["platform"].lower()

    return data