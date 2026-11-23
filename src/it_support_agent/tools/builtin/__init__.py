"""Built-in tools. Add a module here and list its tool in BUILTIN_TOOLS."""

from it_support_agent.tools.builtin.servers import fetch_recent_logs, get_server_health, restart_service
from it_support_agent.tools.builtin.tickets import escalate_to_engineer

BUILTIN_TOOLS = [get_server_health, fetch_recent_logs, restart_service, escalate_to_engineer]
