"""Cover step — stub stores placeholder ref until image API wired."""


class CoverStep:
    async def generate(self, *, draft_text: str, session_id: int) -> str:
        return f"cover://session/{session_id}"
