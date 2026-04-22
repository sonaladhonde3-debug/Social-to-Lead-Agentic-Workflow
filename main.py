from agent.graph import build_graph
from agent.state import AgentState
import time


# Toggle debug (ON for demo, OFF for submission)
DEBUG = False

print("AutoStream AI Agent Ready (type 'exit' to quit)")

agent = build_graph()

# Function to initialize/reset state
def init_state():
    return {
        "messages": [],
        "intent": None,
        "lead_name": None,
        "lead_email": None,
        "lead_platform": None,
        "lead_captured": False,
        "awaiting": None,
        "rag_context": None,
        "in_lead_flow": False
    }

state: AgentState = init_state()

while True:
    user_input = input("\nYou: ").strip()

    # Exit condition
    if user_input.lower() in ["exit", "quit"]:
        print("Bot: Goodbye")
        break

    # Reset conversation
    if user_input.lower() in ["reset", "start over"]:
        state = init_state()
        print("Bot: Conversation reset")
        continue

    # Ignore empty input
    if not user_input:
        continue

    # Add user message
    state["messages"].append({
        "role": "user",
        "content": user_input
    })

    # Latency tracking
    start = time.time()

    # Run agent with error handling
    try:
        result = agent.invoke(state)
    except Exception as e:
        print("Error:", str(e))
        print("Bot: Something went wrong. Please try again.")
        continue

    end = time.time()

    # Update state safely
    if result:
        state.update(result)

    # Print bot response
    print(f"\nBot: {state['messages'][-1]['content']}")

    # Debug info
    if DEBUG:
        print(f"\nLatency: {round(end - start, 2)}s")
        print("\n[STATE DEBUG]:", {
            "intent": state.get("intent"),
            "name": state.get("lead_name"),
            "email": state.get("lead_email"),
            "platform": state.get("lead_platform"),
            "captured": state.get("lead_captured"),
            "in_lead_flow": state.get("in_lead_flow")
        })