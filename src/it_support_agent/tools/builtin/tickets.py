"""Ticketing / escalation tools."""

import json
import uuid
from typing import Annotated

from pydantic import Field

from it_support_agent.core.exceptions import ToolError
from it_support_agent.tools import tool


@tool
def escalate_to_engineer(
    summary: Annotated[
        str, Field(description="A short summary of the issue, what was checked, and what was tried.")
    ],
) -> str:
    """Escalates the issue to a human engineer when automated fixes fail or the error is unknown."""
    if not summary.strip():
        raise ToolError("summary must not be empty")
    print("-> TOOL: Escalating to human...")
    ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"  # mock ticket ID
    return json.dumps(
        {
            "status": "success",
            "ticket_id": ticket_id,
            "message": f"Ticket {ticket_id} created and assigned to an engineer",
        }
    )
