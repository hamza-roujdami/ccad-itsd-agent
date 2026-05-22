"""Launch the Clinical ITSM Agent in MAF DevUI.

Usage:
    cd src && python devui_app.py

Opens http://localhost:8080 with a chat interface, conversation history,
and tool call visibility.
"""

from agent_framework.devui import serve
from agent import create_agent

agent = create_agent()
serve(entities=[agent], auto_open=True, port=8080, auth_enabled=False)
