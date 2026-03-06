# 🤖 AI IT Helpdesk Agent — Workshop Project

> **Built with:** LangChain · LangGraph · LangSmith · LangFuse · FastAPI

A production-quality AI support agent that demonstrates how modern AI applications are architected using the LangChain ecosystem. Perfect for developer workshops and team demos.

---

## 🏗️ System Architecture

```
User Question
      ↓
┌─────────────────────────────────────────────────────────┐
│                  LangGraph Workflow                      │
│                                                         │
│  START → [classify_intent] → (conditional routing)      │
│               ↓ (LLM classifies intent)                 │
│   ┌───────────┬──────────┬───────────┬──────────┐       │
│   │knowledge  │service   │create     │escalate  │       │
│   │_base      │_status   │_ticket    │          │       │
│   └─────┬─────┴────┬─────┴─────┬─────┴────┬─────┘       │
│         └──────────┴───────────┴──────────┘             │
│                          ↓                              │
│              [generate_response] → END                  │
│                          ↓                              │
│          LangSmith Trace + LangFuse Analytics           │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
WorkshopProject/
├── main.py                          # 🚀 Entry point (CLI, Demo, API)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
├── setup.sh                         # One-command setup script
│
├── config/
│   └── settings.py                  # Centralized configuration
│
├── tools/                           # LangChain Tools (@tool decorator)
│   ├── knowledge_base.py            # Search IT policies & procedures
│   ├── service_status.py            # Check IT service health
│   └── ticket_system.py             # Create support tickets
│
├── graph/                           # LangGraph Workflow
│   ├── state.py                     # Shared state (HelpdeskState TypedDict)
│   ├── nodes.py                     # Node functions (each step in workflow)
│   └── workflow.py                  # Graph assembly & compilation
│
├── agent/                           # Agent Orchestration
│   ├── prompts.py                   # Prompt templates (intent, response)
│   └── helpdesk_agent.py            # Main HelpdeskAgent class
│
├── observability/                   # Tracing & Analytics
│   ├── langsmith_tracer.py          # LangSmith developer debugging
│   └── langfuse_tracer.py           # LangFuse production analytics
│
├── api/
│   └── app.py                       # FastAPI REST endpoints
│
└── demo/
    └── workshop_demo.py             # 5 interactive workshop scenarios
```

---

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and enter the project
cd WorkshopProject

# Run the setup script (creates venv, installs deps, creates .env)
./setup.sh
```

### 2. Configure Environment

```bash
# Edit .env with your API keys
nano .env
```

```env
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional: LangSmith (developer tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=IT-Helpdesk-Workshop

# Optional: LangFuse (production analytics)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Run

```bash
source .venv/bin/activate

# Interactive chat
python main.py

# Full workshop demo (5 scenarios)
python main.py --demo

# Demo without pauses (auto-run)
python main.py --demo --auto

# Specific scenarios
python main.py --scenario 1,3,5

# REST API server
python main.py --api

# Single question
python main.py --ask "How do I reset my password?"
```

---

## 🛠️ What Each Technology Does

### ⛓ LangChain — Orchestration Layer

LangChain handles prompt templates, LLM calls, and tool definitions.

**Tool Definition (the `@tool` decorator):**
```python
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """Search the IT knowledge base for policies and procedures."""
    # In production: vector DB similarity search
    return "Password reset: Go to https://reset.company.com..."

@tool
def check_service_status(service: str) -> str:
    """Check the operational status of IT services."""
    return "VPN: ✅ Operational (uptime: 99.9%)"

@tool
def create_support_ticket(issue: str, user_email: str) -> str:
    """Create a support ticket in Jira/ServiceNow."""
    return "✅ Ticket INC-421 created — P2 High priority"
```

**Prompt Templates:**
```python
from langchain_core.prompts import ChatPromptTemplate

intent_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify the IT helpdesk query into: knowledge_base, service_status, create_ticket, escalate, general"),
    ("human", "{question}")
])
```

---

### ◈ LangGraph — Workflow Engine

LangGraph defines **deterministic, stateful** agent execution using a directed graph.

**State (the "memory" of the workflow):**
```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

class HelpdeskState(TypedDict):
    messages: Annotated[list, add_messages]  # conversation history
    question: str           # user's question
    intent: str             # classified intent
    entities: dict          # extracted entities (service name, etc.)
    tool_output: str        # result from tool execution
    ticket_id: str | None   # created ticket ID
    final_answer: str       # response to user
```

**Graph Construction:**
```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(HelpdeskState)

# Add nodes
graph.add_node("classify_intent", classify_intent_node)
graph.add_node("knowledge_base_node", knowledge_base_node)
graph.add_node("generate_response", generate_response_node)

# Add edges
graph.add_edge(START, "classify_intent")
graph.add_conditional_edges("classify_intent", route_intent, {
    "knowledge_base_node": "knowledge_base_node",
    "service_status_node": "service_status_node",
    "create_ticket_node":  "create_ticket_node",
})
graph.add_edge("knowledge_base_node", "generate_response")
graph.add_edge("generate_response", END)

compiled = graph.compile()
```

---

### 🔍 LangSmith — Developer Debugging

LangSmith provides **automatic tracing** of every LLM call in your application.

**Setup (just environment variables):**
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=IT-Helpdesk-Workshop
```

**What you see in the LangSmith dashboard:**
```
Run: "Helpdesk: My VPN is not working"
├── classify_intent (LLM)
│   ├── Input:  "My VPN is not working"
│   ├── Prompt: [system: classify intent...] [human: {question}]
│   ├── Output: {"intent": "service_status", "entities": {"service": "VPN"}}
│   └── Tokens: 245 input, 48 output | Latency: 0.8s
├── service_status_node (Tool)
│   ├── Input:  {"service": "VPN"}
│   └── Output: "✅ VPN Operational — uptime 99.9%"
└── generate_response (LLM)
    ├── Input:  question + tool_output
    ├── Output: "Your VPN is currently working fine..."
    └── Tokens: 312 input, 89 output | Latency: 1.2s
```

**Total latency:** 2.1s | **Total tokens:** 694 | **Cost:** ~$0.0002

> 💡 **LangSmith = Developer tool** for debugging and prompt iteration

---

### 📊 LangFuse — Production Analytics

LangFuse provides **production-grade observability** with cost monitoring and analytics.

**Setup (callback-based):**
```python
from langfuse.callback import CallbackHandler

handler = CallbackHandler(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    user_id="john@company.com",
    session_id="session-123",
    tags=["production", "it-helpdesk"],
)

# Pass to LangChain/LangGraph
graph.invoke(state, config={"callbacks": [handler]})
```

**LangFuse Dashboard shows:**
- 💰 Cost per conversation (token usage × model price)
- ⏱️ Latency percentiles (p50, p95, p99)
- 📈 Usage trends over time
- 👤 Per-user analytics
- 🏷️ Prompt version performance comparison

**Key Difference:**

| | LangSmith | LangFuse |
|---|---|---|
| **Primary Use** | Developer debugging | Production monitoring |
| **Best For** | Prompt iteration, debugging | Cost control, business metrics |
| **Tracing** | Automatic (env vars) | Callback-based |
| **Analytics** | Run-level detail | Aggregate dashboards |
| **Audience** | Engineers | Engineers + Management |

---

## 🎭 Demo Scenarios

| # | Scenario | Intent | Demonstrates |
|---|---|---|---|
| 1 | "How do I reset my password?" | `knowledge_base` | Tool use, KB search |
| 2 | "Is the email server working?" | `service_status` | Entity extraction, service check |
| 3 | "My laptop is broken, create a ticket" | `create_ticket` | Tool side effects, ticket creation |
| 4 | "VPN keeps disconnecting — is there an outage?" | `service_status` | Compound reasoning |
| 5 | "I think my account was compromised!" | `escalate` | Critical path, P1 ticket |

---

## 🌐 API Endpoints

Start the API: `python main.py --api`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/status` | Integration status |
| POST | `/chat` | Main chat endpoint |
| POST | `/chat/stream` | Streaming chat (SSE) |
| GET | `/tickets` | List all tickets |
| GET | `/tickets/{id}` | Get ticket by ID |
| GET | `/services` | All service statuses |
| GET | `/graph/info` | Graph topology |

**Swagger UI:** http://localhost:8000/docs

**Example cURL:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "My VPN is not working", "user_email": "john@company.com"}'
```

---

## 🔧 Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| LangChain | ≥0.3.0 | LLM orchestration & tools |
| LangGraph | ≥0.2.0 | Stateful workflow engine |
| LangSmith | ≥0.1.0 | Developer debugging |
| LangFuse | ≥2.0.0 | Production analytics |
| OpenAI | ≥1.0.0 | LLM provider (GPT-4o-mini) |
| FastAPI | ≥0.104.0 | REST API |
| Rich | ≥13.7.0 | Terminal UI |

---

## 📝 License

MIT — Free to use and modify for workshops and demonstrations.
