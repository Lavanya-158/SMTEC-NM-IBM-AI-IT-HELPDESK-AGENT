# AI IT Helpdesk Agent

A command-line IT support agent powered by a local LLM (via [Ollama](https://ollama.com)). It chats with a user about their IT issue, classifies it, offers troubleshooting steps from a local knowledge base + LLM reasoning, logs a support ticket, and escalates to a human if unresolved.

## Features
- Conversational troubleshooting for common issues: WiFi, password, printer, email, slow computer
- Keyword-based classification combined with LLM reasoning
- Local knowledge base of step-by-step fixes
- Automatic ticket logging to `tickets.json`
- Escalation flag when the user isn't satisfied

## Setup

1. Install [Ollama](https://ollama.com/download) and make sure it's running.
2. Pull a model:
   ```bash
   ollama pull llama3
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python it_helpdesk_agent.py
```

Type your IT issue when prompted. Type `exit` or `quit` to end the chat.

## How it works

1. **Classification** – `classify_issue()` matches keywords against a small knowledge base (`wifi`, `password`, `printer`, `email`, `slow computer`).
2. **Reasoning** – The matched category's troubleshooting steps are injected as context, and the full conversation is sent to the local Ollama model for a natural-language reply.
3. **Ticketing** – Every interaction (issue, category, resolution, escalation status) is appended to `tickets.json`.
4. **Escalation** – If the user says the issue wasn't solved, the agent flags the ticket as escalated for human follow-up.

## Project structure

```
.
├── it_helpdesk_agent.py   # main application
├── requirements.txt       # Python dependencies
└── README.md
```

## Possible improvements
- Web UI (Streamlit/Flask) instead of CLI
- Expand the knowledge base / load it from a JSON or CSV file
- Add email or Slack notifications on escalation
- Store tickets in a database instead of a flat JSON file
