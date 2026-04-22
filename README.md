# Social-to-Lead Agentic Workflow

An AI-powered conversational agent that converts social media inquiries into qualified leads. Built with **LangGraph** and **Groq (LLaMA 3.1 8B)**, the agent handles the full sales funnel — greeting, product Q&A (via RAG), objection handling, and multi-turn lead capture — in a single stateful conversation.

> **Note on LLM choice:** The initial implementation used the Gemini API, but it was returning errors due to a rate-limit quota being set to zero. To keep development moving, the project was switched to **Groq** (serving LLaMA 3.1 8B), which provides fast, free-tier inference with no quota issues.

---

## Table of Contents

- [How to Run Locally](#how-to-run-locally)
- [Architecture Explanation](#architecture-explanation)
- [WhatsApp Deployment via Webhooks](#whatsapp-deployment-via-webhooks)

---

## How to Run Locally

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/)

### 1. Clone the repository

```bash
git clone https://github.com/sonaladhonde3-debug/Social-to-Lead-Agentic-Workflow.git
cd Social-to-Lead-Agentic-Workflow
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

### 5. (Optional) Rebuild the FAISS index

A pre-built index is included. To rebuild from the knowledge base:

```bash
python rag/build_index.py
```

### 6. Run the agent

**Terminal (CLI):**

```bash
python main.py
```

**Streamlit (Web UI):**

```bash
streamlit run app.py
```

---

## Architecture Explanation

### Why LangGraph?

LangGraph was chosen over frameworks like AutoGen because it provides **explicit, graph-based control flow** that maps naturally to a sales conversion funnel. Each stage of the conversation — greeting, product inquiry, lead capture, objection handling — is a discrete node in a `StateGraph`, making routing logic transparent, debuggable, and easy to extend. Unlike AutoGen's multi-agent chat paradigm (designed for agent-to-agent collaboration), LangGraph's single-agent, multi-step workflow model gives **deterministic, auditable routing** — critical for a lead-capture pipeline where every conversational turn must be intentional.

### How State is Managed

A single `AgentState` (`TypedDict`) flows through every node in the graph. Each node receives the full state, performs its task, and returns **only the fields it modifies** — LangGraph merges partial updates back automatically. Key state fields:

| Field | Purpose |
|---|---|
| `messages` | Full conversation history (user + assistant) |
| `intent` | Classified intent for the current turn |
| `lead_name / email / platform` | Progressively filled lead fields |
| `lead_captured` | Boolean — whether lead has been saved |
| `in_lead_flow` | Lock flag — prevents intent reclassification during multi-turn lead collection |
| `rag_context` | Cached RAG result to avoid redundant retrievals |

The `in_lead_flow` flag is critical: once lead collection starts, the router bypasses intent classification and routes every subsequent message directly to the lead node until all fields are captured, ensuring the multi-turn flow is never interrupted by a misclassification.

### Graph Flow

```
User Input → [classify] → route
                            ├── "greeting"    → [greeting]   → END
                            ├── "inquiry"     → [rag]        → END
                            ├── "high_intent" → [rag → lead] → END
                            ├── "objection"   → [objection]  → END
                            └── (in_lead_flow)→ [lead]       → END
```

---

## Design Decisions

### 1. Agent Reasoning & Intent Detection

Intent classification uses a **two-layer hybrid approach**:

- **Layer 1 — Rule-based matching** (`agent/intent.py → rule_based_intent`): Fast keyword checks catch unambiguous intents (e.g., "hi" → `greeting`, "too expensive" → `objection`) with high confidence and zero latency.
- **Layer 2 — LLM fallback**: If no rule matches, the message is sent to the LLM with a structured prompt that returns `{ intent, confidence }` as JSON. A `safe_json` parser handles malformed outputs gracefully.
- **Fallback**: If the LLM also fails to return valid JSON, the system defaults to `inquiry` (the safest intent — it answers the question without any side effects).

This layered design ensures the agent is both **fast** (rules handle ~70% of messages) and **robust** (LLM catches nuanced cases).

### 2. Correct Use of RAG

The RAG pipeline follows a clean Indexing → Retrieval → Generation pattern:

- **Indexing** (`rag/build_index.py`): The product knowledge base (`rag/knowledge_base.md`) is split by Markdown headers using `MarkdownHeaderTextSplitter`, embedded with `sentence-transformers/all-MiniLM-L6-v2`, and stored as a FAISS index.
- **Retrieval** (`rag/retriever.py`): At query time, the top-3 most relevant chunks are retrieved. The embedder and FAISS index are cached (via `@st.cache_resource` in Streamlit, `@lru_cache` in CLI) to avoid reloading on every turn.
- **Generation** (`agent/rag_response.py`): Retrieved context is injected into a structured prompt with strict guardrails — the LLM is instructed to answer **only** what was asked, avoid hallucination, and keep responses concise (3–6 lines).

RAG is triggered for both `inquiry` and `high_intent` intents. For high-intent users, the agent first provides product information via RAG before initiating lead capture — ensuring the user is informed before being asked for details.

### 3. Clean State Management

- State is defined as a single `AgentState` TypedDict — no scattered globals or hidden side effects.
- Each graph node returns **only the fields it modifies** (partial state updates), keeping node logic focused and side-effect-free.
- The `in_lead_flow` flag acts as a state lock: once the lead collection flow begins, intent reclassification is skipped entirely, preventing the multi-turn flow from being derailed by an ambiguous intermediate message (e.g., a user saying just "YouTube" being misclassified as a greeting).
- `rag_context` is cached in state so that when a `high_intent` user transitions from RAG → lead capture, the retrieval doesn't repeat.

### 4. Proper Tool Calling Logic

The `mock_lead_capture` tool (`agent/tools.py`) simulates a CRM write. It is invoked **only** inside the `lead_node` and **only** after all three required fields (`name`, `email`, `platform`) are validated and present. The tool is never called speculatively — the node checks each field and returns an asking-prompt if any are missing, calling the tool only on the final turn when all data is confirmed. After capture, `lead_captured` is set to `True` and `in_lead_flow` is released, cleanly exiting the lead flow.

### 5. Code Clarity & Structure

```
agent/          → Core agent logic (graph, nodes, state, LLM wrapper)
prompts/        → All LLM prompt templates (separated from logic)
rag/            → RAG pipeline (indexer, retriever, knowledge base)
main.py         → CLI entry point
app.py          → Streamlit UI entry point
```

Design principles:
- **Separation of concerns**: Prompts live in `prompts/`, retrieval logic in `rag/`, agent orchestration in `agent/`. No module does more than one job.
- **Single LLM wrapper** (`agent/llm.py`): All LLM calls go through one function (`call_llm`), making it trivial to swap models, add logging, or introduce retries.
- **Graceful error handling**: Every LLM call is wrapped in try/except with sensible fallbacks — the agent never crashes on a bad API response.

### 6. Real-World Deployability

- **Streamlit UI** (`app.py`) provides an immediate, deployable demo interface.
- **Environment-based config**: API keys are loaded from `.env` via `python-dotenv` — no hardcoded secrets.
- **Stateless agent design**: The `build_graph()` function returns a compiled graph that takes state as input and returns updated state — making it trivially deployable behind any API server (FastAPI, Flask, WhatsApp webhook). No global mutable state inside the agent.
- **Cached resources**: Embeddings and FAISS index are loaded once and cached, avoiding expensive reinitialisation on every request.

---

## WhatsApp Deployment via Webhooks

To deploy this agent on WhatsApp, you would use the **WhatsApp Business API** (via Meta's Cloud API or Twilio) with a webhook-based architecture:

### Architecture

```
WhatsApp User
     │
     ▼
Meta Cloud API / Twilio
     │  (HTTPS POST)
     ▼
Webhook Server (FastAPI / Flask)
     │
     ├── Parse incoming message
     ├── Load/create session state (Redis / DB)
     ├── Invoke LangGraph agent
     ├── Store updated state
     └── Send reply via WhatsApp API
```

### Implementation Steps

1. **Set up a webhook endpoint** — Deploy a FastAPI/Flask server with a publicly accessible URL (e.g., ngrok for dev, AWS/GCP for production). Register this URL as the webhook callback in the Meta Developer Dashboard or Twilio Console.

2. **Verify the webhook** — Meta sends a `GET` request with a verification token. The server responds with the `hub.challenge` value to confirm ownership.

3. **Receive messages** — When a user sends a WhatsApp message, Meta/Twilio delivers a `POST` request containing the sender's phone number and message text.

4. **Session management** — Use the sender's phone number as a session key. Store and retrieve `AgentState` from a persistent store (Redis or a database) so the agent maintains context across messages.

5. **Invoke the agent** — Load the session state, append the new user message, and call `agent.invoke(state)` — exactly as `main.py` does today. No changes to the core agent are needed.

6. **Send the reply** — Extract the assistant's response from the updated state and send it back via the WhatsApp API (`POST /v1/messages`).

7. **Persist state** — Save the updated `AgentState` back to Redis/DB for the next turn.

### Example Webhook (FastAPI)

```python
from fastapi import FastAPI, Request
from agent.graph import build_graph
import redis, json

app = FastAPI()
agent = build_graph()
store = redis.Redis()

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    phone = body["from"]
    user_msg = body["text"]

    # Load or initialize session state
    raw = store.get(phone)
    state = json.loads(raw) if raw else {
        "messages": [], "intent": None,
        "lead_name": None, "lead_email": None,
        "lead_platform": None, "lead_captured": False,
        "awaiting": None, "rag_context": None,
        "in_lead_flow": False
    }

    # Append user message and run agent
    state["messages"].append({"role": "user", "content": user_msg})
    result = agent.invoke(state)
    state.update(result)

    # Persist state and send reply
    store.set(phone, json.dumps(state))
    reply = state["messages"][-1]["content"]
    send_whatsapp_message(phone, reply)  # calls WhatsApp Business API

    return {"status": "ok"}
```

The key takeaway: **no changes to the core agent logic are required**. The same LangGraph graph and state management work identically whether the input comes from a terminal, Streamlit, or a WhatsApp webhook — only the I/O layer changes.
