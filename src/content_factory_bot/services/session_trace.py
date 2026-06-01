"""Session decision trace persisted on ContentSession.session_trace_json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from content_factory_bot.db.models import ContentSession


@dataclass
class SessionTrace:
    selected_angle_id: str | None = None
    format: str | None = None
    hook: str | None = None
    preview: str | None = None
    edit_count: int = 0
    quality_gate_retries: int = 0
    tribal_rewrite_count: int = 0
    ending_variant: str | None = None
    edit_history: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str | None) -> SessionTrace:
        if not raw:
            return cls()
        data: dict[str, Any] = json.loads(raw)
        return cls(
            selected_angle_id=data.get("selected_angle_id"),
            format=data.get("format"),
            hook=data.get("hook"),
            preview=data.get("preview"),
            edit_count=int(data.get("edit_count") or 0),
            quality_gate_retries=int(data.get("quality_gate_retries") or 0),
            tribal_rewrite_count=int(data.get("tribal_rewrite_count") or 0),
            ending_variant=data.get("ending_variant"),
            edit_history=list(data.get("edit_history") or []),
        )


def load_trace(row: ContentSession) -> SessionTrace:
    return SessionTrace.from_json(row.session_trace_json)


async def save_trace(session, row: ContentSession, trace: SessionTrace) -> None:
    row.session_trace_json = trace.to_json()
    await session.commit()
