import json
import re
from agent.llm import call_llm

SYSTEM_PROMPT = """
Classify the user's message into ONE:

- greeting
- inquiry (questions about pricing, plans, features)
- high_intent (clear decision, preference, readiness)
- objection

Return JSON:
{
 "intent": "...",
 "confidence": 0-1
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


def rule_based_intent(user_input: str):
    text = user_input.lower()

    # 🔴 OBJECTION
    if any(p in text for p in [
        "don't want", "not interested", "no thanks",
        "maybe later", "too expensive"
    ]):
        return {"intent": "objection", "confidence": 0.95}

    # 🟡 GREETING
    if any(g in text for g in ["hi", "hello", "hey"]):
        return {"intent": "greeting", "confidence": 0.8}

    # 🔵 INQUIRY (PRIORITY FIX)
    if any(p in text for p in [
        "price", "pricing", "plans", "how much",
        "tell me", "what is", "details", "know about"
    ]):
        return {"intent": "inquiry", "confidence": 0.9}

    # 🟢 HIGH INTENT (ONLY STRONG SIGNALS)
    if any(p in text for p in [
        "i want this", "i will take", "sign me up",
        "this is perfect", "this works for me",
        "i want to try", "i choose"
    ]):
        return {"intent": "high_intent", "confidence": 0.9}

    return None


def classify_intent(user_input, history):

    # STEP 1: rules first
    rule = rule_based_intent(user_input)
    if rule:
        return rule

    # STEP 2: fallback LLM
    response = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ])

    result = safe_json(response)

    if not result:
        return {"intent": "inquiry", "confidence": 0.5}

    return result