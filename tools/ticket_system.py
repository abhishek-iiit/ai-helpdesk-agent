"""
tools/ticket_system.py
======================
IT Support Ticket Creation Tool

Workshop Note:
    In production this would integrate with:
    - Jira Service Management
    - ServiceNow
    - Zendesk
    - Freshservice

    This mock maintains an in-memory ticket store to demonstrate
    the concept with realistic ticket IDs and metadata.
"""

import uuid
from datetime import datetime
from langchain_core.tools import tool

# ─────────────────────────────────────────────────────────────
# In-Memory Ticket Store
# In production: this writes to Jira / ServiceNow API
# ─────────────────────────────────────────────────────────────
_ticket_counter = 420  # Starts at 420 so first ticket is #421
_tickets: list[dict] = []


def _get_next_ticket_id() -> str:
    global _ticket_counter
    _ticket_counter += 1
    return f"INC-{_ticket_counter}"


def _categorize_issue(description: str) -> tuple[str, str, str]:
    """
    Auto-categorize issue and assign priority based on keywords.

    Returns: (category, priority, assigned_team)
    """
    desc_lower = description.lower()

    # Priority keywords
    critical_keywords = ["down", "outage", "all users", "production", "breach", "hack", "urgent", "critical"]
    high_keywords = ["not working", "broken", "error", "failed", "cannot", "blocked", "urgent"]

    # Categorization rules
    categories = {
        "Network & VPN": ["vpn", "network", "wifi", "internet", "connection"],
        "Email & Calendar": ["email", "mail", "outlook", "calendar"],
        "Account & Access": ["password", "locked", "access", "login", "account", "credentials"],
        "Hardware": ["laptop", "computer", "monitor", "keyboard", "mouse", "printer", "hardware"],
        "Software & Apps": ["software", "install", "application", "license", "crash", "freeze"],
        "Security": ["phishing", "virus", "malware", "suspicious", "breach", "hack"],
        "Cloud & Infrastructure": ["aws", "cloud", "server", "database", "deploy"],
        "General IT Support": [],
    }

    # Determine category
    category = "General IT Support"
    for cat, keywords in categories.items():
        if any(kw in desc_lower for kw in keywords):
            category = cat
            break

    # Determine priority
    if any(kw in desc_lower for kw in critical_keywords):
        priority = "P1 - Critical"
        assigned_team = "On-Call Team"
    elif any(kw in desc_lower for kw in high_keywords):
        priority = "P2 - High"
        assigned_team = "IT Support Team"
    else:
        priority = "P3 - Medium"
        assigned_team = "IT Support Team"

    return category, priority, assigned_team


def get_all_tickets() -> list[dict]:
    """Return all tickets (used by API endpoint)."""
    return _tickets.copy()


def get_ticket_by_id(ticket_id: str) -> dict | None:
    """Find a ticket by ID."""
    return next((t for t in _tickets if t["id"] == ticket_id), None)


# ─────────────────────────────────────────────────────────────
# LangChain Tool Definition
# ─────────────────────────────────────────────────────────────
@tool
def create_support_ticket(
    issue: str,
    user_email: str = "user@company.com",
    severity: str = "auto",
) -> str:
    """
    Create an IT support ticket for issues that need human follow-up.

    Use this tool when:
    - The user reports a technical problem that can't be resolved via knowledge base
    - The service is down and the user needs active assistance
    - The user explicitly asks to create/raise/log a ticket
    - The issue requires hands-on IT support

    Args:
        issue: Detailed description of the problem
        user_email: User's email address (default: user@company.com)
        severity: Ticket priority override (P1/P2/P3) or "auto" for auto-detection

    Returns:
        Ticket confirmation with ID, priority, and next steps
    """
    ticket_id = _get_next_ticket_id()
    category, priority, assigned_team = _categorize_issue(issue)

    # Allow manual priority override
    if severity.upper() in ("P1", "P2", "P3"):
        priority_map = {"P1": "P1 - Critical", "P2": "P2 - High", "P3": "P3 - Medium"}
        priority = priority_map[severity.upper()]

    # SLA times by priority
    sla_map = {
        "P1 - Critical": "1 hour",
        "P2 - High": "4 hours",
        "P3 - Medium": "1 business day",
    }

    ticket = {
        "id": ticket_id,
        "issue": issue,
        "category": category,
        "priority": priority,
        "assigned_to": assigned_team,
        "reporter": user_email,
        "status": "Open",
        "created_at": datetime.now().isoformat(),
        "sla": sla_map.get(priority, "1 business day"),
        "jira_url": f"https://jira.company.com/browse/{ticket_id}",
    }

    _tickets.append(ticket)

    sla = sla_map.get(priority, "1 business day")

    return (
        f"✅ **Support Ticket Created Successfully!**\n\n"
        f"🎫 **Ticket ID:** {ticket_id}\n"
        f"📁 **Category:** {category}\n"
        f"🔴 **Priority:** {priority}\n"
        f"👥 **Assigned To:** {assigned_team}\n"
        f"⏱️ **SLA Response Time:** {sla}\n"
        f"📊 **Status:** Open\n\n"
        f"📋 **Issue Summary:**\n{issue[:200]}{'...' if len(issue) > 200 else ''}\n\n"
        f"🔗 **Track your ticket:** {ticket['jira_url']}\n\n"
        f"You'll receive email updates at {user_email}. "
        f"For urgent issues, mention your ticket ID when calling IT at ext. 4357."
    )
