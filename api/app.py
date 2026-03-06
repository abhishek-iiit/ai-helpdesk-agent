"""
api/app.py
==========
FastAPI REST API for the AI IT Helpdesk Agent

Workshop Note:
    FastAPI provides a production-ready HTTP layer on top of our
    LangGraph agent. It includes:
    - Automatic OpenAPI/Swagger documentation at /docs
    - Request/response validation via Pydantic
    - Async support for high concurrency
    - CORS support for web frontends

    API Endpoints:
    ┌─────────────────────────────────────────────────────┐
    │  GET  /               → Health check                │
    │  GET  /status         → Integration status          │
    │  POST /chat           → Main chat endpoint          │
    │  POST /chat/stream    → Streaming chat endpoint     │
    │  GET  /tickets        → List all tickets            │
    │  GET  /tickets/{id}   → Get specific ticket         │
    │  GET  /services       → List service statuses       │
    │  GET  /graph/info     → Graph node info             │
    └─────────────────────────────────────────────────────┘
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json

from config.settings import settings
from agent.helpdesk_agent import HelpdeskAgent
from tools.ticket_system import get_all_tickets, get_ticket_by_id
from tools.service_status import get_all_services_status

# ─────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI IT Helpdesk Agent",
    description=(
        "An intelligent IT support assistant powered by LangChain + LangGraph. "
        "Demonstrates tool use, workflow orchestration, and observability "
        "with LangSmith and LangFuse."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for workshop demos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level agent instance
agent = HelpdeskAgent()


# ─────────────────────────────────────────────────────────────
# Pydantic Request/Response Models
# ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's IT support question", min_length=1)
    user_email: str = Field("user@company.com", description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "My VPN is not working, can you help?",
                "user_email": "john.doe@company.com",
            }
        }


class ChatResponse(BaseModel):
    answer: str
    intent: str
    ticket_id: Optional[str]
    latency_ms: int
    trace_url: Optional[str]
    langfuse_trace_id: Optional[str]


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/status", tags=["Health"])
async def get_status():
    """
    Returns integration status for all observability tools.

    Workshop Note:
        Use this to verify LangSmith and LangFuse are connected.
    """
    return {
        "integrations": settings.status_report(),
        "langsmith_dashboard": "https://smith.langchain.com" if settings.langsmith_enabled else None,
        "langfuse_dashboard": settings.LANGFUSE_HOST if settings.langfuse_enabled else None,
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main chat endpoint — processes a question through the LangGraph workflow.

    Flow:
    1. Classify intent (LLM call)
    2. Route to appropriate tool
    3. Execute tool
    4. Generate response (LLM call)
    5. Return answer with observability metadata

    Workshop Note:
        Try these example questions:
        - "How do I reset my password?"
        - "Is the VPN working?"
        - "My laptop won't turn on, please create a ticket"
        - "We have a security breach!" (triggers escalation)
    """
    try:
        result = agent.ask(
            question=request.question,
            user_email=request.user_email,
            verbose=False,  # Don't print to console in API mode
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint — yields state updates as the graph executes.

    Workshop Note:
        Use this to show users real-time progress:
        "Classifying your question..." → "Checking VPN status..." → "Generating response..."
    """
    def event_stream():
        try:
            for update in agent.stream(
                question=request.question,
                user_email=request.user_email,
            ):
                yield f"data: {json.dumps(update)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/tickets", tags=["Tickets"])
async def list_tickets():
    """
    List all support tickets created during this session.

    Workshop Note:
        Every time a user's issue triggers ticket creation,
        it appears here. Demonstrates the tool's side effects.
    """
    tickets = get_all_tickets()
    return {
        "count": len(tickets),
        "tickets": tickets,
    }


@app.get("/tickets/{ticket_id}", tags=["Tickets"])
async def get_ticket(ticket_id: str):
    """Get details for a specific support ticket."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@app.get("/services", tags=["Services"])
async def list_services():
    """
    List status of all monitored IT services.

    Workshop Note:
        This is the data the service_status tool queries.
        You can see operational vs degraded vs maintenance states.
    """
    services = get_all_services_status()
    summary = {
        "operational": sum(1 for s in services if s["status"] == "operational"),
        "degraded": sum(1 for s in services if s["status"] == "degraded"),
        "outage": sum(1 for s in services if s["status"] == "outage"),
        "maintenance": sum(1 for s in services if s["status"] == "maintenance"),
    }
    return {"summary": summary, "services": services}


@app.get("/graph/info", tags=["Graph"])
async def graph_info():
    """
    Return information about the LangGraph workflow structure.

    Workshop Note:
        Use this to understand the graph topology without running it.
    """
    return {
        "graph_name": "IT Helpdesk Workflow",
        "nodes": [
            {"name": "classify_intent", "type": "LLM", "description": "Classify user intent and extract entities"},
            {"name": "knowledge_base_node", "type": "Tool", "description": "Search IT knowledge base"},
            {"name": "service_status_node", "type": "Tool", "description": "Check service operational status"},
            {"name": "create_ticket_node", "type": "Tool", "description": "Create Jira support ticket"},
            {"name": "escalate_node", "type": "Tool+LLM", "description": "Escalate critical issues to on-call"},
            {"name": "generate_response", "type": "LLM", "description": "Synthesize final user response"},
        ],
        "edges": [
            {"from": "START", "to": "classify_intent", "type": "direct"},
            {"from": "classify_intent", "to": "knowledge_base_node", "type": "conditional", "condition": "intent=knowledge_base"},
            {"from": "classify_intent", "to": "service_status_node", "type": "conditional", "condition": "intent=service_status"},
            {"from": "classify_intent", "to": "create_ticket_node", "type": "conditional", "condition": "intent=create_ticket"},
            {"from": "classify_intent", "to": "escalate_node", "type": "conditional", "condition": "intent=escalate"},
            {"from": "classify_intent", "to": "generate_response", "type": "conditional", "condition": "intent=general"},
            {"from": "knowledge_base_node", "to": "generate_response", "type": "direct"},
            {"from": "service_status_node", "to": "generate_response", "type": "direct"},
            {"from": "create_ticket_node", "to": "generate_response", "type": "direct"},
            {"from": "escalate_node", "to": "generate_response", "type": "direct"},
            {"from": "generate_response", "to": "END", "type": "direct"},
        ],
        "intents": ["knowledge_base", "service_status", "create_ticket", "escalate", "general"],
    }
