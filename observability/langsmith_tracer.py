"""
observability/langsmith_tracer.py
==================================
LangSmith Setup & Tracing Helpers

Workshop Note:
    LangSmith is a DEVELOPER tool for:
    - Visualizing traces of LLM calls
    - Inspecting prompts and responses
    - Measuring latency and token usage
    - Debugging chain execution step-by-step
    - Running prompt experiments

    HOW IT WORKS:
    1. Set LANGCHAIN_TRACING_V2=true in your .env
    2. Set LANGCHAIN_API_KEY to your LangSmith key
    3. Every LangChain/LangGraph call is AUTOMATICALLY traced
    4. View traces at: https://smith.langchain.com

    No code changes needed — just env vars!

    Architecture:
    ┌───────────────────────────────────────────────┐
    │           Your Application                    │
    │   LangChain LLM Call → LangGraph Node         │
    │              │                                │
    │              │ (automatic tracing via env)    │
    │              ▼                                │
    │        LangSmith SDK                          │
    │              │                                │
    │              ▼                                │
    │   smith.langchain.com Dashboard               │
    │   - Full trace tree                           │
    │   - Token counts                              │
    │   - Latency breakdown                         │
    │   - Prompt inspection                         │
    └───────────────────────────────────────────────┘
"""

import uuid
from config.settings import settings


def get_langsmith_config(
    run_id: str | None = None,
    run_name: str = "helpdesk-run",
    tags: list[str] | None = None,
) -> dict:
    """
    Build the LangChain config dict that enables LangSmith tracing.

    This dict is passed to graph.invoke(..., config=config)

    Workshop Note:
        Even without calling this function, LangSmith traces automatically
        because we set os.environ["LANGCHAIN_TRACING_V2"] = "true" in settings.
        This function just adds metadata to make traces more organized.

    Args:
        run_id: Unique run identifier (UUID)
        run_name: Human-readable name shown in LangSmith UI
        tags: Tags for filtering in LangSmith (e.g., ["production", "vpn"])

    Returns:
        Config dict to pass to LangChain/LangGraph .invoke()
    """
    if not run_id:
        run_id = str(uuid.uuid4())

    config = {
        "run_id": run_id,
        "run_name": run_name,
        "tags": tags or ["it-helpdesk", "workshop"],
        "metadata": {
            "project": settings.LANGCHAIN_PROJECT,
            "environment": settings.APP_ENV,
        },
    }

    return config


def get_langsmith_run_url(run_id: str) -> str:
    """
    Generate the LangSmith URL to view a specific trace run.

    Args:
        run_id: The run UUID used when invoking the graph

    Returns:
        URL to view the trace in LangSmith dashboard
    """
    return (
        f"https://smith.langchain.com/projects/{settings.LANGCHAIN_PROJECT}/runs/{run_id}"
    )


def print_langsmith_status():
    """
    Print LangSmith integration status to console.
    Called at startup to confirm tracing is active.
    """
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

    if settings.langsmith_enabled:
        console.print(
            Panel(
                f"[green]✅ LangSmith Tracing: ENABLED[/green]\n"
                f"Project: [cyan]{settings.LANGCHAIN_PROJECT}[/cyan]\n"
                f"Dashboard: [link]https://smith.langchain.com[/link]\n\n"
                f"[dim]Every LLM call, chain, and tool execution will be traced automatically.[/dim]",
                title="[bold]LangSmith — Developer Debugging[/bold]",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]⚠️  LangSmith Tracing: DISABLED[/yellow]\n\n"
                "To enable:\n"
                "1. Sign up at [link]https://smith.langchain.com[/link]\n"
                "2. Add to .env:\n"
                "   LANGCHAIN_TRACING_V2=true\n"
                "   LANGCHAIN_API_KEY=your_key_here",
                title="[bold]LangSmith — Developer Debugging[/bold]",
                border_style="dim",
            )
        )
