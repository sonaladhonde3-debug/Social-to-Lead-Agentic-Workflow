import re

EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

def extract_email(text):
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else None


def is_valid_email(email):
    return re.match(EMAIL_REGEX, email) is not None


import re

def extract_name(text):
    lower = text.lower()

    # allow punctuation after name
    patterns = [
        r"my name is ([a-zA-Z]+)",
        r"i am ([a-zA-Z]+)",
        r"i'm ([a-zA-Z]+)",
        r"this is ([a-zA-Z]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return match.group(1).strip().title()

    # 🔥 handle comma-separated case
    first_part = text.split(",")[0].strip()

    if len(first_part.split()) == 1:
        return first_part.title()

    return None


def extract_platform(text):
    lower = text.lower()

    for p in ["youtube", "instagram", "tiktok"]:
        if p in lower:
            return p

    return None