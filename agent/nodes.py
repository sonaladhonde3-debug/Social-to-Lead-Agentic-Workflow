from agent.tools import mock_lead_capture

def classify_intent_node(state, intent_obj):
    state["intent"] = intent_obj.intent
    return state


def respond_greeting_node(state):
    return "Hey! How can I help you?"


def respond_with_kb_node(state, context):
    return f"Here’s what I found:\n{context}"


def lead_collection_node(state, extracted):
    if extracted.get("name") and not state["lead_name"]:
        state["lead_name"] = extracted["name"]

    if extracted.get("email") and not state["lead_email"]:
        state["lead_email"] = extracted["email"]

    if extracted.get("platform") and not state["lead_platform"]:
        state["lead_platform"] = extracted["platform"]

    if not state["lead_name"]:
        return "What's your name?"

    if not state["lead_email"]:
        return "What's your email?"

    if not state["lead_platform"]:
        return "Which platform do you create on?"

    mock_lead_capture(
        state["lead_name"],
        state["lead_email"],
        state["lead_platform"]
    )

    state["lead_captured"] = True
    return f"You're all set, {state['lead_name']} 🚀"