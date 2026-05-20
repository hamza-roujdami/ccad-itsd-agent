"""ACS Call Automation handler — voice loop for phone calls.

Flow:
  IncomingCall → answer → greet → [recognize STT → agent → play TTS → repeat] → hang up
"""

import logging
from urllib.parse import urlencode

from azure.communication.callautomation import (
    CallAutomationClient,
    CallConnectionClient,
    PhoneNumberIdentifier,
    TextSource,
    RecognizeInputType,
)

from config import settings

logger = logging.getLogger(__name__)

GREETING = "Hello, IT Service Desk. How can I help you today?"
GOODBYE = "Thank you for calling the IT Service Desk. Goodbye."
SILENCE_PROMPT = "I'm sorry, I didn't catch that. Could you please repeat?"
ERROR_PROMPT = "I'm sorry, I'm having trouble processing your request. Please try again."

# Voice for TTS in calls — must match Azure Speech voice name
VOICE_NAME = "en-US-AriaNeural"

# Max silence before re-prompting (seconds)
RECOGNIZE_TIMEOUT_SECONDS = 10


def create_call_automation_client() -> CallAutomationClient:
    """Create the ACS Call Automation client."""
    return CallAutomationClient.from_connection_string(settings.acs_connection_string)


def _callback_url(path: str) -> str:
    """Build the full callback URL for ACS events."""
    base = settings.acs_callback_base_url.rstrip("/")
    return f"{base}{path}"


def _text_source(text: str) -> TextSource:
    """Create a TextSource for TTS playback."""
    return TextSource(
        text=text,
        voice_name=VOICE_NAME,
    )


def _cognitive_services_kwargs() -> dict:
    """Return kwargs for cognitive services endpoint if configured."""
    if settings.acs_cognitive_services_endpoint:
        return {"cognitive_services_endpoint": settings.acs_cognitive_services_endpoint}
    return {}


async def handle_incoming_call(event: dict, call_client: CallAutomationClient) -> None:
    """Answer an incoming call and start the voice loop."""
    incoming_call_context = event.get("incomingCallContext", "")
    caller_raw = event.get("from", {})
    if isinstance(caller_raw, dict):
        caller = caller_raw.get("rawId", caller_raw.get("phoneNumber", {}).get("value", "unknown"))
    else:
        caller = str(caller_raw)
    logger.info("Incoming call from %s", caller)
    logger.info("Call context length: %d", len(incoming_call_context))

    if not incoming_call_context:
        logger.error("No incomingCallContext in event")
        return

    # Answer the call — ACS will send events to our callback URL
    callback = _callback_url("/api/calls/events")
    logger.info("Answering call with callback: %s", callback)
    call_client.answer_call(
        incoming_call_context=incoming_call_context,
        callback_url=callback,
        **_cognitive_services_kwargs(),
    )
    logger.info("Call answered, waiting for CallConnected event")


async def handle_call_connected(event: dict, call_connection: CallConnectionClient) -> None:
    """Call is connected — play greeting then start listening."""
    logger.info("Call connected: %s", event.get("callConnectionId"))

    # Play greeting
    call_connection.play_media_to_all(
        play_source=_text_source(GREETING),
    )
    logger.info("Playing greeting")


async def handle_play_completed(event: dict, call_connection: CallConnectionClient) -> None:
    """TTS playback finished — start listening for caller's speech."""
    logger.info("Play completed, starting speech recognition")
    _start_recognize(call_connection)


async def handle_play_failed(event: dict, call_connection: CallConnectionClient) -> None:
    """TTS playback failed — try to recover by listening."""
    logger.warning("Play failed: %s", event.get("resultInformation", {}))
    _start_recognize(call_connection)


async def handle_recognize_completed(
    event: dict,
    call_connection: CallConnectionClient,
    agent,
    sessions: dict,
) -> None:
    """Speech recognized — send to agent, play response."""
    speech_result = event.get("speechResult", {})
    transcript = speech_result.get("speech", "")

    if not transcript.strip():
        logger.info("Empty transcript, re-prompting")
        call_connection.play_media_to_all(play_source=_text_source(SILENCE_PROMPT))
        return

    call_id = event.get("callConnectionId", "")
    logger.info("Caller said: %s (call: %s)", transcript, call_id)

    # Get or create agent session for this call
    if call_id not in sessions:
        sessions[call_id] = agent.create_session()
    session = sessions[call_id]

    try:
        # Run agent — same as /chat endpoint
        result = await agent.run(transcript, session=session)
        reply = result.text or ERROR_PROMPT
        logger.info("Agent reply: %s", reply[:100])

        # Strip markdown for TTS
        clean_reply = _clean_for_tts(reply)

        # Play agent's response
        call_connection.play_media_to_all(play_source=_text_source(clean_reply))

    except Exception as e:
        logger.error("Agent error: %s", e, exc_info=True)
        call_connection.play_media_to_all(play_source=_text_source(ERROR_PROMPT))


async def handle_recognize_failed(event: dict, call_connection: CallConnectionClient) -> None:
    """Speech recognition failed (timeout, no speech, etc.)."""
    result_info = event.get("resultInformation", {})
    sub_code = result_info.get("subCode", 0)
    logger.warning("Recognize failed (subCode=%s): %s", sub_code, result_info.get("message"))

    # 8510 = silence timeout — re-prompt
    if sub_code == 8510:
        call_connection.play_media_to_all(play_source=_text_source(SILENCE_PROMPT))
    else:
        # Other failure — try once more
        _start_recognize(call_connection)


async def handle_call_disconnected(event: dict, sessions: dict) -> None:
    """Call ended — clean up session."""
    call_id = event.get("callConnectionId", "")
    logger.info("Call disconnected: %s", call_id)
    sessions.pop(call_id, None)


def _start_recognize(call_connection: CallConnectionClient) -> None:
    """Start speech recognition on the call."""
    # Get the first non-ACS participant (the caller)
    props = call_connection.get_call_properties()
    target = None
    for p in props.targets:
        target = p
        break

    if not target:
        logger.error("No target participant found for recognition")
        return

    logger.info("Starting recognition for participant: %s", target.raw_id if hasattr(target, 'raw_id') else target)
    call_connection.start_recognizing_media(
        input_type=RecognizeInputType.SPEECH,
        target_participant=target,
        end_silence_timeout=RECOGNIZE_TIMEOUT_SECONDS,
        speech_language="en-US",
    )


def _clean_for_tts(text: str) -> str:
    """Strip markdown formatting for natural TTS output."""
    import re
    clean = text
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)  # bold
    clean = re.sub(r'\*(.*?)\*', r'\1', clean)  # italic
    clean = re.sub(r'#{1,6}\s', '', clean)  # headings
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)  # links
    clean = re.sub(r'`([^`]+)`', r'\1', clean)  # inline code
    clean = re.sub(r'^[-*•]\s+', '', clean, flags=re.MULTILINE)  # bullets
    clean = re.sub(r'\n{2,}', '. ', clean)  # paragraph breaks → pause
    clean = re.sub(r'\n', ' ', clean)  # line breaks
    return clean.strip()
