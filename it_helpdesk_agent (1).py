"""
AI IT Helpdesk Agent (powered by Ollama)
------------------------------------------
A simple command-line IT support agent that:
  1. Chats with a user about their IT issue
  2. Classifies the issue into a category
  3. Gives troubleshooting steps using a local knowledge base + LLM reasoning
  4. Logs a support ticket to a local JSON file
  5. Escalates to "human support" if the user is not satisfied

Requirements:
    pip install ollama

Before running:
    1. Install Ollama: https://ollama.com/download
    2. Pull a model, e.g.:  ollama pull llama3
    3. Make sure the Ollama app/service is running.

Run:
    python it_helpdesk_agent.py
"""

import json
import os
import sys
from datetime import datetime

try:
    import ollama
except ImportError:
    print("The 'ollama' package is not installed. Run: pip install ollama")
    sys.exit(1)

MODEL_NAME = "llama3"          # change to any model you have pulled (e.g. "mistral", "phi3")
TICKETS_FILE = "tickets.json"

KNOWLEDGE_BASE = {
    "wifi": "1. Restart the router.\n2. Forget and reconnect to the network.\n3. Check if other devices can connect.\n4. Update network drivers.",
    "password": "1. Use the 'Forgot Password' link on the login page.\n2. Check for Caps Lock.\n3. Ensure account isn't locked after failed attempts.\n4. Contact admin if reset email doesn't arrive.",
    "printer": "1. Check printer is powered on and connected.\n2. Restart the print spooler service.\n3. Reinstall or update printer drivers.\n4. Verify correct printer is set as default.",
    "email": "1. Check internet connection.\n2. Verify email server settings (IMAP/SMTP).\n3. Clear cache or restart the email client.\n4. Check if account is over storage limit.",
    "slow computer": "1. Restart the computer.\n2. Check for high CPU/memory usage in Task Manager.\n3. Run a malware scan.\n4. Free up disk space and disable unnecessary startup apps.",
}

SYSTEM_PROMPT = """You are a friendly and professional IT Helpdesk Agent.
Your job is to:
- Understand the user's technical issue.
- Classify it into one category from this list if possible: wifi, password, printer, email, slow computer, other.
- Give clear, numbered troubleshooting steps.
- Be concise, calm, and helpful. Avoid unnecessary jargon.
- If the issue seems serious (data loss, security breach, hardware failure), recommend escalating to a human technician.
"""


def check_ollama_connection():
    """Verify Ollama is running and the model is available."""
    try:
        models = ollama.list()
        available = [m.get("model", m.get("name", "")) for m in models.get("models", [])]
        if not any(MODEL_NAME in name for name in available):
            print(f"⚠️  Model '{MODEL_NAME}' not found locally.")
            print(f"   Run: ollama pull {MODEL_NAME}")
            sys.exit(1)
    except Exception as e:
        print("❌ Could not connect to Ollama. Is the Ollama app/service running?")
        print(f"   Details: {e}")
        sys.exit(1)


def classify_issue(user_message: str) -> str:
    """Simple keyword-based classification, used alongside LLM reasoning."""
    text = user_message.lower()
    for keyword in KNOWLEDGE_BASE:
        if keyword in text:
            return keyword
    return "other"


def ask_agent(conversation: list) -> str:
    """Send the conversation to the Ollama model and return its reply."""
    try:
        response = ollama.chat(model=MODEL_NAME, messages=conversation)
        return response["message"]["content"]
    except Exception as e:
        return f"⚠️ Sorry, I couldn't reach the AI model right now. ({e})"


def log_ticket(user_message: str, category: str, resolution: str, escalated: bool):
    """Append a ticket record to a local JSON file."""
    ticket = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "issue": user_message,
        "category": category,
        "resolution": resolution,
        "escalated": escalated,
    }

    tickets = []
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
        except (json.JSONDecodeError, IOError):
            tickets = []

    tickets.append(ticket)

    try:
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2)
    except IOError as e:
        print(f"⚠️ Could not save ticket log: {e}")


def main():
    print("=" * 55)
    print(" 🖥️  AI IT Helpdesk Agent (Ollama)")
    print(" Type 'exit' anytime to end the chat.")
    print("=" * 55)

    check_ollama_connection()

    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_message = input("\nYou: ").strip()
        if not user_message:
            continue
        if user_message.lower() in ("exit", "quit"):
            print("Agent: Thanks for contacting IT Helpdesk. Goodbye! 👋")
            break

        category = classify_issue(user_message)
        conversation.append({"role": "user", "content": user_message})

        # If we have a known KB entry, give the agent a hint via context injection
        if category in KNOWLEDGE_BASE:
            hint = f"(Reference troubleshooting steps for '{category}':\n{KNOWLEDGE_BASE[category]})"
            conversation.append({"role": "system", "content": hint})

        reply = ask_agent(conversation)
        conversation.append({"role": "assistant", "content": reply})

        print(f"\nAgent [{category}]: {reply}")

        satisfied = input("\nDid this solve your issue? (yes/no): ").strip().lower()
        escalated = satisfied.startswith("n")

        log_ticket(user_message, category, reply, escalated)

        if escalated:
            print("Agent: I've logged a ticket and escalated this to a human technician. "
                  "They'll follow up with you shortly.")


if __name__ == "__main__":
    main()
