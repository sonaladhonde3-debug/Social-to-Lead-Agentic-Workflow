from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.intent import classify_intent
from agent.extraction import extract_all
from agent.rag_response import generate_answer
from rag.retriever import retrieve_context
from agent.tools import mock_lead_capture
from agent.llm import call_llm


# 🔹 NODE 1: Intent classification
def classify_node(state: AgentState):
    user_input = state["messages"][-1]["content"]

    # 🔥 DO NOT reclassify during lead flow
    if state.get("in_lead_flow"):
        return {"intent": state.get("intent")}

    intent_obj = classify_intent(user_input, state["messages"])
    return {"intent": intent_obj["intent"]}

# 🔹 NODE 2: Greeting response
def greeting_node(state: AgentState):
    user_input = state["messages"][-1]["content"].lower()

    # 🔥 Handle thanks / gratitude
    if any(word in user_input for word in ["thanks", "thank you", "thx"]):
        reply = "You're welcome. Let me know if you need any further assistance."

    # 🔥 Handle goodbye
    elif any(word in user_input for word in ["bye", "goodbye", "see you"]):
        reply = "Goodbye. Feel free to reach out anytime."

    # 🔥 Default greeting
    else:
        reply = "Hello. How can I assist you today?"

    return {
        "messages": state["messages"] + [{
            "role": "assistant",
            "content": reply
        }]
    }

# 🔹 NODE 3: RAG retrieval + response (with soft conversion)
def rag_node(state: AgentState):
    user_input = state["messages"][-1]["content"]

    context = retrieve_context(user_input)
    answer = generate_answer(context, user_input)

    return {
        "rag_context": context,
        "messages": state["messages"] + [{
            "role": "assistant",
            "content": answer
        }]
    }


# 🔹 NODE 4: Objection handling (improved)
def objection_node(state: AgentState):
    user_input = state["messages"][-1]["content"]

    prompt = f"""
You are a professional sales assistant.

Respond to a hesitant user in a polite and helpful way.

Guidelines:
- Acknowledge concern
- Do not be pushy
- Offer a helpful suggestion
- Keep response short (2–3 lines)

User message:
{user_input}

Response:
"""

    response = call_llm([
        {"role": "system", "content": prompt}
    ])

    return {
        "messages": state["messages"] + [{
            "role": "assistant",
            "content": response.strip()
        }]
    }


# 🔹 NODE 5: Lead handling
def lead_node(state: AgentState):
    user_input = state["messages"][-1]["content"]
    extracted = extract_all(user_input)

    updated_state = dict(state)

    # 🔥 activate lead flow
    updated_state["in_lead_flow"] = True

    # fill extracted fields
    if extracted.get("name") and not updated_state.get("lead_name"):
        updated_state["lead_name"] = extracted["name"]

    if extracted.get("email") and not updated_state.get("lead_email"):
        updated_state["lead_email"] = extracted["email"]

    if extracted.get("platform") and not updated_state.get("lead_platform"):
        updated_state["lead_platform"] = extracted["platform"]

    # ask missing fields
    if not updated_state.get("lead_name"):
        return {
            **updated_state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": "Could you please share your name?"
            }]
        }

    if not updated_state.get("lead_email"):
        return {
            **updated_state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": "Could you provide your email address?"
            }]
        }

    if not updated_state.get("lead_platform"):
        return {
            **updated_state,
            "messages": state["messages"] + [{
                "role": "assistant",
                "content": "Which platform do you primarily create content on? (e.g., YouTube, Instagram)"
            }]
        }

    # 🔥 capture lead
    if not updated_state.get("lead_captured"):
        mock_lead_capture(
            updated_state["lead_name"],
            updated_state["lead_email"],
            updated_state["lead_platform"]
        )
        updated_state["lead_captured"] = True
        updated_state["in_lead_flow"] = False

    return {
        **updated_state,
        "messages": state["messages"] + [{
            "role": "assistant",
            "content": f"Thank you, {updated_state['lead_name']}. Your details have been recorded successfully."
        }]
    }


# 🔹 ROUTER (FINAL SMART FLOW)
def route(state):

    # 🔥 Continue lead flow if active
    if state.get("in_lead_flow"):
        return "lead"

    intent = state["intent"]

    if intent == "greeting":
        return "greeting"

    elif intent == "inquiry":
        return "rag"

    elif intent == "high_intent":
        # 🔥 CRITICAL: ensure info is given before capture
        if not state.get("rag_context"):
            return "rag"
        return "lead"

    elif intent == "objection":
        return "objection"


# 🔥 BUILD GRAPH
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("greeting", greeting_node)
    graph.add_node("rag", rag_node)
    graph.add_node("lead", lead_node)
    graph.add_node("objection", objection_node)

    graph.set_entry_point("classify")

    graph.add_conditional_edges("classify", route)

    graph.add_edge("greeting", END)
    graph.add_edge("rag", END)
    graph.add_edge("lead", END)
    graph.add_edge("objection", END)

    return graph.compile()