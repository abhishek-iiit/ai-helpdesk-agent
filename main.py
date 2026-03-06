"""
main.py
=======
Entry Point for the AI IT Helpdesk Agent

Usage:
    python main.py                  # Interactive CLI chat
    python main.py --demo           # Run full workshop demo
    python main.py --demo --auto    # Demo without pauses
    python main.py --api            # Start FastAPI server
    python main.py --scenario 1,3  # Run specific demo scenarios
    python main.py --ask "question" # Ask a single question

Workshop Note:
    This file is the single entry point for all interaction modes.
    It demonstrates clean CLI design alongside the AI components.
"""

import argparse
import sys
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from config.settings import settings
from agent.helpdesk_agent import HelpdeskAgent
from observability.langsmith_tracer import print_langsmith_status
from observability.langfuse_tracer import print_langfuse_status

console = Console()


def run_interactive_cli():
    """
    Interactive CLI chat mode.

    Starts a REPL loop where the user can type questions and
    get real-time responses from the AI agent.
    """
    agent = HelpdeskAgent()

    console.print(
        Panel(
            "[bold cyan]🤖 ARIA — AI IT Helpdesk[/bold cyan]\n"
            "[dim]Type your IT support question and press Enter.\n"
            "Type 'exit' or 'quit' to stop. Type 'help' for example questions.[/dim]",
            border_style="cyan",
        )
    )

    # Show example questions
    examples = [
        "How do I reset my password?",
        "Is the VPN working right now?",
        "My email is not syncing",
        "Please create a ticket — my laptop is broken",
        "I got a phishing email!",
    ]
    console.print("\n[dim]Example questions:[/dim]")
    for q in examples:
        console.print(f"  [dim cyan]→[/dim cyan] [italic]{q}[/italic]")
    console.print()

    while True:
        try:
            question = Prompt.ask("[bold green]You[/bold green]")

            if question.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break
            elif question.lower() == "help":
                for q in examples:
                    console.print(f"  [cyan]→[/cyan] {q}")
                continue
            elif question.lower() == "status":
                print_langsmith_status()
                print_langfuse_status()
                continue
            elif not question.strip():
                continue

            result = agent.ask(question=question, verbose=True)

            if result.get("ticket_id"):
                console.print(f"\n[yellow]📋 Ticket: {result['ticket_id']}[/yellow]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye! 👋[/dim]")
            break


def run_api_server():
    """Start the FastAPI server."""
    from api.app import app

    console.print(
        Panel(
            f"[bold green]🚀 Starting FastAPI Server[/bold green]\n\n"
            f"URL:    [cyan]http://localhost:{settings.API_PORT}[/cyan]\n"
            f"Docs:   [cyan]http://localhost:{settings.API_PORT}/docs[/cyan]\n"
            f"Health: [cyan]http://localhost:{settings.API_PORT}/status[/cyan]",
            border_style="green",
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level="info",
    )


def run_single_question(question: str):
    """Ask a single question and print the result."""
    agent = HelpdeskAgent()
    result = agent.ask(question=question, verbose=True)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="AI IT Helpdesk Agent — LangChain + LangGraph Workshop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                         # Interactive CLI
  python main.py --demo                  # Workshop demo (with pauses)
  python main.py --demo --auto           # Workshop demo (no pauses)
  python main.py --scenario 1            # Run scenario 1 only
  python main.py --scenario 1,3,5        # Run scenarios 1, 3, and 5
  python main.py --api                   # Start REST API server
  python main.py --ask "VPN not working" # Single question
        """,
    )
    parser.add_argument("--demo", action="store_true", help="Run the workshop demo")
    parser.add_argument("--auto", action="store_true", help="Run demo without pausing")
    parser.add_argument("--scenario", type=str, help="Comma-separated scenario IDs (e.g., 1,3,5)")
    parser.add_argument("--api", action="store_true", help="Start FastAPI server")
    parser.add_argument("--ask", type=str, help="Ask a single question")
    parser.add_argument("--status", action="store_true", help="Show integration status")

    args = parser.parse_args()

    # ── Show configuration status ───────────────────────────────
    if args.status:
        console.print("\n[bold]Integration Status:[/bold]")
        console.print(f"  Gemini:    {'✅' if settings.GOOGLE_API_KEY else '❌'} ({settings.GEMINI_MODEL})")
        print_langsmith_status()
        print_langfuse_status()
        return

    # ── Validate Google API key for non-status modes ─────────────
    if not args.status:
        if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your_google_api_key_here":
            console.print(
                Panel(
                    "[red]❌ GOOGLE_API_KEY is not set![/red]\n\n"
                    "1. Copy the example env file:\n"
                    "   [cyan]cp .env.example .env[/cyan]\n\n"
                    "2. Add your Google API key to .env:\n"
                    "   [cyan]GOOGLE_API_KEY=AIza...[/cyan]\n\n"
                    "Get a free key at: https://aistudio.google.com/app/apikey\n\n"
                    "3. Optionally add LangSmith and LangFuse keys for tracing.",
                    title="[bold red]Setup Required[/bold red]",
                    border_style="red",
                )
            )
            sys.exit(1)

    # ── Route to appropriate mode ───────────────────────────────
    if args.api:
        run_api_server()

    elif args.demo or args.scenario:
        from demo.workshop_demo import run_demo
        scenario_ids = None
        if args.scenario:
            scenario_ids = [int(x.strip()) for x in args.scenario.split(",")]
        run_demo(scenario_ids=scenario_ids, pause_between=not args.auto)

    elif args.ask:
        run_single_question(args.ask)

    else:
        # Default: interactive CLI
        run_interactive_cli()


if __name__ == "__main__":
    main()
