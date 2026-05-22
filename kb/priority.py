"""Priority verification tool — deterministic multi-signal priority scoring.

Adapted from factory-code's priority intelligence engine. Uses four signals:
1. User-suggested priority
2. Impact × Urgency business matrix
3. AI text analysis (keyword-based severity detection)
4. Patient care keyword detection (clinical-specific)

Returns a verified priority mapped to ManageEngine's clinical priority scale:
  0.Patient Care | 1.Critical | 2.High | 3.Normal | 4.Low
"""

from collections import Counter
from typing import Annotated

from agent_framework import tool

# ── Clinical ManageEngine priorities (ordered by severity) ─────────────────────

PRIORITY_ORDER = {
    "4.Low": 1,
    "3.Normal": 2,
    "2.High": 3,
    "1.Critical": 4,
    "0.Patient Care": 5,
}

# ── Impact / Urgency scales ─────────────────────────────────────────────

IMPACT_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
URGENCY_ORDER = {"low": 1, "medium": 2, "high": 3, "immediate": 4}

_IMPACT_ALIASES = {
    "critical": "critical", "major": "critical", "sev1": "critical",
    "high": "high",
    "medium": "medium", "moderate": "medium",
    "low": "low", "minor": "low",
}

_URGENCY_ALIASES = {
    "immediate": "immediate", "now": "immediate", "asap": "immediate",
    "high": "high", "urgent": "high",
    "medium": "medium", "normal": "medium",
    "low": "low",
}

# ── Impact × Urgency → Priority matrix ──────────────────────────────────

_PRIORITY_MATRIX: dict[str, dict[str, str]] = {
    "immediate": {"critical": "1.Critical", "high": "1.Critical", "medium": "2.High", "low": "3.Normal"},
    "high":      {"critical": "1.Critical", "high": "2.High",     "medium": "3.Normal", "low": "4.Low"},
    "medium":    {"critical": "2.High",     "high": "2.High",     "medium": "3.Normal", "low": "4.Low"},
    "low":       {"critical": "3.Normal",   "high": "3.Normal",   "medium": "4.Low",    "low": "4.Low"},
}

# ── Keyword signals ─────────────────────────────────────────────────────

_PATIENT_CARE_SIGNALS = [
    "patient", "life-threatening", "clinical emergency", "patient safety",
    "bedside", "medication", "blood bank", "code blue", "crash cart",
    "ventilator", "infusion pump", "patient monitor", "life support",
]

_CRITICAL_SIGNALS = [
    "outage", "production down", "all users", "entire site", "entire department",
    "security breach", "data loss", "ransomware", "system down", "epic down",
    "hyperspace down", "cannot access any", "complete failure",
]

_HIGH_SIGNALS = [
    "multiple users", "cannot login", "cannot access", "service unavailable",
    "urgent", "major", "blocked", "department affected", "floor affected",
]

_LOW_SIGNALS = [
    "how to", "question", "feature request", "enhancement", "cosmetic",
    "minor", "nice to have", "when i get a chance",
]


def _normalize_impact(impact: str) -> str:
    return _IMPACT_ALIASES.get((impact or "").strip().lower(), "medium")


def _normalize_urgency(urgency: str) -> str:
    return _URGENCY_ALIASES.get((urgency or "").strip().lower(), "medium")


def _normalize_user_priority(priority: str) -> str:
    """Map free-text priority to ManageEngine priority names."""
    p = (priority or "").strip().lower()
    if "patient" in p or p == "0":
        return "0.Patient Care"
    if "critical" in p or p in ("1", "p1", "sev1"):
        return "1.Critical"
    if "high" in p or p in ("2", "p2", "sev2"):
        return "2.High"
    if "normal" in p or "medium" in p or p in ("3", "p3", "sev3"):
        return "3.Normal"
    if "low" in p or p in ("4", "p4", "sev4"):
        return "4.Low"
    return "3.Normal"


def _matrix_priority(impact: str, urgency: str) -> str:
    return _PRIORITY_MATRIX[_normalize_urgency(urgency)][_normalize_impact(impact)]


def _text_analysis(subject: str, description: str) -> tuple[str, str]:
    """Keyword-based severity detection from incident text."""
    text = f"{subject} {description}".lower()

    if any(s in text for s in _PATIENT_CARE_SIGNALS):
        return "0.Patient Care", "Detected patient care / clinical safety signals"
    if any(s in text for s in _CRITICAL_SIGNALS):
        return "1.Critical", "Detected critical-impact signals (outage, security, data loss)"
    if any(s in text for s in _HIGH_SIGNALS):
        return "2.High", "Detected high-severity signals (multiple users blocked)"
    if any(s in text for s in _LOW_SIGNALS):
        return "4.Low", "Detected low-severity signals (how-to, enhancement)"
    return "3.Normal", "No strong severity signals detected"


def _distance(a: str, b: str) -> int:
    return abs(PRIORITY_ORDER.get(a, 2) - PRIORITY_ORDER.get(b, 2))


def _weighted_decision(
    user_priority: str,
    matrix_priority: str,
    text_priority: str,
) -> tuple[str, list[str]]:
    """Weighted vote across all signals."""
    weights: Counter[str] = Counter()
    weights[user_priority] += 1
    weights[matrix_priority] += 2
    weights[text_priority] += 2

    top_weight = max(weights.values())
    candidates = [p for p, w in weights.items() if w == top_weight]
    signals = [user_priority, matrix_priority, text_priority]

    if len(candidates) == 1:
        winner = candidates[0]
    else:
        # Tie-break: pick highest severity among tied candidates
        winner = max(candidates, key=lambda c: PRIORITY_ORDER.get(c, 0))

    notes = [
        f"Weighted votes: {dict(weights)}",
        f"Winner: '{winner}'",
    ]
    return winner, notes


@tool(approval_mode="never_require")
async def assess_priority(
    subject: Annotated[str, "Short summary of the issue"],
    description: Annotated[str, "Detailed description of the issue"],
    user_priority: Annotated[str, "Priority suggested by the user (e.g., low, medium, high, critical, patient care)"] = "normal",
    impact: Annotated[str, "Business impact: critical, high, medium, or low"] = "medium",
    urgency: Annotated[str, "Urgency: immediate, high, medium, or low"] = "medium",
) -> str:
    """Verify and determine the correct priority for a ticket using multi-signal analysis.

    Combines user input, impact/urgency matrix, and text analysis to produce
    a verified priority. Use this BEFORE creating a ticket via createRequest
    to ensure the priority is accurate. Returns the verified ManageEngine
    priority name (e.g., '0.Patient Care', '1.Critical', '2.High', '3.Normal', '4.Low')
    along with reasoning."""

    norm_user = _normalize_user_priority(user_priority)
    matrix_result = _matrix_priority(impact, urgency)
    text_result, text_reason = _text_analysis(subject, description)

    # Patient care always wins — non-negotiable in a hospital
    if text_result == "0.Patient Care":
        return (
            f"**Verified Priority: 0.Patient Care**\n"
            f"Reason: {text_reason}\n"
            f"Action: This issue impacts patient safety. Create ticket IMMEDIATELY "
            f"with priority '0.Patient Care'."
        )

    verified, notes = _weighted_decision(norm_user, matrix_result, text_result)
    overridden = verified != norm_user

    lines = [
        f"**Verified Priority: {verified}**",
        f"",
        f"Signal Analysis:",
        f"  • User suggested: {norm_user} (weight: 1)",
        f"  • Impact/Urgency matrix ({impact}×{urgency}): {matrix_result} (weight: 2)",
        f"  • Text analysis: {text_result} — {text_reason} (weight: 2)",
        f"  • Decision: {' | '.join(notes)}",
    ]
    if overridden:
        lines.append(f"  • ⚠ User priority '{norm_user}' overridden to '{verified}'")
    else:
        lines.append(f"  • ✓ User priority is consistent with analysis")

    lines.append(f"\nUse priority '{verified}' when creating the ticket via createRequest.")
    return "\n".join(lines)
