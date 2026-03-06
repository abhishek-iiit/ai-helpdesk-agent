"""
graph/state.py
==============
LangGraph State Definition

Workshop Note:
    State is the HEART of LangGraph. Every node reads from and writes to
    this shared state object. Think of it as the "memory" that flows
    through the entire workflow graph.

    The Annotated[list, add_messages] pattern tells LangGraph to
    APPEND messages rather than REPLACE them — building conversation history.
"""

from typing import Optional
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class HelpdeskState(TypedDict):
    """
    Shared state that flows through every node in the LangGraph workflow.

    ┌─────────────────────────────────────────────────────┐
    │                  HelpdeskState                       │
    ├─────────────────┬───────────────────────────────────┤
    │ messages        │ Full conversation history          │
    │ question        │ Current user question              │
    │ intent          │ Classified intent category         │
    │ entities        │ Extracted entities (service, etc.) │
    │ tool_output     │ Result from tool execution         │
    │ ticket_id       │ Created ticket ID (if any)         │
    │ final_answer    │ Response to send to user           │
    │ trace_metadata  │ Observability context              │
    └─────────────────┴───────────────────────────────────┘
    """

    # Conversation history — add_messages APPENDS instead of replacing
    messages: Annotated[list[BaseMessage], add_messages]

    # Current user question
    question: str

    # Intent classification result
    # Values: "knowledge_base" | "service_status" | "create_ticket" | "escalate" | "general"
    intent: str

    # Extracted entities from the question
    # e.g., {"service": "VPN", "user_email": "john@company.com"}
    entities: dict

    # Raw output from the executed tool
    tool_output: str

    # Ticket ID if a ticket was created
    ticket_id: Optional[str]

    # Final synthesized answer for the user
    final_answer: str

    # Metadata for tracing (LangSmith / LangFuse)
    trace_metadata: dict


# ─────────────────────────────────────────────────────────────
# Intent Categories
# ─────────────────────────────────────────────────────────────
class Intent:
    """
    Possible intent classifications.

    Workshop Note:
        These map directly to routing decisions in the LangGraph
        conditional edge. Each intent routes to a different tool node.
    """
    KNOWLEDGE_BASE = "knowledge_base"    # → search_knowledge_base tool
    SERVICE_STATUS = "service_status"    # → check_service_status tool
    CREATE_TICKET = "create_ticket"      # → create_support_ticket tool
    ESCALATE = "escalate"               # → escalate to human agent
    GENERAL = "general"                 # → direct LLM answer (no tool)


def initial_state(question: str, user_email: str = "user@company.com") -> dict:
    """
    Create the initial state for a new conversation turn.

    Args:
        question: The user's input question
        user_email: The user's email for ticket creation

    Returns:
        Initial state dict to pass to the compiled graph
    """
    return {
        "messages": [],
        "question": question,
        "intent": "",
        "entities": {"user_email": user_email},
        "tool_output": "",
        "ticket_id": None,
        "final_answer": "",
        "trace_metadata": {
            "user_email": user_email,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        },
    }
