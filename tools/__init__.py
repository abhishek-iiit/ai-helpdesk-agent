from tools.knowledge_base import search_knowledge_base
from tools.service_status import check_service_status
from tools.ticket_system import create_support_ticket

# All tools available to the agent
ALL_TOOLS = [
    search_knowledge_base,
    check_service_status,
    create_support_ticket,
]

__all__ = [
    "search_knowledge_base",
    "check_service_status",
    "create_support_ticket",
    "ALL_TOOLS",
]
