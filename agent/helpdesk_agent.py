"""
agent/helpdesk_agent.py
=======================
Main Helpdesk Agent — High-Level Interface

Workshop Note:
    This class wraps the LangGraph workflow and provides a clean
    API for the FastAPI layer, demo scripts, and CLI.

    It also:
    - Injects LangSmith & LangFuse callbacks for observability
    - Formats responses consistently
    - Handles errors gracefully
"""

import time
import uuid
from typing import Iterator, Optional

from rich.console import Console
from rich.rule import Rule
from rich.panel import Panel

from config.settings import settings
from graph.state import initial_state
from graph.workflow import helpdesk_graph
from observability.langsmith_tracer import get_langsmith_config
from observability.langfuse_tracer import get_langfuse_callbacks, flush_langfuse

console = Console()


class HelpdeskAgent:
    """
    AI IT Helpdesk Agent

    This is the main entry point for interacting with the helpdesk system.
    It orchestrates:
    - LangGraph workflow execution
    - LangSmith tracing (developer debugging)
    - LangFuse tracking (production observability)

    Example:
        agent = HelpdeskAgent()
        response = agent.ask("How do I reset my password?")
        print(response["answer"])
    """

    def __init__(self):
        self.graph = helpdesk_graph
        self.session_id = str(uuid.uuid4())[:8]

    def ask(
        self,
        question: str,
        user_email: str = "user@company.com",
        verbose: bool = True,
    ) -> dict:
        """
        Process a user question through the full LangGraph workflow.

        Args:
            question: The user's IT support question
            user_email: User's email (for ticket creation)
            verbose: Show node execution in console

        Returns:
            dict with keys:
            - answer: The final response
            - intent: Detected intent
            - ticket_id: Created ticket ID (or None)
            - tool_output: Raw tool result
            - latency_ms: Processing time
            - trace_url: LangSmith trace URL (if enabled)
            - langfuse_trace_id: LangFuse trace ID (if enabled)
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()

        if verbose:
            console.print(Rule("[bold blue]🤖 ARIA - AI IT Helpdesk Agent[/bold blue]"))
            console.print(f"\n[bold]User:[/bold] {question}\n")

        # ── Build initial state ─────────────────────────────────
        state = initial_state(question=question, user_email=user_email)
        state["trace_metadata"]["run_id"] = run_id
        state["trace_metadata"]["session_id"] = self.session_id

        # ── Build observability callbacks ───────────────────────
        callbacks = []

        # LangFuse callback (adds automatic tracing to all LLM calls)
        langfuse_callbacks, langfuse_trace_id = get_langfuse_callbacks(
            run_id=run_id,
            user_id=user_email,
            session_id=self.session_id,
            question=question,
        )
        callbacks.extend(langfuse_callbacks)

        # LangSmith config (env vars handle the rest automatically)
        langsmith_config = get_langsmith_config(
            run_id=run_id,
            run_name=f"helpdesk-{question[:30]}",
        )

        # ── Invoke the LangGraph workflow ───────────────────────
        config = {
            **langsmith_config,
            "callbacks": callbacks,
            "run_name": f"Helpdesk: {question[:50]}",
            "tags": ["helpdesk", "workshop"],
            "metadata": {
                "user_email": user_email,
                "session_id": self.session_id,
                "question": question,
            },
        }

        try:
            result = self.graph.invoke(state, config=config)
        except Exception as e:
            error_msg = f"I encountered an error processing your request: {str(e)}\n\nPlease contact IT directly at ext. 4357 or it-help@company.com"
            console.print(f"[red]Error during graph execution: {e}[/red]")
            return {
                "answer": error_msg,
                "intent": "error",
                "ticket_id": None,
                "tool_output": str(e),
                "latency_ms": int((time.time() - start_time) * 1000),
                "trace_url": None,
                "langfuse_trace_id": langfuse_trace_id,
                "error": str(e),
            }

        latency_ms = int((time.time() - start_time) * 1000)

        # ── Flush LangFuse to ensure data is sent ───────────────
        if settings.langfuse_enabled:
            flush_langfuse()

        # ── Format response ─────────────────────────────────────
        final_answer = result.get("final_answer", "I could not generate a response.")
        intent = result.get("intent", "unknown")
        ticket_id = result.get("ticket_id")

        # Build LangSmith trace URL
        trace_url = None
        if settings.langsmith_enabled:
            trace_url = f"https://smith.langchain.com/projects/{settings.LANGCHAIN_PROJECT}"

        if verbose:
            console.print(Rule("[bold green]Response[/bold green]"))
            console.print(
                Panel(
                    final_answer,
                    title="[bold green]🤖 ARIA[/bold green]",
                    border_style="green",
                )
            )
            console.print(
                f"\n[dim]Intent: {intent} | Latency: {latency_ms}ms | "
                f"Ticket: {ticket_id or 'None'} | "
                f"LangSmith: {'✅' if settings.langsmith_enabled else '❌'} | "
                f"LangFuse: {'✅' if settings.langfuse_enabled else '❌'}[/dim]\n"
            )
            if trace_url:
                console.print(f"[dim]🔍 View trace: {trace_url}[/dim]")

        return {
            "answer": final_answer,
            "intent": intent,
            "ticket_id": ticket_id,
            "tool_output": result.get("tool_output", ""),
            "latency_ms": latency_ms,
            "trace_url": trace_url,
            "langfuse_trace_id": langfuse_trace_id,
        }

    def stream(
        self,
        question: str,
        user_email: str = "user@company.com",
    ) -> Iterator[dict]:
        """
        Stream the graph execution — yields state updates at each node.

        Workshop Note:
            Streaming is useful for:
            1. Showing real-time progress to users
            2. Debugging node-by-node execution
            3. Building responsive UIs that update as the agent works

        Yields:
            Dict with node name and state snapshot after each node
        """
        state = initial_state(question=question, user_email=user_email)
        callbacks = get_langfuse_callbacks(
            run_id=str(uuid.uuid4()),
            user_id=user_email,
            session_id=self.session_id,
            question=question,
        )[0]

        config = {
            "callbacks": callbacks,
            "tags": ["helpdesk", "stream"],
        }

        for node_name, node_state in self.graph.stream(state, config=config):
            yield {
                "node": node_name,
                "state_snapshot": {
                    "intent": node_state.get("intent", ""),
                    "tool_output_preview": node_state.get("tool_output", "")[:100],
                    "ticket_id": node_state.get("ticket_id"),
                    "has_answer": bool(node_state.get("final_answer")),
                }
            }
