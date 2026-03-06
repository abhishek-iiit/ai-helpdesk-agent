"""
graph/nodes.py
==============
LangGraph Node Implementations

Workshop Note:
    Each NODE in the graph is a Python function that:
    1. Receives the current STATE
    2. Performs some operation (LLM call, tool execution, etc.)
    3. Returns a DICT with state updates

    The graph engine merges these updates into the shared state
    and passes it to the next node.

    Graph Flow:
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │  START → [classify_intent] → (conditional routing)      │
    │                                                         │
    │     ┌──────────────────────────────────────┐           │
    │     │ knowledge_base  service_status        │           │
    │     │ create_ticket   escalate   general    │           │
    │     └──────────────────────────────────────┘           │
    │                      ↓                                  │
    │           [generate_response] → END                     │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
"""

import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config.settings import settings
from graph.state import HelpdeskState, Intent
from agent.prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    ESCALATION_PROMPT,
    GENERAL_RESPONSE_PROMPT,
)
from tools import search_knowledge_base, check_service_status, create_support_ticket

console = Console()

# ─────────────────────────────────────────────────────────────
# LLM Instance
# ─────────────────────────────────────────────────────────────
def get_llm(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    """
    Create a ChatGoogleGenerativeAI instance.

    Workshop Note:
        temperature=0.1 gives near-deterministic responses —
        important for classification tasks.
        temperature=0.7 gives more creative/varied responses —
        better for generating helpful answers.
    """
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=temperature,
        google_api_key=settings.GOOGLE_API_KEY,
    )


# ─────────────────────────────────────────────────────────────
# Workshop-Friendly Console Output
# ─────────────────────────────────────────────────────────────
def _print_node(name: str, content: str, color: str = "blue"):
    """Print a colored panel showing which graph node is executing."""
    console.print(
        Panel(
            content,
            title=f"[bold {color}]⬡ NODE: {name}[/bold {color}]",
            border_style=color,
            padding=(0, 1),
        )
    )


# ─────────────────────────────────────────────────────────────
# NODE 1: classify_intent
# ─────────────────────────────────────────────────────────────
def classify_intent_node(state: HelpdeskState) -> dict:
    """
    Node 1: Classify the user's intent using an LLM.

    Uses a structured prompt to determine:
    - What the user wants (intent category)
    - Key entities (service names, urgency level)
    - Confidence score

    Workshop Note:
        This is a CLASSIFICATION node. It doesn't answer the question —
        it just categorizes it for routing. This pattern is common in
        production AI agents to keep each node focused.
    """
    question = state["question"]

    _print_node(
        "classify_intent",
        f"[yellow]Classifying:[/yellow] {question}",
        "yellow",
    )

    llm = get_llm(temperature=0.0)  # Zero temperature for deterministic classification

    # Format the classification prompt
    messages = INTENT_CLASSIFICATION_PROMPT.format_messages(question=question)

    # Call the LLM
    response = llm.invoke(messages)
    raw_content = response.content.strip()

    # Parse JSON response
    try:
        # Handle potential markdown code blocks
        if "```" in raw_content:
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]

        parsed = json.loads(raw_content)
        intent = parsed.get("intent", Intent.GENERAL)
        entities = parsed.get("entities", {})
        confidence = parsed.get("confidence", 0.5)
        reasoning = parsed.get("reasoning", "")

        _print_node(
            "classify_intent",
            f"[green]Intent:[/green] {intent} (confidence: {confidence:.0%})\n"
            f"[green]Entities:[/green] {entities}\n"
            f"[dim]{reasoning}[/dim]",
            "green",
        )

    except (json.JSONDecodeError, KeyError) as e:
        # Fallback to general if parsing fails
        intent = Intent.GENERAL
        entities = {}
        _print_node("classify_intent", f"[red]Parse error, defaulting to 'general': {e}[/red]", "red")

    # Merge user_email from existing entities
    merged_entities = {**state.get("entities", {}), **entities}

    return {
        "intent": intent,
        "entities": merged_entities,
        "messages": [HumanMessage(content=question)],
    }


# ─────────────────────────────────────────────────────────────
# NODE 2a: knowledge_base_node
# ─────────────────────────────────────────────────────────────
def knowledge_base_node(state: HelpdeskState) -> dict:
    """
    Node 2a: Execute the knowledge base search tool.

    Invoked when intent = "knowledge_base"
    Searches IT policies, procedures, and how-to guides.
    """
    question = state["question"]

    _print_node(
        "knowledge_base",
        f"[cyan]Searching KB for:[/cyan] {question}",
        "cyan",
    )

    result = search_knowledge_base.invoke({"query": question})

    _print_node("knowledge_base", f"[green]KB Result (truncated):[/green]\n{result[:200]}...", "cyan")

    return {"tool_output": result}


# ─────────────────────────────────────────────────────────────
# NODE 2b: service_status_node
# ─────────────────────────────────────────────────────────────
def service_status_node(state: HelpdeskState) -> dict:
    """
    Node 2b: Execute the service status check tool.

    Invoked when intent = "service_status"
    Queries the monitoring system for service health.
    """
    entities = state.get("entities", {})
    service = entities.get("service") or state["question"]

    _print_node(
        "service_status",
        f"[magenta]Checking status for:[/magenta] {service}",
        "magenta",
    )

    result = check_service_status.invoke({"service": service})

    _print_node("service_status", f"[green]Status Result:[/green]\n{result[:300]}", "magenta")

    return {"tool_output": result}


# ─────────────────────────────────────────────────────────────
# NODE 2c: create_ticket_node
# ─────────────────────────────────────────────────────────────
def create_ticket_node(state: HelpdeskState) -> dict:
    """
    Node 2c: Execute the ticket creation tool.

    Invoked when intent = "create_ticket"
    Creates a support ticket in Jira/ServiceNow.
    """
    question = state["question"]
    entities = state.get("entities", {})
    user_email = entities.get("user_email", "user@company.com")

    # If service status was checked and there's an existing tool_output,
    # incorporate it into the ticket description
    existing_output = state.get("tool_output", "")
    issue_description = question
    if existing_output:
        issue_description = f"{question}\n\nContext: {existing_output[:200]}"

    _print_node(
        "create_ticket",
        f"[red]Creating ticket for:[/red] {question[:100]}\n"
        f"[dim]Reporter: {user_email}[/dim]",
        "red",
    )

    result = create_support_ticket.invoke({
        "issue": issue_description,
        "user_email": user_email,
    })

    # Extract ticket ID from result
    ticket_id = None
    if "INC-" in result:
        import re
        match = re.search(r'INC-\d+', result)
        if match:
            ticket_id = match.group()

    _print_node("create_ticket", f"[green]Ticket Created:[/green] {ticket_id}", "red")

    return {
        "tool_output": result,
        "ticket_id": ticket_id,
    }


# ─────────────────────────────────────────────────────────────
# NODE 2d: escalate_node
# ─────────────────────────────────────────────────────────────
def escalate_node(state: HelpdeskState) -> dict:
    """
    Node 2d: Handle critical escalations.

    Invoked when intent = "escalate"
    For critical issues: security breaches, production outages, all-user impacts.
    Always creates a P1 ticket AND pages the on-call team.
    """
    question = state["question"]
    entities = state.get("entities", {})
    user_email = entities.get("user_email", "user@company.com")

    _print_node(
        "escalate",
        f"[bold red]🚨 ESCALATING CRITICAL ISSUE[/bold red]\n{question[:100]}",
        "red",
    )

    # Create a P1 ticket
    ticket_result = create_support_ticket.invoke({
        "issue": f"[ESCALATED - P1] {question}",
        "user_email": user_email,
        "severity": "P1",
    })

    # Generate escalation response using LLM
    llm = get_llm(temperature=0.3)
    messages = ESCALATION_PROMPT.format_messages(
        question=question,
        entities=str(entities),
    )
    response = llm.invoke(messages)

    escalation_output = (
        f"🚨 **CRITICAL ISSUE — ESCALATED TO ON-CALL TEAM**\n\n"
        f"{response.content}\n\n"
        f"---\n**Ticket Details:**\n{ticket_result}"
    )

    # Extract ticket ID
    ticket_id = None
    if "INC-" in ticket_result:
        import re
        match = re.search(r'INC-\d+', ticket_result)
        if match:
            ticket_id = match.group()

    return {
        "tool_output": escalation_output,
        "ticket_id": ticket_id,
    }


# ─────────────────────────────────────────────────────────────
# NODE 3: generate_response
# ─────────────────────────────────────────────────────────────
def generate_response_node(state: HelpdeskState) -> dict:
    """
    Node 3 (Final): Generate the user-facing response.

    Invoked after any tool node (or directly for general questions).
    Uses the LLM to synthesize tool output into a clear, friendly response.

    Workshop Note:
        This is the RESPONSE SYNTHESIS node. Even though tools return
        structured data, we use the LLM to make it conversational and
        to add context/next steps. This is a common pattern:

        Tool Output (raw data) → LLM (synthesize) → User Response (natural language)
    """
    question = state["question"]
    tool_output = state.get("tool_output", "")
    intent = state.get("intent", Intent.GENERAL)

    _print_node(
        "generate_response",
        f"[blue]Synthesizing response for intent:[/blue] {intent}",
        "blue",
    )

    llm = get_llm(temperature=0.7)  # Higher temperature for natural responses

    if tool_output:
        # Use tool output to generate response
        messages = RESPONSE_GENERATION_PROMPT.format_messages(
            question=question,
            tool_output=tool_output,
        )
    else:
        # General question — answer directly without tool context
        messages = GENERAL_RESPONSE_PROMPT.format_messages(question=question)

    response = llm.invoke(messages)
    final_answer = response.content

    _print_node(
        "generate_response",
        f"[green]Response generated[/green] ({len(final_answer)} chars)",
        "blue",
    )

    return {
        "final_answer": final_answer,
        "messages": [AIMessage(content=final_answer)],
    }


# ─────────────────────────────────────────────────────────────
# Conditional Edge: Route based on intent
# ─────────────────────────────────────────────────────────────
def route_intent(state: HelpdeskState) -> str:
    """
    Conditional edge function — determines next node based on intent.

    Workshop Note:
        This is the ROUTING LOGIC of LangGraph. After classify_intent_node
        runs, the graph calls this function to decide which node to visit next.

        This creates a DYNAMIC workflow where the path through the graph
        depends on the content of the user's message.

    Returns:
        Name of the next node to execute
    """
    intent = state.get("intent", Intent.GENERAL)

    routing_map = {
        Intent.KNOWLEDGE_BASE: "knowledge_base_node",
        Intent.SERVICE_STATUS: "service_status_node",
        Intent.CREATE_TICKET:  "create_ticket_node",
        Intent.ESCALATE:       "escalate_node",
        Intent.GENERAL:        "generate_response_node",
    }

    next_node = routing_map.get(intent, "generate_response_node")

    console.print(
        f"\n[bold white on blue] ROUTING [/bold white on blue] "
        f"intent=[yellow]{intent}[/yellow] → "
        f"[cyan]{next_node}[/cyan]\n"
    )

    return next_node
