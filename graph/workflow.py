"""
graph/workflow.py
=================
LangGraph Workflow Definition

Workshop Note:
    This file BUILDS and COMPILES the graph.
    Think of it as the "blueprint" that wires all nodes together.

    Visual representation:
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   START                                                     │
    │     │                                                       │
    │     ▼                                                       │
    │ ┌───────────────────┐                                       │
    │ │  classify_intent  │  ← LLM call: What does the user want? │
    │ └─────────┬─────────┘                                       │
    │           │ (conditional routing based on intent)           │
    │    ┌──────┴──────────────────────────────────┐             │
    │    │                                          │             │
    │    ▼              ▼              ▼            ▼             │
    │ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐        │
    │ │knowledge │ │service  │ │ create   │ │escalate  │        │
    │ │_base     │ │_status  │ │ _ticket  │ │          │        │
    │ └────┬─────┘ └────┬────┘ └────┬─────┘ └────┬─────┘        │
    │      │            │           │             │               │
    │      └────────────┴─────┬─────┴─────────────┘              │
    │                         │                                   │
    │                         ▼                                   │
    │               ┌──────────────────┐                         │
    │               │ generate_response │  ← LLM: Synthesize      │
    │               └────────┬─────────┘                         │
    │                        │                                    │
    │                       END                                   │
    └─────────────────────────────────────────────────────────────┘
"""

from langgraph.graph import StateGraph, START, END

from graph.state import HelpdeskState
from graph.nodes import (
    classify_intent_node,
    knowledge_base_node,
    service_status_node,
    create_ticket_node,
    escalate_node,
    generate_response_node,
    route_intent,
)


def build_helpdesk_graph() -> StateGraph:
    """
    Build the LangGraph workflow (returns uncompiled graph).

    Workshop Note:
        Building the graph is separate from compiling it.
        This lets you inspect, visualize, or modify the graph
        before it's ready to run.
    """
    # ── Initialize graph with our state schema ─────────────────
    graph = StateGraph(HelpdeskState)

    # ── Add Nodes ──────────────────────────────────────────────
    # Each node is a Python function that processes state
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("knowledge_base_node", knowledge_base_node)
    graph.add_node("service_status_node", service_status_node)
    graph.add_node("create_ticket_node", create_ticket_node)
    graph.add_node("escalate_node", escalate_node)
    graph.add_node("generate_response", generate_response_node)

    # ── Add Edges ──────────────────────────────────────────────
    # Entry point: START → classify_intent (always)
    graph.add_edge(START, "classify_intent")

    # Conditional routing: classify_intent → (one of the tool nodes or generate_response)
    # route_intent() decides which node based on state["intent"]
    graph.add_conditional_edges(
        "classify_intent",           # From this node...
        route_intent,                # ...call this function to decide...
        {                            # ...and map return values to nodes:
            "knowledge_base_node":  "knowledge_base_node",
            "service_status_node":  "service_status_node",
            "create_ticket_node":   "create_ticket_node",
            "escalate_node":        "escalate_node",
            "generate_response_node": "generate_response",
        }
    )

    # Tool nodes → generate_response (all tool nodes feed into final response)
    graph.add_edge("knowledge_base_node", "generate_response")
    graph.add_edge("service_status_node", "generate_response")
    graph.add_edge("create_ticket_node",  "generate_response")
    graph.add_edge("escalate_node",       "generate_response")

    # Final node → END
    graph.add_edge("generate_response", END)

    return graph


def compile_helpdesk_graph():
    """
    Build and compile the graph, making it ready to invoke.

    Workshop Note:
        .compile() validates the graph structure (no orphan nodes,
        no infinite loops without checkpointers, etc.) and returns
        a CompiledGraph that can be .invoke()'d or .stream()'d.
    """
    graph = build_helpdesk_graph()
    compiled = graph.compile()
    return compiled


# ── Module-level compiled graph (singleton) ────────────────────
# Import this in other modules: from graph.workflow import helpdesk_graph
helpdesk_graph = compile_helpdesk_graph()
