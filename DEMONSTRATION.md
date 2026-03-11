# 🤖 AI IT Helpdesk Agent — Complete Project Demonstration

> A production-quality AI support agent built with **LangChain**, **LangGraph**, and full observability via **LangSmith** & **LangFuse**.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Architecture & Data Flow](#3-architecture--data-flow)
4. [Component-by-Component Breakdown](#4-component-by-component-breakdown)
5. [Technologies Used](#5-technologies-used)
6. [Environment Configuration](#6-environment-configuration)
7. [How to Run](#7-how-to-run)
8. [Example Execution Walkthrough](#8-example-execution-walkthrough)
9. [Key Concepts & Patterns](#9-key-concepts--patterns)
10. [Security Notes](#10-security-notes)

---

## 1. Project Overview

**ARIA (AI IT Helpdesk Agent)** is an intelligent IT support assistant that can:

| User Action | ARIA Response |
|---|---|
| Ask a policy question | Searches a knowledge base and explains procedures |
| Report a service issue | Checks real-time service status |
| Request a support ticket | Creates a categorised ticket with SLA |
| Report a security incident | Escalates to a P1 critical incident |
| Ask a general question | Responds directly via LLM |

**Primary Goal:** Serve as a workshop/education project demonstrating how to build intelligent agents with LangChain, LangGraph, and production observability tools.

**Total Code:** ~2,500 lines across 14 Python modules.

---

## 2. Project Structure

```
AI-Helpdesk-Agent/
│
├── main.py                  # CLI entry point — 4 run modes
├── requirements.txt         # Python dependencies
├── setup.sh                 # One-command environment setup
├── .env.example             # Template for API keys / config
├── README.md                # Official documentation
│
├── config/                  # ── Centralised Configuration
│   ├── settings.py          #    Env var loading + helper properties
│   └── __init__.py
│
├── agent/                   # ── High-Level Agent Interface
│   ├── helpdesk_agent.py    #    HelpdeskAgent class (main orchestrator)
│   ├── prompts.py           #    All ChatPromptTemplate definitions
│   └── __init__.py
│
├── graph/                   # ── LangGraph Workflow Engine
│   ├── state.py             #    HelpdeskState TypedDict + Intent enum
│   ├── nodes.py             #    6 node functions (the actual logic)
│   ├── workflow.py          #    Graph assembly and compilation
│   └── __init__.py
│
├── tools/                   # ── LangChain Tools (mock data)
│   ├── knowledge_base.py    #    10-category KB with keyword search
│   ├── service_status.py    #    12-service status monitor
│   ├── ticket_system.py     #    In-memory ticket store + auto-triage
│   └── __init__.py
│
├── observability/           # ── Tracing & Analytics
│   ├── langsmith_tracer.py  #    Developer tracing (LangSmith)
│   ├── langfuse_tracer.py   #    Production analytics (LangFuse)
│   └── __init__.py
│
├── api/                     # ── REST API Layer
│   └── app.py               #    FastAPI app with 8 endpoints
│
└── demo/                    # ── Workshop Demo Runner
    ├── workshop_demo.py     #    5 interactive scenarios
    └── __init__.py
```

---

## 3. Architecture & Data Flow

### High-Level System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│              "How do I reset my password?"                       │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                 main.py  (Entry Point)                           │
│  • Parses CLI args (--demo, --api, --ask, --scenario, --status)  │
│  • Instantiates HelpdeskAgent                                    │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│          agent/helpdesk_agent.py  (HelpdeskAgent)                │
│  • Builds initial HelpdeskState                                  │
│  • Attaches observability callbacks                              │
│  • Invokes the compiled LangGraph                                │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│            graph/workflow.py  (LangGraph StateGraph)             │
│                                                                  │
│  START ──► classify_intent ──► (conditional routing)            │
│                  │  LLM decides which branch                     │
│     ┌────────────┼─────────────┬────────────┬─────────┐         │
│     ▼            ▼             ▼            ▼         ▼         │
│  KB node   Status node  Ticket node  Escalate   (general)       │
│     └────────────┬─────────────┘────────────┘         │         │
│                  ▼                                     │         │
│          generate_response ◄───────────────────────────┘         │
│                  │  LLM synthesises final answer                 │
│                  ▼                                               │
│                END                                               │
└─────────────────────────┬────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    LangSmith         LangFuse       Console / API
    (Dev traces)   (Prod analytics)  (User response)
```

### State Object — How Data Flows Between Nodes

Every node reads from and writes updates back to a shared `HelpdeskState` dictionary:

```
Initial State
  └─ question: "Is the email server working?"

After classify_intent_node
  ├─ intent:    "service_status"
  └─ entities:  {"service": "email", "urgency": "normal"}

After service_status_node
  └─ tool_output: "⚠️ Email — DEGRADED\n• Incident: Slow delivery..."

After generate_response_node
  └─ final_answer: "Your email service is currently experiencing issues..."

Returned to User
  └─ answer, intent, ticket_id, latency_ms, trace_url
```

---

## 4. Component-by-Component Breakdown

---

### 4.1 `main.py` — Entry Point

**Role:** CLI interface and application launcher. Parses arguments and routes to the correct run mode.

**Run Modes:**

| Flag | Mode | Description |
|---|---|---|
| *(none)* | Interactive CLI | REPL loop — type questions, get answers |
| `--demo` | Workshop demo | Runs 5 pre-built scenarios with explanations |
| `--demo --auto` | Auto demo | Same with no manual pauses |
| `--scenario 1,3,5` | Specific scenarios | Run selected scenario numbers only |
| `--ask "..."` | Single question | One-shot question then exit |
| `--api` | REST server | Start FastAPI on port 8000 |
| `--status` | Status check | Print which integrations are active |

**Key Logic:**
- Calls `settings.status_report()` to detect active integrations at startup
- All question processing is delegated to `HelpdeskAgent`
- Interactive loop handles `exit` / `quit` / `q` to terminate

---

### 4.2 `config/` — Configuration Management

#### `config/settings.py`

**Role:** Single source of truth for all environment variables. Loaded once at startup via `python-dotenv`.

**Key Properties:**

```python
settings.GOOGLE_API_KEY       # Required — Gemini LLM API key
settings.GEMINI_MODEL         # Default: "gemini-2.0-flash"
settings.langsmith_enabled    # True if API key + TRACING_V2=true are set
settings.langfuse_enabled     # True if public/secret keys are present
settings.API_PORT             # Default: 8000
```

**`settings.status_report()`** returns a summary dict:
```python
{
  "llm": "gemini-2.0-flash",
  "langsmith": True,
  "langfuse": False,
  "environment": "development"
}
```

**`settings.apply_langsmith_env()`** — Writes LangSmith env vars so LangChain auto-traces all LLM calls without any code changes in the rest of the app.

---

### 4.3 `agent/` — High-Level Agent Interface

#### `agent/prompts.py`

**Role:** All LLM prompt templates as `ChatPromptTemplate` objects. Centralised so prompts can be versioned and A/B tested independently.

**5 Prompt Templates:**

| Template | Purpose | LLM Output Format |
|---|---|---|
| `HELPDESK_SYSTEM_PROMPT` | Sets ARIA's persona and tone | System message |
| `INTENT_CLASSIFICATION_PROMPT` | Classifies user query into one of 5 intents | JSON |
| `RESPONSE_GENERATION_PROMPT` | Synthesises tool output into a friendly answer | Natural language |
| `ESCALATION_PROMPT` | Generates urgent escalation message for security/critical issues | Natural language |
| `GENERAL_RESPONSE_PROMPT` | Direct LLM response for general chitchat (no tool needed) | Natural language |

**Intent Classification — expected LLM output format:**
```json
{
  "intent": "knowledge_base",
  "confidence": 0.97,
  "entities": {"topic": "password"},
  "reasoning": "User is asking how to perform an action (reset password)"
}
```

---

#### `agent/helpdesk_agent.py`

**Role:** The main orchestrator class. Wraps the LangGraph and exposes a clean Python API.

**Class: `HelpdeskAgent`**

```python
agent = HelpdeskAgent(helpdesk_graph)
result = agent.ask("How do I reset my password?", user_email="alice@company.com")
```

**`ask()` method — step by step:**
1. Create initial `HelpdeskState` from the question
2. Build observability callbacks (LangFuse callback handler + LangSmith via env vars)
3. Invoke `helpdesk_graph.invoke(state, config={callbacks: [...]})`
4. Measure wall-clock latency
5. Extract `final_answer`, `intent`, `ticket_id` from final state
6. Flush LangFuse traces (non-blocking)
7. Return structured result dict:

```python
{
  "answer": "Here's how to reset your password...",
  "intent": "knowledge_base",
  "ticket_id": None,
  "latency_ms": 1240,
  "trace_url": "https://smith.langchain.com/...",
  "langfuse_trace_id": "abc123..."
}
```

**`stream()` method:**
Yields state snapshots after each node executes — useful for real-time streaming UIs:
```python
for update in agent.stream(question, user_email):
    print(update["node"], update["state_snapshot"])
```

---

### 4.4 `graph/` — LangGraph Workflow Engine

#### `graph/state.py`

**Role:** Defines the shared state schema using `TypedDict` — the data contract that all nodes must honour.

**`HelpdeskState` Fields:**

| Field | Type | Purpose |
|---|---|---|
| `messages` | `Annotated[list, add_messages]` | Full conversation history (auto-appends, never overwrites) |
| `question` | `str` | Current user query |
| `intent` | `str` | Classified intent (set by classify_intent node) |
| `entities` | `dict` | Extracted data e.g. `{"service": "vpn", "urgency": "high"}` |
| `tool_output` | `str` | Raw result returned by whichever tool executed |
| `ticket_id` | `Optional[str]` | Ticket ID if one was created (e.g. `"INC-421"`) |
| `final_answer` | `str` | The polished response returned to the user |
| `trace_metadata` | `dict` | Observability context (session ID, run ID, timestamps) |

**`Intent` Constants:**
```python
class Intent:
    KNOWLEDGE_BASE = "knowledge_base"
    SERVICE_STATUS = "service_status"
    CREATE_TICKET  = "create_ticket"
    ESCALATE       = "escalate"
    GENERAL        = "general"
```

**`initial_state(question, user_email)`** — Factory function that creates a fresh blank state for each new request.

---

#### `graph/nodes.py`

**Role:** The actual business logic — 6 functions, each one a node in the LangGraph.

**Node Summary:**

| Node Function | What it does | State fields updated |
|---|---|---|
| `classify_intent_node` | LLM call → parses JSON to get intent + entities | `intent`, `entities` |
| `knowledge_base_node` | Keyword search in the KB dict | `tool_output` |
| `service_status_node` | Lookup in SERVICES dict using extracted service name | `tool_output` |
| `create_ticket_node` | Auto-categorise issue, assign SLA, generate ticket | `tool_output`, `ticket_id` |
| `escalate_node` | Create P1 ticket + LLM generates urgent response | `tool_output`, `ticket_id` |
| `generate_response_node` | LLM call → synthesise `tool_output` into `final_answer` | `final_answer`, `messages` |

**Routing Function:**
```python
def route_intent(state: HelpdeskState) -> str:
    routing_map = {
        "knowledge_base":  "knowledge_base_node",
        "service_status":  "service_status_node",
        "create_ticket":   "create_ticket_node",
        "escalate":        "escalate_node",
        "general":         "generate_response",
    }
    return routing_map.get(state["intent"], "generate_response")
```

---

#### `graph/workflow.py`

**Role:** Assembles and compiles the LangGraph from its nodes and edges.

**Graph Assembly:**
```python
graph = StateGraph(HelpdeskState)

# Register nodes
graph.add_node("classify_intent",    classify_intent_node)
graph.add_node("knowledge_base_node", knowledge_base_node)
graph.add_node("service_status_node", service_status_node)
graph.add_node("create_ticket_node",  create_ticket_node)
graph.add_node("escalate_node",       escalate_node)
graph.add_node("generate_response",   generate_response_node)

# Fixed entry edge
graph.add_edge(START, "classify_intent")

# Conditional routing after classification
graph.add_conditional_edges("classify_intent", route_intent, {...})

# All tool nodes flow into generate_response
graph.add_edge("knowledge_base_node",  "generate_response")
graph.add_edge("service_status_node",  "generate_response")
graph.add_edge("create_ticket_node",   "generate_response")
graph.add_edge("escalate_node",        "generate_response")

# Exit
graph.add_edge("generate_response", END)

helpdesk_graph = graph.compile()
```

---

### 4.5 `tools/` — LangChain Tools

All three tools use the `@tool` decorator from LangChain — this gives them a typed interface that LLMs can call, with auto-generated docstrings used for tool selection.

---

#### `tools/knowledge_base.py`

**Purpose:** Mock IT knowledge base with keyword-based search.

**Data:** 10 categories with keywords, title, and detailed answer text:

| Category | Sample Keywords |
|---|---|
| Password Reset | password, reset, forgot, locked, account |
| VPN Setup | vpn, remote, cisco, anyconnect, tunnel |
| Email Issues | email, outlook, exchange, calendar, smtp |
| Software Install | install, software, license, download |
| WiFi / Network | wifi, internet, network, connection |
| Hardware | laptop, screen, keyboard, monitor, dock |
| Security | phishing, virus, malware, suspicious, breach |
| Onboarding | new employee, access, badge, setup |
| Slack | slack, channel, message, notification |
| Leave / HR | leave, vacation, time off, hr portal |

**Search Algorithm:** Scores each category by counting keyword matches in the query, returns the highest-scoring category with a confidence value.

**Tool Signature:**
```python
@tool
def search_knowledge_base(query: str) -> str:
    """Search IT knowledge base for policies, procedures, and how-to guides."""
```

---

#### `tools/service_status.py`

**Purpose:** Mock service status monitor — simulates a real-time status page.

**12 Monitored Services:**

| Service | Mock Status |
|---|---|
| VPN (Cisco AnyConnect) | Operational |
| Email (Microsoft Exchange) | **Degraded** (slow delivery incident) |
| Slack | Operational |
| Jira | Operational |
| GitHub Enterprise | Operational |
| AWS (Production) | Operational |
| Database (PostgreSQL) | Operational |
| HR Portal (Workday) | Maintenance |
| Corporate WiFi | Operational |
| CI/CD (Jenkins) | Operational |
| Zoom | Operational |
| Okta (SSO) | Operational |

Each service entry includes: status, uptime % (30-day), last checked timestamp, and optional incident description.

**Tool Signature:**
```python
@tool
def check_service_status(service: str) -> str:
    """Check the current operational status of an IT service or system."""
```

---

#### `tools/ticket_system.py`

**Purpose:** In-memory support ticket store — simulates a Jira/ServiceNow system.

**Auto-Triage Logic:**

| Field | How it's determined |
|---|---|
| **Category** | Keyword matching → Hardware / Network / Email / Account / Software / Security / Cloud / General |
| **Priority** | P1 if critical keywords ("breach", "outage"); P2 if error keywords ("broken", "not working"); P3 default |
| **Assigned Team** | Derived from category (e.g. Hardware → IT Support; Security → Security Operations) |
| **SLA** | P1 = 1 hour; P2 = 4 hours; P3 = 1 business day |

**Ticket Object:**
```python
{
  "id": "INC-421",
  "issue": "My laptop screen is cracked",
  "category": "Hardware",
  "priority": "P2 - High",
  "assigned_to": "IT Support Team",
  "sla": "4 hours",
  "status": "Open",
  "jira_url": "https://jira.company.com/browse/INC-421",
  "created_at": "2024-01-15T10:30:00"
}
```

**Tool Signature:**
```python
@tool
def create_support_ticket(issue: str, user_email: str, severity: str = "auto") -> str:
    """Create an IT support ticket for a reported issue."""
```

---

### 4.6 `observability/` — Tracing & Analytics

#### `observability/langsmith_tracer.py`

**Purpose:** Developer-focused execution tracing via LangSmith.

**What LangSmith captures (automatically):**
- Full prompt text sent to each LLM call
- Raw LLM response
- Token usage (input / output)
- Latency per call
- The entire execution tree from `classify_intent` → `knowledge_base_node` → `generate_response`

**How it works:**
LangChain checks for `LANGCHAIN_TRACING_V2=true` at import time. If set, every `.invoke()`, `.stream()`, and tool call is automatically traced — no code changes required.

**Key Functions:**
```python
get_langsmith_config(run_id, run_name, tags)  # → config dict for graph.invoke()
get_langsmith_run_url(run_id)                 # → link to trace in dashboard
print_langsmith_status()                      # → console status message
```

**Example trace tree in LangSmith dashboard:**
```
Run: "helpdesk-How do I reset my password?"
├── classify_intent (LLM)   — 0.8s, 245 tokens in, 48 tokens out
├── knowledge_base_node (Tool) — 0.01s
└── generate_response (LLM) — 1.2s, 312 tokens in, 89 tokens out
```

---

#### `observability/langfuse_tracer.py`

**Purpose:** Production analytics and cost monitoring via LangFuse.

**What LangFuse adds on top of LangSmith:**

| Capability | LangSmith | LangFuse |
|---|---|---|
| Per-run debugging | ✅ | ✅ |
| Aggregate cost monitoring | ❌ | ✅ |
| Latency percentiles (p95, p99) | ❌ | ✅ |
| User-level analytics | Partial | ✅ |
| Prompt version A/B testing | ❌ | ✅ |
| Self-hosted option | ❌ | ✅ |

**Implementation:** Uses `langfuse.langchain.CallbackHandler` — passed as a callback when invoking the graph. Non-blocking async sends to LangFuse cloud.

**Key Functions:**
```python
get_langfuse_callbacks(run_id, user_id, session_id, question)
# Returns: (callbacks_list, trace_id)

flush_langfuse()                        # Send pending traces
get_langfuse_trace_url(trace_id)        # → link to trace
print_langfuse_status()                 # → console status
```

**Note:** Both observability tools are fully optional — the agent works perfectly without either.

---

### 4.7 `api/` — REST Layer

#### `api/app.py`

**Role:** FastAPI application exposing the agent as a REST API.

**Setup:**
```python
app = FastAPI(title="AI IT Helpdesk Agent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

**8 Endpoints:**

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Health check — confirms API is running |
| `GET` | `/status` | Returns active integrations (LangSmith/LangFuse enabled?) |
| `POST` | `/chat` | Main chat endpoint — request/response cycle |
| `POST` | `/chat/stream` | Streaming chat via Server-Sent Events (SSE) |
| `GET` | `/tickets` | List all in-memory support tickets |
| `GET` | `/tickets/{id}` | Get a specific ticket by ID |
| `GET` | `/services` | List all monitored service statuses |
| `GET` | `/graph/info` | Returns graph topology and node descriptions |

**Pydantic Models:**
```python
class ChatRequest(BaseModel):
    question: str           # min 1 character
    user_email: str = "user@company.com"

class ChatResponse(BaseModel):
    answer: str
    intent: str
    ticket_id: Optional[str]
    latency_ms: int
    trace_url: Optional[str]
    langfuse_trace_id: Optional[str]
```

**Swagger UI** is auto-generated at `http://localhost:8000/docs` — you can test all endpoints interactively in the browser.

---

### 4.8 `demo/` — Interactive Workshop

#### `demo/workshop_demo.py`

**Role:** A Rich terminal UI demo runner with 5 curated scenarios that teach different agent capabilities.

**5 Workshop Scenarios:**

| # | User Question | Intent | Concept Taught |
|---|---|---|---|
| 1 | "How do I reset my password?" | `knowledge_base` | Tool use, KB search, prompt engineering |
| 2 | "Is the email server working? I'm not receiving emails." | `service_status` | Entity extraction, degraded status handling |
| 3 | "My laptop screen is cracked. Please create a support ticket." | `create_ticket` | Tool side effects, ticket ID generation, auto-triage |
| 4 | "My VPN keeps disconnecting since this morning. Is there an outage? If not, create a ticket." | `service_status` | Multi-step reasoning, compound queries |
| 5 | "URGENT: I received a suspicious email and clicked a link. I think my account is compromised!" | `escalate` | Criticality detection, P1 routing, escalation |

**Demo Features:**
- Uses the `Rich` library for coloured panels, tables, and progress indicators
- Pauses between scenarios for explanation (skip with `--auto`)
- After each scenario, displays a summary box explaining which concepts were demonstrated
- Shows intent classification result, latency, ticket ID, and trace links

---

## 5. Technologies Used

| Technology | Version | Role in Project |
|---|---|---|
| **Python** | 3.11+ | Runtime |
| **LangChain** | ≥ 0.3.0 | LLM orchestration, `@tool` decorator, `ChatPromptTemplate` |
| **LangGraph** | ≥ 0.2.0 | Stateful workflow engine, conditional routing, `StateGraph` |
| **Google Gemini** | `gemini-2.0-flash` | LLM provider — intent classification + response generation |
| **FastAPI** | ≥ 0.104.0 | REST API framework with auto-generated Swagger docs |
| **Pydantic** | ≥ 2.5.0 | Request/response model validation |
| **LangSmith** | ≥ 0.1.0 | Developer tracing and debugging (optional) |
| **LangFuse** | ≥ 2.0.0 | Production cost/latency analytics (optional) |
| **Rich** | ≥ 13.7.0 | Beautiful terminal UI for workshop scenarios |
| **python-dotenv** | ≥ 1.0.0 | `.env` file loading |
| **Uvicorn** | ≥ 0.24.0 | ASGI server for FastAPI |

---

## 6. Environment Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Required

```env
GOOGLE_API_KEY=AIza...          # Free key: https://aistudio.google.com/app/apikey
GEMINI_MODEL=gemini-2.0-flash   # Model name (default works)
```

### Optional — LangSmith (Developer Tracing)

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_...                        # From https://smith.langchain.com
LANGCHAIN_PROJECT=IT-Helpdesk-Workshop          # Project name in dashboard
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### Optional — LangFuse (Production Analytics)

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...   # From https://cloud.langfuse.com
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Application Settings

```env
APP_NAME=AI IT Helpdesk
APP_ENV=development              # or: production
LOG_LEVEL=INFO
API_PORT=8000
```

---

## 7. How to Run

### Step 1 — Setup

```bash
cd AI-Helpdesk-Agent
chmod +x setup.sh
./setup.sh
```

`setup.sh` does:
1. Checks Python ≥ 3.11
2. Creates `.venv/` virtual environment
3. Installs all dependencies from `requirements.txt`
4. Copies `.env.example` → `.env` if no `.env` exists

### Step 2 — Add API Key

```bash
# Open .env and add your Google API key
nano .env
# Set: GOOGLE_API_KEY=AIza...
```

### Step 3 — Run

```bash
source .venv/bin/activate
```

**Interactive CLI (recommended first run):**
```bash
python main.py
```

**Full workshop demo (5 scenarios):**
```bash
python main.py --demo
```

**Demo without pauses:**
```bash
python main.py --demo --auto
```

**Run specific scenarios:**
```bash
python main.py --scenario 1,3,5
```

**Single question:**
```bash
python main.py --ask "Is the VPN working right now?"
```

**REST API server:**
```bash
python main.py --api
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Check integration status:**
```bash
python main.py --status
```

---

## 8. Example Execution Walkthrough

### User asks: `"Is the email server working?"`

```
Step 1 — main.py
  Receives question via CLI input
  Creates HelpdeskAgent instance

Step 2 — HelpdeskAgent.ask()
  Builds initial HelpdeskState:
    { question: "Is the email server working?", intent: "", ... }
  Attaches LangFuse callback (if configured)
  Calls helpdesk_graph.invoke(state)

Step 3 — LangGraph: classify_intent_node
  LLM call with INTENT_CLASSIFICATION_PROMPT
  Input:  "Is the email server working?"
  Output: { "intent": "service_status", "entities": {"service": "email"}, "confidence": 0.96 }
  State:  intent="service_status", entities={"service": "email"}

Step 4 — LangGraph: route_intent()
  state["intent"] = "service_status"
  Returns: "service_status_node"

Step 5 — LangGraph: service_status_node
  Calls check_service_status(service="email")
  Lookup in SERVICES dict → finds "email" entry
  Status: DEGRADED | Incident: "Slow email delivery affecting 15% of users"
  State:  tool_output = "⚠️ Email (Microsoft Exchange) — DEGRADED\n..."

Step 6 — LangGraph: generate_response_node
  LLM call with RESPONSE_GENERATION_PROMPT
  Input:  question + tool_output
  Output: "Your email service is currently experiencing some issues. We're
           seeing degraded performance with slow delivery affecting about 15%
           of users. Our engineering team is investigating and expects to
           resolve this within 2 hours. In the meantime, try sending from
           webmail as a workaround..."
  State:  final_answer = "Your email service..."

Step 7 — HelpdeskAgent
  Measures latency: 1,340 ms
  Extracts: answer, intent, ticket_id=None
  Flushes LangFuse
  Returns result dict

Step 8 — Console output
  Intent:   service_status  |  Latency: 1340ms  |  LangSmith: ✅
  ┌─────────────────────────────────────┐
  │  Your email service is currently   │
  │  experiencing some issues...        │
  └─────────────────────────────────────┘
```

---

## 9. Key Concepts & Patterns

### LangChain Concepts

| Concept | Where Used | Purpose |
|---|---|---|
| `@tool` decorator | `tools/*.py` | Wraps Python functions so LLMs can call them with typed inputs |
| `ChatPromptTemplate` | `agent/prompts.py` | Structured prompt with variable placeholders |
| `ChatGoogleGenerativeAI` | `graph/nodes.py` | LLM interface with temperature control |
| `add_messages` reducer | `graph/state.py` | Appends to message history instead of replacing it |

### LangGraph Concepts

| Concept | Where Used | Purpose |
|---|---|---|
| `StateGraph(TypedDict)` | `graph/workflow.py` | Graph with typed, shared state |
| `add_node()` | `graph/workflow.py` | Register a Python function as a graph node |
| `add_conditional_edges()` | `graph/workflow.py` | Branch to different nodes based on state values |
| `graph.compile()` | `graph/workflow.py` | Lock the graph; enables `.invoke()` and `.stream()` |
| Node function signature | `graph/nodes.py` | `def node(state: HelpdeskState) -> dict:` — returns only changed fields |

### Observability Patterns

| Pattern | Tool | Description |
|---|---|---|
| Auto-tracing via env vars | LangSmith | Set `LANGCHAIN_TRACING_V2=true` → zero code changes needed |
| Callback-based tracing | LangFuse | Pass `CallbackHandler` in `config` → captures all events |
| Session tracking | Both | `session_id` groups all turns from one user session |
| Latency measurement | `helpdesk_agent.py` | Wall-clock `time.time()` wrapping `graph.invoke()` |

### Design Patterns

| Pattern | Location | Benefit |
|---|---|---|
| **Centralised config** | `config/settings.py` | One place to change env vars; no hardcoded keys |
| **Mock tools** | `tools/*.py` | Workshop runs without any external API subscriptions |
| **Keyword scoring** | `tools/knowledge_base.py` | Simple semantic approximation; swap for embeddings in production |
| **Auto-triage** | `tools/ticket_system.py` | Rules-based categorisation (replace with ML classifier in production) |
| **Separation of concerns** | All layers | Config / Agent / Graph / Tools / API are fully independent modules |

---

## 10. Security Notes

| Risk | Mitigation |
|---|---|
| API keys in source code | `.env` is in `.gitignore` — never committed |
| LangSmith/LangFuse data sharing | Both are optional third-party SaaS; review their privacy policies |
| Ticket system | Mock only — production must use authenticated Jira/ServiceNow API |
| Service status | Mock only — production should query real monitoring APIs (Datadog, PagerDuty) |
| Knowledge base access | Add auth/RBAC when connecting to internal Confluence or SharePoint |
| CORS in API | Currently `allow_origins=["*"]` — restrict to known domains in production |

---

## Summary

This project is a **complete, production-ready blueprint** for building AI helpdesk agents. It demonstrates:

| Capability | Implementation |
|---|---|
| ✅ Intent classification | LLM + structured JSON output |
| ✅ Tool orchestration | LangChain `@tool` + LangGraph routing |
| ✅ Stateful workflows | LangGraph `StateGraph` with `TypedDict` |
| ✅ Developer tracing | LangSmith auto-tracing |
| ✅ Production analytics | LangFuse callback handler |
| ✅ REST API | FastAPI with Pydantic validation + SSE streaming |
| ✅ Workshop UX | Rich terminal UI with 5 interactive scenarios |
| ✅ Clean architecture | Config / Agent / Graph / Tools / Observability / API all decoupled |

**The fastest way to see it in action:**
```bash
./setup.sh
source .venv/bin/activate
# Add GOOGLE_API_KEY to .env
python main.py --demo
```
