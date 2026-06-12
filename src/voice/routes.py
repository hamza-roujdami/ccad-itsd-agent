"""ACS Call Automation — FastAPI router for voice channel.

Routes:
  POST /api/calls/incoming — Event Grid webhook (IncomingCall)
  POST /api/calls/events   — Call Automation callback events (voice loop)
"""

import logging

from fastapi import APIRouter, Request, Response

from voice.handler import (
    create_call_automation_client,
    handle_incoming_call,
    handle_call_connected,
    handle_play_completed,
    handle_play_failed,
    handle_recognize_completed,
    handle_recognize_failed,
    handle_call_disconnected,
)

logger = logging.getLogger(__name__)

call_router = APIRouter(prefix="/api/calls", tags=["voice"])

_call_client = None
_call_sessions: dict[str, object] = {}
_call_callers: dict[str, str] = {}  # call_connection_id → caller raw ID


def init_call_client(callback_base_url: str) -> None:
    """Initialize the ACS Call Automation client. Called during server startup."""
    global _call_client
    _call_client = create_call_automation_client()
    logger.info("ACS Call Automation initialized (callback: %s)", callback_base_url)


@call_router.post("/incoming")
async def calls_incoming(request: Request):
    """Handle Event Grid events (IncomingCall + validation)."""
    body = await request.json()

    if isinstance(body, list) and body:
        event = body[0]
        event_type = event.get("eventType", "")

        # Event Grid subscription validation handshake
        if event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
            validation_code = event.get("data", {}).get("validationCode", "")
            logger.info("Event Grid validation: %s", validation_code)
            return {"validationResponse": validation_code}

        # Incoming PSTN call
        if event_type == "Microsoft.Communication.IncomingCall":
            if not _call_client:
                logger.error("ACS not configured, cannot answer call")
                return Response(status_code=503)
            data = event.get("data", {})
            caller_raw_id = data.get("from", {}).get("rawId", "unknown")
            logger.info("IncomingCall from: %s", caller_raw_id)
            try:
                result = await handle_incoming_call(data, _call_client)
                # Store caller for later use in recognize
                if result and result.get("call_connection_id"):
                    _call_callers[result["call_connection_id"]] = caller_raw_id
            except Exception as e:
                logger.error("Failed to answer call: %s", e, exc_info=True)
            return Response(status_code=200)

    return Response(status_code=200)


@call_router.post("/events")
async def calls_events(request: Request):
    """Handle ACS Call Automation callback events (voice loop)."""
    # Late import to get the current agent reference from server module
    from server import _agent

    events = await request.json()
    if not isinstance(events, list):
        events = [events]

    for event in events:
        event_type = event.get("type", "")
        event_data = event.get("data", {})
        call_connection_id = event_data.get("callConnectionId", "")

        logger.info("[CALL] Event: %s (call: %s)", event_type, call_connection_id)

        if not _call_client or not call_connection_id:
            continue

        try:
            call_connection = _call_client.get_call_connection(call_connection_id)

            if event_type == "Microsoft.Communication.CallConnected":
                await handle_call_connected(event_data, call_connection)

            elif event_type == "Microsoft.Communication.PlayCompleted":
                caller_id = _call_callers.get(call_connection_id)
                await handle_play_completed(event_data, call_connection, caller_id)

            elif event_type == "Microsoft.Communication.PlayFailed":
                caller_id = _call_callers.get(call_connection_id)
                await handle_play_failed(event_data, call_connection, caller_id)

            elif event_type == "Microsoft.Communication.RecognizeCompleted":
                await handle_recognize_completed(event_data, call_connection, _agent, _call_sessions)

            elif event_type == "Microsoft.Communication.RecognizeFailed":
                await handle_recognize_failed(event_data, call_connection)

            elif event_type == "Microsoft.Communication.CallDisconnected":
                await handle_call_disconnected(event_data, _call_sessions)
                _call_callers.pop(call_connection_id, None)

            else:
                logger.info("Unhandled call event: %s", event_type)

        except Exception as e:
            logger.error("Error handling call event %s: %s", event_type, e, exc_info=True)

    return Response(status_code=200)
