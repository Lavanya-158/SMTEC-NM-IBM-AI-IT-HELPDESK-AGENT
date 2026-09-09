"""
AI IT Helpdesk Agent
A self-contained Python demo requiring only the Python standard library.

Run:
    python ai_it_helpdesk_agent.py
"""

import difflib
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


KNOWLEDGE_BASE = [
    {
        "id": "kb-001",
        "category": "Account & Access",
        "title": "Password Reset Procedure",
        "keywords": ["password", "locked", "locked out", "reset", "login", "forgot"],
        "content": (
            "1. Go to the company login portal and click 'Forgot Password'.\n"
            "2. Verify your identity using the MFA code.\n"
            "3. Set a new password following the 12-character policy.\n"
            "4. If verification fails 3 times, IT must reset the account manually."
        ),
    },
    {
        "id": "kb-002",
        "category": "Network & Connectivity",
        "title": "Wi-Fi / VPN Troubleshooting",
        "keywords": ["wifi", "wi-fi", "vpn", "network", "connect", "internet",
                     "disconnect", "disconnecting"],
        "content": (
            "1. Confirm Wi-Fi/VPN is enabled.\n"
            "2. Forget and reconnect to the 'Corp-Secure' network.\n"
            "3. Restart the VPN client and re-enter credentials.\n"
            "4. If multiple users are affected, it may be a network outage."
        ),
    },
    {
        "id": "kb-003",
        "category": "Software & Applications",
        "title": "Software Installation / License Errors",
        "keywords": ["install", "installation", "license", "software", "error",
                     "application", "app"],
        "content": (
            "1. Confirm connection to the corporate network or VPN.\n"
            "2. Re-run the installer as administrator.\n"
            "3. Clear the local license cache and retry activation.\n"
            "4. If the error persists, record the exact error code for escalation."
        ),
    },
    {
        "id": "kb-004",
        "category": "Hardware",
        "title": "Laptop Overheating / Shutdown",
        "keywords": ["laptop", "overheat", "overheating", "shutdown", "hardware",
                     "battery", "monitor", "dock", "docking"],
        "content": (
            "1. Ensure vents are unblocked and the laptop is on a hard, flat surface.\n"
            "2. Check for pending BIOS/driver updates.\n"
            "3. If shutdowns continue, request physical hardware inspection."
        ),
    },
    {
        "id": "kb-005",
        "category": "Email & Collaboration Tools",
        "title": "Shared Drive / Mailbox Access",
        "keywords": ["shared drive", "shared folder", "folder", "access",
                     "mailbox", "email", "permission", "permissions"],
        "content": (
            "1. Confirm the correct resource path.\n"
            "2. Check whether your department/team recently changed.\n"
            "3. If membership is correct but access is missing, create an access-change ticket."
        ),
    },
]

CATEGORY_TO_KB = {item["category"]: item for item in KNOWLEDGE_BASE}

SERVICE_STATUS = {
    "vpn_gateway": "operational",
    "email_server": "operational",
    "license_server": "operational",
    "wifi_network": random.choice(["operational", "degraded"]),
}

TICKETS: List[Dict[str, Any]] = []


def tool_check_service_status(service_name: str) -> str:
    status = SERVICE_STATUS.get(service_name, "unknown")
    return f"Service '{service_name}' status: {status}"


def tool_reset_password(user_id: str) -> str:
    return (
        f"Password reset initiated for user '{user_id}'. "
        "A reset link has been sent."
    )


def tool_create_ticket(
    user_id: str,
    category: str,
    summary: str,
    steps_taken: str,
) -> Dict[str, Any]:
    ticket = {
        "ticket_id": f"INC-{uuid.uuid4().hex[:8].upper()}",
        "user_id": user_id,
        "category": category,
        "summary": summary,
        "steps_already_attempted": steps_taken,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Open - Pending Human Review",
    }
    TICKETS.append(ticket)
    return ticket


def retrieve_knowledge(query: str, top_k: int = 1) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    scored: List[Tuple[float, Dict[str, Any]]] = []

    for article in KNOWLEDGE_BASE:
        keyword_hits = sum(
            1 for keyword in article["keywords"] if keyword in query_lower
        )
        fuzzy_score = difflib.SequenceMatcher(
            None, query_lower, article["title"].lower()
        ).ratio()
        score = keyword_hits * 2 + fuzzy_score
        scored.append((score, article))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [article for score, article in scored if score > 0][:top_k]


@dataclass
class ConversationState:
    user_id: str
    history: List[Tuple[str, str]] = field(default_factory=list)
    steps_attempted: List[str] = field(default_factory=list)
    resolved: bool = False


class AIITHelpdeskAgent:
    def __init__(self) -> None:
        self.sessions: Dict[str, ConversationState] = {}

    def _get_session(self, user_id: str) -> ConversationState:
        if user_id not in self.sessions:
            self.sessions[user_id] = ConversationState(user_id=user_id)
        return self.sessions[user_id]

    def handle_message(self, user_id: str, message: str) -> str:
        session = self._get_session(user_id)
        session.history.append(("user", message))

        matches = retrieve_knowledge(message)

        if not matches:
            response = (
                "I couldn't find a documented solution for that issue.\n"
                "I'm escalating this to a human IT agent."
            )
            ticket = tool_create_ticket(
                user_id,
                "Uncategorized",
                message,
                "; ".join(session.steps_attempted) or "None",
            )
            response += (
                f"\n\nTicket created: {ticket['ticket_id']}"
                f"\nStatus: {ticket['status']}"
            )
            session.history.append(("agent", response))
            return response

        article = matches[0]
        session.steps_attempted.append(article["title"])

        tool_output: Optional[str] = None
        message_lower = message.lower()

        if article["category"] == "Account & Access" and "locked" in message_lower:
            tool_output = tool_reset_password(user_id)
        elif article["category"] == "Network & Connectivity":
            service = "vpn_gateway" if "vpn" in message_lower else "wifi_network"
            tool_output = tool_check_service_status(service)
        elif article["category"] == "Software & Applications":
            tool_output = tool_check_service_status("license_server")

        response_lines = [
            f"[Classified as: {article['category']}]",
            f"[Retrieved article: {article['title']} ({article['id']})]",
        ]

        if tool_output:
            response_lines.append(f"[Tool result: {tool_output}]")

        response_lines.append("\nSuggested steps:")
        response_lines.append(article["content"])

        if tool_output and "degraded" in tool_output.lower():
            response_lines.append(
                "\nNote: This service is currently experiencing a known issue."
            )

        final_response = "\n".join(response_lines)
        session.history.append(("agent", final_response))
        return final_response

    def escalate(self, user_id: str, reason: str) -> Dict[str, Any]:
        session = self._get_session(user_id)
        return tool_create_ticket(
            user_id,
            "Escalated",
            reason,
            "; ".join(session.steps_attempted) or "None",
        )


SAMPLE_QUERIES = [
    "I forgot my password and I'm locked out of my account.",
    "My laptop won't connect to the office Wi-Fi.",
    "I'm getting an error code when installing the accounting software.",
    "The VPN keeps disconnecting every few minutes.",
    "I don't have access to the shared project folder anymore.",
    "My monitor isn't detected when I dock my laptop.",
]


def print_header(text: str) -> None:
    print("\n" + "=" * 78)
    print(text)
    print("=" * 78)


def run_demo() -> None:
    agent = AIITHelpdeskAgent()
    print_header("AI IT HELPDESK AGENT - DEMO RUN")
    print("Simulating support conversations for sample user queries...\n")

    for i, query in enumerate(SAMPLE_QUERIES, start=1):
        user_id = f"demo_user_{i}"
        print(f"--- Conversation {i} ---")
        print(f"User: {query}")
        print("Agent:")
        print(agent.handle_message(user_id, query))
        print()


def run_interactive() -> None:
    agent = AIITHelpdeskAgent()
    user_id = "interactive_user"

    print_header("AI IT HELPDESK AGENT - INTERACTIVE MODE")
    print("Type your IT issue below. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not message:
            continue

        if message.lower() in ("exit", "quit"):
            print("Session ended.")
            break

        print("\nAgent:")
        print(agent.handle_message(user_id, message))
        print()


def display_tickets() -> None:
    print_header("TICKETS CREATED DURING THIS SESSION")

    if not TICKETS:
        print("No tickets were created.")
        return

    for ticket in TICKETS:
        print(
            f"- {ticket['ticket_id']} | {ticket['category']} | "
            f"{ticket['status']}"
        )
        print(f"  User: {ticket['user_id']}")
        print(f"  Summary: {ticket['summary']}")
        print(f"  Created: {ticket['created_at']}")
        print()


def main() -> None:
    run_demo()
    display_tickets()
    print("-" * 78)

    while True:
        try:
            choice = input(
                "\nWould you like to try interactive mode "
                "and type your own IT issues? (y/n): "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nProgram terminated.")
            break

        if choice == "y":
            run_interactive()
            break
        if choice == "n":
            print("\nDemo complete.")
            break

        print("Please enter 'y' or 'n'.")


if __name__ == "__main__":
    main()
