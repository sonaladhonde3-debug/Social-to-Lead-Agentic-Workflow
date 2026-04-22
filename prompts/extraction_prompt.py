EXTRACT_ALL_PROMPT = """
Extract:
- name
- email
- platform

Return JSON:
{"name": ..., "email": ..., "platform": ...}

Use null if missing.
"""