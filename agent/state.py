from typing import TypedDict, Optional

class AgentState(TypedDict):
    messages: list
    intent: Optional[str]
    lead_name: Optional[str]
    lead_email: Optional[str]
    lead_platform: Optional[str]
    lead_captured: bool
    awaiting: Optional[str]
    rag_context: Optional[str]
    in_lead_flow: bool