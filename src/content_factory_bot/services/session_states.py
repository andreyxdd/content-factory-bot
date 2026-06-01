"""Canonical content-session FSM states and legacy compatibility."""

from __future__ import annotations

# --- New linear flow ---
AWAITING_INPUT = "awaiting_input"
RESEARCHING = "researching"
DRAFTING = "drafting"
AWAITING_ANGLE_CHOICE = "awaiting_angle_choice"
AWAITING_ANGLE_EDIT = "awaiting_angle_edit"
EXPANDING_POST = "expanding_post"
AWAITING_ENDING_OFFER = "awaiting_ending_offer"
AWAITING_ENDING_PICK = "awaiting_ending_pick"
AWAITING_ENDING_REGEN = "awaiting_ending_regen"
AWAITING_TRIBAL_CHECK = "awaiting_tribal_check"
AWAITING_TRIBAL_FEEDBACK = "awaiting_tribal_feedback"
AWAITING_FINALIZE = "awaiting_finalize"
AWAITING_PUBLISH_SCOPE = "awaiting_publish_scope"
AWAITING_PUBLISH_DEST = "awaiting_publish_dest"
READY_TO_PUBLISH_LATER = "ready_to_publish_later"
PARTIALLY_PUBLISHED = "partially_published"
PUBLISHED = "published"
DRAFT_FAILED = "draft_failed"
CLOSED = "closed"

# --- Legacy (compat until sessions close) ---
LEGACY_AWAITING_DRAFT_CHOICE = "awaiting_draft_choice"
LEGACY_AWAITING_FOLLOW_UP = "awaiting_follow_up"
LEGACY_AWAITING_CUSTOM_DRAFT = "awaiting_custom_draft"
LEGACY_AWAITING_PUBLISH = "awaiting_publish"
LEGACY_CONFIRMED = "confirmed"

LEGACY_STATES = frozenset(
    {
        LEGACY_AWAITING_DRAFT_CHOICE,
        LEGACY_AWAITING_FOLLOW_UP,
        LEGACY_AWAITING_CUSTOM_DRAFT,
        LEGACY_AWAITING_PUBLISH,
        LEGACY_CONFIRMED,
    }
)

TERMINAL_STATES = frozenset(
    {
        READY_TO_PUBLISH_LATER,
        PARTIALLY_PUBLISHED,
        PUBLISHED,
        CLOSED,
        DRAFT_FAILED,
    }
)


def is_legacy_state(state: str) -> bool:
    return state in LEGACY_STATES
