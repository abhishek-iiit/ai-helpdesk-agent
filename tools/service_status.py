"""
tools/service_status.py
=======================
IT Service Status Checker Tool

Workshop Note:
    In production this would integrate with:
    - Prometheus/Grafana for metrics
    - PagerDuty for incident management
    - StatusPage.io for public status
    - AWS CloudWatch / Azure Monitor for cloud services

    This mock demonstrates the CONCEPT with realistic data.
"""

import random
from datetime import datetime, timedelta
from langchain_core.tools import tool

# ─────────────────────────────────────────────────────────────
# Mock Service Registry
# In production: query real monitoring APIs
# ─────────────────────────────────────────────────────────────
SERVICES = {
    "vpn": {
        "name": "VPN (Cisco AnyConnect)",
        "status": "operational",
        "uptime": "99.9%",
        "last_checked": "2 minutes ago",
        "incident": None,
    },
    "email": {
        "name": "Email (Microsoft Exchange)",
        "status": "degraded",
        "uptime": "97.2%",
        "last_checked": "1 minute ago",
        "incident": "Slow email delivery affecting ~15% of users. Engineering is investigating. ETA: 2 hours.",
    },
    "slack": {
        "name": "Slack",
        "status": "operational",
        "uptime": "99.95%",
        "last_checked": "30 seconds ago",
        "incident": None,
    },
    "jira": {
        "name": "Jira / Confluence",
        "status": "operational",
        "uptime": "99.8%",
        "last_checked": "5 minutes ago",
        "incident": None,
    },
    "github": {
        "name": "GitHub Enterprise",
        "status": "operational",
        "uptime": "99.99%",
        "last_checked": "1 minute ago",
        "incident": None,
    },
    "aws": {
        "name": "AWS Cloud (us-east-1)",
        "status": "operational",
        "uptime": "99.95%",
        "last_checked": "30 seconds ago",
        "incident": None,
    },
    "database": {
        "name": "Production Database (PostgreSQL)",
        "status": "operational",
        "uptime": "99.99%",
        "last_checked": "15 seconds ago",
        "incident": None,
    },
    "hr_portal": {
        "name": "HR Portal (Workday)",
        "status": "maintenance",
        "uptime": "98.5%",
        "last_checked": "3 minutes ago",
        "incident": "Scheduled maintenance window: Fri 11pm – Sat 3am EST. Some features unavailable.",
    },
    "wifi": {
        "name": "Corporate WiFi",
        "status": "operational",
        "uptime": "99.7%",
        "last_checked": "1 minute ago",
        "incident": None,
    },
    "ci_cd": {
        "name": "CI/CD Pipeline (Jenkins)",
        "status": "operational",
        "uptime": "99.2%",
        "last_checked": "2 minutes ago",
        "incident": None,
    },
    "zoom": {
        "name": "Zoom",
        "status": "operational",
        "uptime": "99.8%",
        "last_checked": "2 minutes ago",
        "incident": None,
    },
    "okta": {
        "name": "Okta SSO / Identity Provider",
        "status": "operational",
        "uptime": "99.99%",
        "last_checked": "30 seconds ago",
        "incident": None,
    },
}

# Status emoji mapping for nice output
STATUS_EMOJI = {
    "operational": "✅",
    "degraded": "⚠️",
    "outage": "🔴",
    "maintenance": "🔧",
    "unknown": "❓",
}


def _find_service(service_query: str) -> dict | None:
    """
    Find a service by name or keyword matching.
    Returns service dict or None if not found.
    """
    query = service_query.lower().strip()

    # Direct key match
    if query in SERVICES:
        return {"key": query, **SERVICES[query]}

    # Keyword matching
    keyword_map = {
        "vpn": ["vpn", "remote", "anyconnect", "cisco"],
        "email": ["email", "mail", "outlook", "exchange", "inbox"],
        "slack": ["slack", "chat", "messaging"],
        "jira": ["jira", "confluence", "ticket", "project management"],
        "github": ["github", "git", "code", "repository", "repo"],
        "aws": ["aws", "cloud", "amazon", "ec2", "s3"],
        "database": ["database", "db", "postgres", "postgresql", "sql"],
        "hr_portal": ["hr", "workday", "payroll", "human resources"],
        "wifi": ["wifi", "wireless", "internet", "network"],
        "ci_cd": ["ci", "cd", "jenkins", "pipeline", "build", "deploy"],
        "zoom": ["zoom", "video", "meeting", "call"],
        "okta": ["okta", "sso", "login", "authentication", "identity"],
    }

    for service_key, keywords in keyword_map.items():
        if any(kw in query for kw in keywords):
            return {"key": service_key, **SERVICES[service_key]}

    return None


def get_all_services_status() -> list[dict]:
    """Return status of all services (used by API endpoint)."""
    return [
        {"key": key, **service}
        for key, service in SERVICES.items()
    ]


# ─────────────────────────────────────────────────────────────
# LangChain Tool Definition
# ─────────────────────────────────────────────────────────────
@tool
def check_service_status(service: str) -> str:
    """
    Check the real-time operational status of IT services and systems.

    Use this tool when the user asks about:
    - Whether a service is working or down
    - Service outages, degradation, or maintenance windows
    - Status of VPN, Email, Slack, GitHub, AWS, Database, etc.

    Args:
        service: Name of the service to check (e.g., "VPN", "email", "Slack")

    Returns:
        Current operational status with any incident details
    """
    svc = _find_service(service)

    if not svc:
        # List available services if not found
        available = ", ".join(SERVICES.keys())
        return (
            f"❓ Service '{service}' not found in our monitoring system.\n\n"
            f"**Available services:** {available}\n\n"
            f"For unlisted services, check: https://status.company.com"
        )

    emoji = STATUS_EMOJI.get(svc["status"], "❓")
    status_upper = svc["status"].upper()

    result = f"{emoji} **{svc['name']}** — {status_upper}\n"
    result += f"• Uptime (30 days): {svc['uptime']}\n"
    result += f"• Last checked: {svc['last_checked']}\n"

    if svc["incident"]:
        result += f"\n⚡ **Active Incident:**\n{svc['incident']}\n"
        result += f"\n📋 Incident updates: https://status.company.com"
    else:
        result += f"\n✓ All systems normal. No active incidents."

    return result
