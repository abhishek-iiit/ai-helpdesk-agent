"""
demo/workshop_demo.py
=====================
Interactive Workshop Demo Script

This script runs through 5 carefully crafted scenarios that demonstrate
every component of the AI IT Helpdesk architecture:

Scenario 1: Knowledge Base Query      → LangChain tool use
Scenario 2: Service Status Check      → LangGraph routing
Scenario 3: Ticket Creation           → Tool with side effects
Scenario 4: Service + Ticket (combo)  → Multi-step reasoning
Scenario 5: Escalation                → Critical path routing

After each scenario, we explain what happened in the graph.
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.columns import Columns
from rich.console import Group
from rich.text import Text
from rich import box

from agent.helpdesk_agent import HelpdeskAgent
from observability.langsmith_tracer import print_langsmith_status
from observability.langfuse_tracer import print_langfuse_status
from config.settings import settings

console = Console(width=100)

# ─────────────────────────────────────────────────────────────
# Workshop Scenarios
# ─────────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "id": 1,
        "title": "Knowledge Base Query",
        "question": "How do I reset my password?",
        "user_email": "alice@company.com",
        "expected_intent": "knowledge_base",
        "teaches": [
            "LangChain: Tool definition with @tool decorator",
            "LangGraph: Routing to knowledge_base_node",
            "LangSmith: See the prompt + LLM response in trace",
            "LangFuse: Token usage tracked for this query",
        ],
    },
    {
        "id": 2,
        "title": "Service Status Check",
        "question": "Is the email server working? I'm not receiving emails.",
        "user_email": "bob@company.com",
        "expected_intent": "service_status",
        "teaches": [
            "LangChain: check_service_status tool execution",
            "LangGraph: Conditional edge routes to service_status_node",
            "LangSmith: View entity extraction (service='email')",
            "LangFuse: Latency for status check vs knowledge query",
        ],
    },
    {
        "id": 3,
        "title": "Support Ticket Creation",
        "question": "My laptop screen is cracked and I need a replacement. Please create a support ticket.",
        "user_email": "charlie@company.com",
        "expected_intent": "create_ticket",
        "teaches": [
            "LangChain: create_support_ticket tool with auto-categorization",
            "LangGraph: Tool node returns ticket_id to state",
            "LangSmith: Full trace shows state transitions",
            "LangFuse: Track ticket creation rate over time",
        ],
    },
    {
        "id": 4,
        "title": "VPN Not Working (Compound Issue)",
        "question": "My VPN keeps disconnecting since this morning. Is there an outage? If not, please create a ticket.",
        "user_email": "diana@company.com",
        "expected_intent": "service_status",
        "teaches": [
            "LangChain: Agent reasoning across multiple tools",
            "LangGraph: Service status → ticket creation flow",
            "LangSmith: Multi-step trace visualization",
            "LangFuse: Cost comparison for simple vs complex queries",
        ],
    },
    {
        "id": 5,
        "title": "Security Escalation (Critical)",
        "question": "URGENT: I received a suspicious email and clicked a link. I think my account might be compromised!",
        "user_email": "eve@company.com",
        "expected_intent": "escalate",
        "teaches": [
            "LangChain: Escalation path with P1 ticket creation",
            "LangGraph: Critical routing to escalate_node",
            "LangSmith: See confidence scores in classification",
            "LangFuse: Alert thresholds for critical events",
        ],
    },
]


# ─────────────────────────────────────────────────────────────
# Display Helpers
# ─────────────────────────────────────────────────────────────
def print_header():
    """Print the workshop banner."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🤖 AI IT HELPDESK AGENT[/bold cyan]\n"
            "[white]Workshop Demo: LangChain + LangGraph + LangSmith + LangFuse[/white]\n\n"
            "[dim]Built with:[/dim]\n"
            "  [yellow]⛓  LangChain[/yellow]  — Tool definitions & LLM orchestration\n"
            "  [green]◈  LangGraph[/green]  — Stateful workflow engine\n"
            "  [blue]◉  LangSmith[/blue]  — Developer tracing & debugging\n"
            "  [magenta]◈  LangFuse[/magenta]  — Production cost & analytics",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def print_architecture_diagram():
    """Print the system architecture as ASCII art."""
    console.print(
        Panel(
            """[bold white]SYSTEM PIPELINE:[/bold white]

[white]User Question[/white]
      [cyan]↓[/cyan]
[yellow]┌─────────────────────────────────┐[/yellow]
[yellow]│      classify_intent (LLM)      │[/yellow]  [dim]← LangChain prompt template[/dim]
[yellow]└──────────────┬──────────────────┘[/yellow]
               [cyan]↓[/cyan] [dim](conditional routing)[/dim]
[green]┌──────────┬──────────┬────────┬─────────┐[/green]
[green]│knowledge │ service  │ticket  │escalate │[/green]  [dim]← LangGraph nodes[/dim]
[green]│_base     │ _status  │_create │         │[/green]
[green]└──────┬───┴────┬─────┴───┬────┴────┬────┘[/green]
       [cyan]└────────┴─────────┴────────┘[/cyan]
               [cyan]↓[/cyan]
[blue]┌─────────────────────────────────┐[/blue]
[blue]│    generate_response (LLM)      │[/blue]  [dim]← Response synthesis[/dim]
[blue]└─────────────────────────────────┘[/blue]
               [cyan]↓[/cyan]
        [white]Final Answer[/white]
               [cyan]↓[/cyan]
[yellow]     LangSmith Trace[/yellow] [magenta]+ LangFuse Analytics[/magenta]""",
            title="[bold]Architecture[/bold]",
            border_style="white",
        )
    )


def print_scenario_header(scenario: dict):
    """Print a scenario header."""
    console.print()
    console.print(Rule(
        f"[bold cyan]Scenario {scenario['id']}: {scenario['title']}[/bold cyan]",
        style="cyan",
    ))

    console.print(
        Panel(
            f"[bold white]User Question:[/bold white]\n[yellow]\"{scenario['question']}\"[/yellow]\n\n"
            f"[bold white]User:[/bold white] {scenario['user_email']}\n"
            f"[bold white]Expected Intent:[/bold white] [green]{scenario['expected_intent']}[/green]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def print_teaches(scenario: dict, actual_intent: str, latency_ms: int, ticket_id: str | None):
    """Print the educational summary after each scenario."""
    # Results table
    results_table = Table(box=box.ROUNDED, border_style="green", show_header=False)
    results_table.add_column("Key", style="dim", width=20)
    results_table.add_column("Value")
    results_table.add_row("Intent Detected", f"[green]{actual_intent}[/green]")
    results_table.add_row("Latency", f"{latency_ms}ms")
    if ticket_id:
        results_table.add_row("Ticket Created", f"[yellow]{ticket_id}[/yellow]")
    results_table.add_row("LangSmith", "✅ Trace recorded" if settings.langsmith_enabled else "❌ Disabled")
    results_table.add_row("LangFuse", "✅ Analytics recorded" if settings.langfuse_enabled else "❌ Disabled")

    # Concepts taught
    teaches_text = "\n".join(f"[cyan]→[/cyan] {t}" for t in scenario["teaches"])

    console.print(
        Panel(
            Group(
                Text("📊 Results:", style="bold white"),
                results_table,
                Text(""),
                Text("📚 What this demonstrates:", style="bold white"),
                Text.from_markup(teaches_text),
            ),
            title=f"[bold]Scenario {scenario['id']} Complete[/bold]",
            border_style="green",
        )
    )


def print_final_summary(results: list[dict]):
    """Print workshop summary table."""
    console.print()
    console.print(Rule("[bold cyan]Workshop Summary[/bold cyan]", style="cyan"))

    table = Table(
        title="All Scenarios Results",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Scenario", width=30)
    table.add_column("Intent", width=18)
    table.add_column("Ticket", width=12)
    table.add_column("Latency", width=10)

    for r in results:
        table.add_row(
            str(r["scenario_id"]),
            r["title"][:28],
            f"[green]{r['intent']}[/green]",
            f"[yellow]{r['ticket_id']}[/yellow]" if r['ticket_id'] else "[dim]—[/dim]",
            f"{r['latency_ms']}ms",
        )

    console.print(table)

    # Technology recap
    console.print()
    console.print(
        Panel(
            "[bold]Technologies Used in This Demo:[/bold]\n\n"
            "[yellow]⛓  LangChain[/yellow]\n"
            "   • Defined 3 tools: search_knowledge_base, check_service_status, create_support_ticket\n"
            "   • Used ChatPromptTemplate for structured prompts\n"
            "   • ChatGoogleGenerativeAI for LLM calls with temperature control\n\n"
            "[green]◈  LangGraph[/green]\n"
            "   • StateGraph with HelpdeskState (shared state)\n"
            "   • 6 nodes: classify_intent + 4 tool nodes + generate_response\n"
            "   • Conditional edges for dynamic routing based on intent\n"
            "   • Deterministic, inspectable workflow execution\n\n"
            "[blue]◉  LangSmith[/blue]\n"
            "   • Automatic tracing via LANGCHAIN_TRACING_V2=true\n"
            "   • Full prompt/response inspection for each LLM call\n"
            "   • Token usage and latency per node\n"
            "   • Ideal for: development, debugging, prompt iteration\n\n"
            "[magenta]◈  LangFuse[/magenta]\n"
            "   • Callback-based tracing for production monitoring\n"
            "   • Cost per conversation tracking\n"
            "   • User-level and session-level analytics\n"
            "   • Ideal for: production, cost control, business metrics",
            title="[bold cyan]Workshop Takeaways[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


# ─────────────────────────────────────────────────────────────
# Main Demo Runner
# ─────────────────────────────────────────────────────────────
def run_demo(scenario_ids: list[int] | None = None, pause_between: bool = True):
    """
    Run the workshop demo scenarios.

    Args:
        scenario_ids: List of scenario IDs to run (default: all)
        pause_between: Pause between scenarios for discussion
    """
    print_header()
    print_architecture_diagram()

    # Print observability status
    console.print()
    print_langsmith_status()
    console.print()
    print_langfuse_status()
    console.print()

    # Check OpenAI key
    if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your_google_api_key_here":
        console.print(
            Panel(
                "[red]❌ GOOGLE_API_KEY not set![/red]\n\n"
                "Please add your Google API key to .env:\n"
                "GOOGLE_API_KEY=AIza...\n\n"
                "Get a free key at: https://aistudio.google.com/app/apikey",
                title="[bold red]Configuration Error[/bold red]",
                border_style="red",
            )
        )
        return

    agent = HelpdeskAgent()
    scenarios_to_run = [s for s in SCENARIOS if scenario_ids is None or s["id"] in scenario_ids]
    results = []

    for scenario in scenarios_to_run:
        print_scenario_header(scenario)

        if pause_between:
            console.print("[dim]Press Enter to run this scenario...[/dim]")
            input()

        # Run the scenario
        result = agent.ask(
            question=scenario["question"],
            user_email=scenario["user_email"],
            verbose=True,
        )

        results.append({
            "scenario_id": scenario["id"],
            "title": scenario["title"],
            "intent": result["intent"],
            "ticket_id": result["ticket_id"],
            "latency_ms": result["latency_ms"],
        })

        print_teaches(scenario, result["intent"], result["latency_ms"], result["ticket_id"])

        if pause_between and scenario != scenarios_to_run[-1]:
            console.print("\n[dim]Press Enter for next scenario...[/dim]")
            input()
        else:
            time.sleep(1)

    print_final_summary(results)

    # Final observability links
    if settings.langsmith_enabled:
        console.print(f"\n[blue]🔍 View all traces in LangSmith:[/blue] https://smith.langchain.com")
    if settings.langfuse_enabled:
        console.print(f"[magenta]📊 View analytics in LangFuse:[/magenta] {settings.LANGFUSE_HOST}")


if __name__ == "__main__":
    run_demo(pause_between=True)
