"""Voice channel — ACS telephony integration.

Enables caregivers to call a phone number and speak to the Clinical ITSM Agent.
"""

from voice.routes import call_router, init_call_client

__all__ = ["call_router", "init_call_client"]
