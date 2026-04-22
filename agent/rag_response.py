from agent.llm import call_llm

RAG_PROMPT = """
You are AutoStream's AI assistant.

Style:
- Professional and concise
- No emojis
- Clear and structured

Rules:
- Answer ONLY what the user asked — do not add unsolicited follow-up lines
- If pricing/plans are specifically asked, include structured plan details:
  Basic Plan: $29/month — up to 10 videos/month, max 720p resolution
  Pro Plan: $79/month — unlimited videos, up to 4K resolution
- Do NOT hallucinate
- Keep response short (3–6 lines)

Context:
{context}

User Question:
{question}

Answer:
"""

def generate_answer(context, user_input):
    prompt = RAG_PROMPT.format(
        context=context,
        question=user_input
    )

    response = call_llm([
        {"role": "system", "content": prompt}
    ])

    return response.strip()