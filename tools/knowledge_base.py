"""
tools/knowledge_base.py
=======================
IT Knowledge Base Search Tool

Workshop Note:
    In production this would be a RAG (Retrieval-Augmented Generation) system
    using a vector database (Pinecone, Weaviate, Chroma) + embeddings.

    For the workshop we use a keyword-based mock to keep focus on
    LangChain + LangGraph + Observability concepts — not vector DBs.
"""

from langchain_core.tools import tool

# ─────────────────────────────────────────────────────────────
# Mock Knowledge Base
# In production: replace with vector store similarity search
# ─────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = {
    "password": {
        "keywords": ["password", "reset", "forgot", "locked", "credentials", "login", "sign in", "account"],
        "title": "Password Reset & Account Access",
        "answer": (
            "🔑 **Password Reset Instructions:**\n"
            "1. Visit https://reset.company.com\n"
            "2. Enter your Employee ID\n"
            "3. Check your registered personal email for a one-time OTP\n"
            "4. Set a new password (min 8 chars: uppercase, lowercase, number, special char)\n\n"
            "⚠️ After 5 failed attempts, your account locks for 30 minutes.\n"
            "📞 For immediate help: Call IT Helpdesk at ext. 4357 (HELP)"
        ),
    },
    "vpn": {
        "keywords": ["vpn", "remote", "connect", "access", "network", "cisco", "anyconnect", "tunnel"],
        "title": "VPN & Remote Access",
        "answer": (
            "🔒 **VPN Setup Guide:**\n"
            "1. Download Cisco AnyConnect from https://it.company.com/vpn\n"
            "2. Server address: vpn.company.com\n"
            "3. Use your domain username (without @company.com) and domain password\n"
            "4. Select 'Corporate-Full-Tunnel' profile for full access\n\n"
            "**Troubleshooting:**\n"
            "• Ensure your device is on the approved device list\n"
            "• Disable any third-party VPN clients before connecting\n"
            "• Check that your antivirus is up-to-date (required for VPN access)\n"
            "• Certificate errors? Run: sudo security add-trusted-cert <cert>"
        ),
    },
    "email": {
        "keywords": ["email", "outlook", "mail", "calendar", "exchange", "smtp", "imap", "inbox"],
        "title": "Email & Calendar Setup",
        "answer": (
            "📧 **Email Configuration:**\n"
            "**Outlook (Recommended):**\n"
            "• Add your company account: yourname@company.com\n"
            "• Outlook will auto-discover settings\n\n"
            "**Manual Settings:**\n"
            "• IMAP: mail.company.com, Port 993, SSL\n"
            "• SMTP: smtp.company.com, Port 587, STARTTLS\n"
            "• Use your full email address and domain password\n\n"
            "**Calendar Sharing:** Use Outlook > Calendar > Share > Add People"
        ),
    },
    "software": {
        "keywords": ["software", "install", "license", "application", "app", "tool", "program"],
        "title": "Software Installation & Licenses",
        "answer": (
            "💿 **Software Requests:**\n"
            "• Browse approved software at https://it.company.com/software\n"
            "• Self-service installs available via Company App Store\n"
            "• Licensed software requires manager approval (submit via Jira IT Board)\n\n"
            "**Common Tools Available:**\n"
            "• Microsoft Office 365 — auto-installed on all company devices\n"
            "• JetBrains IDEs — request via IT Portal\n"
            "• Adobe Creative Cloud — requires Creative Team approval\n"
            "• Zoom/Teams — available in App Store\n\n"
            "Note: Unlicensed software is prohibited per Security Policy SEC-002"
        ),
    },
    "wifi": {
        "keywords": ["wifi", "wireless", "internet", "network", "connection", "ssid"],
        "title": "WiFi & Network Access",
        "answer": (
            "📶 **WiFi Networks:**\n"
            "• **Corp-Secure** (recommended): WPA2-Enterprise, use domain credentials\n"
            "• **Corp-Guest**: For visitors — no internal resource access\n"
            "• **Corp-IOT**: For IoT/lab devices only\n\n"
            "**Setup for New Devices:**\n"
            "1. Connect to Corp-Guest first\n"
            "2. Register device at https://it.company.com/device-registration\n"
            "3. Install company certificate\n"
            "4. Connect to Corp-Secure"
        ),
    },
    "hardware": {
        "keywords": ["laptop", "computer", "hardware", "monitor", "keyboard", "mouse", "printer", "device", "equipment"],
        "title": "Hardware Requests & Equipment",
        "answer": (
            "🖥️ **Hardware Request Process:**\n"
            "1. Submit request via Jira IT Board (https://jira.company.com/it)\n"
            "2. Select category: Laptop / Monitor / Peripherals / Other\n"
            "3. Manager approval required for requests >$500\n"
            "4. Standard processing: 3-5 business days\n\n"
            "**Emergency Loaner Equipment:** Available at IT Desk (Floor 2, Room 201)\n"
            "**Laptop Issues:** Book a 30-min slot at https://it.company.com/booking"
        ),
    },
    "security": {
        "keywords": ["security", "phishing", "virus", "malware", "suspicious", "hack", "breach", "2fa", "mfa"],
        "title": "Security Policies & Incidents",
        "answer": (
            "🛡️ **Security Policies:**\n"
            "• MFA required for all company accounts (authenticator app preferred)\n"
            "• Passwords must be changed every 90 days\n"
            "• Never share credentials — IT will NEVER ask for your password\n\n"
            "**Report a Security Incident:**\n"
            "• Email: security@company.com (24/7 monitored)\n"
            "• Hotline: ext. 9911\n"
            "• Phishing emails: Forward to phishing@company.com\n\n"
            "⚡ Suspected breach? Call security hotline IMMEDIATELY — do not power off the device"
        ),
    },
    "onboarding": {
        "keywords": ["new", "onboard", "setup", "first day", "getting started", "checklist", "join"],
        "title": "IT Onboarding Checklist",
        "answer": (
            "🎉 **IT Onboarding Checklist:**\n"
            "Day 1:\n"
            "✅ Collect laptop from IT Desk with your employee ID\n"
            "✅ Set up your password at https://onboard.company.com\n"
            "✅ Configure MFA on your authenticator app\n"
            "✅ Connect to Corp-Secure WiFi\n\n"
            "Week 1:\n"
            "✅ Install required software from Company App Store\n"
            "✅ Set up email on all devices\n"
            "✅ Complete Security Awareness Training (mandatory)\n"
            "✅ Join #it-help Slack channel for quick support"
        ),
    },
    "slack": {
        "keywords": ["slack", "teams", "chat", "messaging", "communication", "channel"],
        "title": "Slack & Team Communication",
        "answer": (
            "💬 **Slack Setup:**\n"
            "• Workspace: company.slack.com\n"
            "• Sign in with your company Google account (SSO)\n"
            "• Install desktop app from https://slack.com/downloads\n\n"
            "**Key Channels:**\n"
            "• #it-help — IT support (fastest response)\n"
            "• #announcements — Company-wide updates\n"
            "• #engineering — Dev team\n"
            "• #random — Watercooler chat\n\n"
            "**Retention Policy:** Messages older than 1 year are archived (not deleted)"
        ),
    },
    "leave": {
        "keywords": ["leave", "vacation", "pto", "sick", "time off", "holiday", "absence"],
        "title": "Leave & Time-Off Policies",
        "answer": (
            "🏖️ **Leave Policy (IT Perspective):**\n"
            "• Submit leave requests in Workday (https://workday.company.com)\n"
            "• IT access remains active during leave\n"
            "• For extended leave (>30 days): IT will temporarily suspend VPN access\n"
            "• Set email auto-reply before going on leave\n\n"
            "**For HR Leave Policies** contact HR at hr@company.com\n"
            "**Public Holidays List:** https://hr.company.com/holidays"
        ),
    },
}


def _keyword_search(query: str) -> tuple[str, str, float]:
    """
    Find best matching knowledge base article using keyword scoring.

    Returns: (title, answer, confidence_score)

    Workshop Note:
        Production systems use semantic search with embeddings for much
        better accuracy. This mock demonstrates the CONCEPT.
    """
    query_lower = query.lower()
    best_match = None
    best_score = 0.0

    for key, article in KNOWLEDGE_BASE.items():
        score = sum(
            1 for kw in article["keywords"]
            if kw in query_lower
        )
        # Normalize by number of keywords
        normalized = score / len(article["keywords"])
        if normalized > best_score:
            best_score = normalized
            best_match = article

    if best_match and best_score > 0:
        return best_match["title"], best_match["answer"], best_score

    return (
        "General IT Support",
        (
            "I couldn't find a specific policy for your question. "
            "Please contact the IT Helpdesk directly:\n"
            "• 📧 Email: it-help@company.com\n"
            "• 📞 Phone: ext. 4357 (HELP)\n"
            "• 💬 Slack: #it-help\n"
            "• 🎫 Portal: https://jira.company.com/it\n\n"
            "Support hours: Mon–Fri 8am–8pm EST"
        ),
        0.0,
    )


# ─────────────────────────────────────────────────────────────
# LangChain Tool Definition
# ─────────────────────────────────────────────────────────────
@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the IT knowledge base for policies, procedures, and how-to guides.

    Use this tool when the user asks about:
    - How to do something (password reset, VPN setup, email config)
    - Company IT policies and procedures
    - Software installation and licensing
    - Hardware requests
    - Security guidelines
    - Onboarding steps

    Args:
        query: The user's question or search terms

    Returns:
        Relevant IT policy or procedure information
    """
    title, answer, confidence = _keyword_search(query)

    result = f"📚 **Knowledge Base: {title}**\n"
    result += f"_(Confidence: {confidence:.0%})_\n\n"
    result += answer

    return result
