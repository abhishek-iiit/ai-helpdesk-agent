"""
observability/langfuse_tracer.py
=================================
LangFuse Setup & Tracing Helpers

Workshop Note:
    LangFuse is a PRODUCTION tool for:
    - Cost monitoring (token usage × price per model)
    - Prompt performance analytics
    - User session tracking
    - Quality scoring / human feedback
    - A/B testing prompts in production
    - Distributed tracing across services

    KEY DIFFERENCE from LangSmith:
    ┌────────────────┬────────────────────────────────────┐
    │ LangSmith      │ LangFuse                           │
    ├────────────────┼────────────────────────────────────┤
    │ Developer tool │ Production analytics platform      │
    │ Debugging      │ Business metrics & cost monitoring │
    │ Prompt testing │ Usage analytics at scale           │
    │ Local/dev      │ Production SaaS                    │
    └────────────────┴────────────────────────────────────┘

    HOW IT WORKS:
    1. Create CallbackHandler from langfuse
    2. Pass it in the callbacks list to LangChain calls
    3. LangFuse captures all traces automatically
    4. View analytics at: https://cloud.langfuse.com

    Architecture:
    ┌───────────────────────────────────────────────┐
    │           Your Application                    │
    │   LangChain LLM Call                          │
    │        │ (callback hook)                      │
    │        ▼                                      │
    │   LangFuseCallbackHandler                     │
    │        │ (async, non-blocking)                │
    │        ▼                                      │
    │   cloud.langfuse.com Dashboard                │
    │   - Cost per conversation                     │
    │   - Response latency p50/p95/p99              │
    │   - Prompt version performance                │
    │   - User-level analytics                      │
    │   - Token usage trends                        │
    └───────────────────────────────────────────────┘
"""

import uuid
from config.settings import settings

# LangFuse v3+ uses langfuse.langchain.CallbackHandler (not langfuse.callback).
# We probe the correct import path so older v2 installs also degrade gracefully.
try:
    from langfuse.langchain import CallbackHandler as _LangfuseCallbackHandler  # noqa: F401
    _LANGFUSE_AVAILABLE = True
except Exception:
    _LANGFUSE_AVAILABLE = False


def get_langfuse_callbacks(
    run_id: str | None = None,
    user_id: str = "anonymous",
    session_id: str | None = None,
    question: str = "",
) -> tuple[list, str | None]:
    """
    Create LangFuse callback handler for production tracing.

    Workshop Note:
        The CallbackHandler is passed in the `callbacks` list when
        calling LangChain/LangGraph. LangFuse intercepts all LLM calls
        and records them with metadata.

    Args:
        run_id: Unique trace ID
        user_id: User identifier (for user-level analytics)
        session_id: Session identifier (for session-level analytics)
        question: The user's question (stored as trace input)

    Returns:
        Tuple of (callbacks_list, trace_id)
        - callbacks_list: Pass to LangChain config
        - trace_id: Use to link to the trace in LangFuse UI
    """
    if not settings.langfuse_enabled or not _LANGFUSE_AVAILABLE:
        return [], None

    try:
        from langfuse.langchain import CallbackHandler

        # LangFuse v3 requires trace IDs as 32 lowercase hex chars (UUID without hyphens).
        raw_id = run_id or str(uuid.uuid4())
        trace_id = raw_id.replace("-", "")

        # v3 API: keys/host are read from env vars automatically.
        # trace_context pins the trace ID so the run appears under a
        # predictable ID in the LangFuse dashboard.
        handler = CallbackHandler(
            trace_context={"trace_id": trace_id},
            update_trace=True,
        )

        return [handler], trace_id

    except ImportError:
        return [], None
    except Exception as e:
        print(f"[LangFuse] Failed to create callback handler: {e}")
        return [], None


def flush_langfuse():
    """
    Flush pending LangFuse events to the server.

    Workshop Note:
        LangFuse sends data asynchronously to avoid slowing down your app.
        Call flush() at the end of your request to ensure all events
        are sent before the response is returned.

        In production, this is typically called via middleware or
        request lifecycle hooks.
    """
    if not settings.langfuse_enabled or not _LANGFUSE_AVAILABLE:
        return

    try:
        from langfuse import get_client
        get_client().flush()
    except Exception:
        pass  # Non-critical — don't let flush errors break the app


def get_langfuse_trace_url(trace_id: str) -> str | None:
    """
    Generate URL to view a specific trace in LangFuse.

    Args:
        trace_id: The trace ID used when creating the callback handler

    Returns:
        URL to the trace in LangFuse dashboard
    """
    if not settings.langfuse_enabled or not trace_id:
        return None
    # Ensure trace_id is in 32-hex format for the URL (strip hyphens if present)
    hex_trace_id = trace_id.replace("-", "")
    return f"{settings.LANGFUSE_HOST}/trace/{hex_trace_id}"


def print_langfuse_status():
    """
    Print LangFuse integration status to console.
    Called at startup to confirm production tracing is active.
    """
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

    if settings.langfuse_enabled and _LANGFUSE_AVAILABLE:
        console.print(
            Panel(
                f"[green]✅ LangFuse Tracing: ENABLED[/green]\n"
                f"Host: [cyan]{settings.LANGFUSE_HOST}[/cyan]\n"
                f"Dashboard: [link]{settings.LANGFUSE_HOST}[/link]\n\n"
                f"[dim]Tracking cost, latency, and prompt performance in production.[/dim]",
                title="[bold]LangFuse — Production Analytics[/bold]",
                border_style="magenta",
            )
        )
    elif settings.langfuse_enabled and not _LANGFUSE_AVAILABLE:
        console.print(
            Panel(
                "[yellow]⚠️  LangFuse keys are set but the package is not compatible with Python 3.14+[/yellow]\n\n"
                "LangFuse tracing is disabled for this run.\n"
                "The agent works fully without it — LangSmith handles developer tracing.\n\n"
                "[dim]LangFuse concept is still demonstrated in observability/langfuse_tracer.py[/dim]",
                title="[bold]LangFuse — Production Analytics[/bold]",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]⚠️  LangFuse: DISABLED[/yellow]\n\n"
                "To enable:\n"
                "1. Sign up at [link]https://cloud.langfuse.com[/link]\n"
                "2. Add to .env:\n"
                "   LANGFUSE_PUBLIC_KEY=your_public_key\n"
                "   LANGFUSE_SECRET_KEY=your_secret_key",
                title="[bold]LangFuse — Production Analytics[/bold]",
                border_style="dim",
            )
        )
