"""Review step — short critique before draft menus when review_enabled."""

from content_factory_bot.llm.client import LLMClient


class ReviewStep:
    async def critique(self, *, draft_options: list[str], profile_summary: str) -> str:
        client = LLMClient.from_settings(review=True)
        bullets = "\n".join(f"- {o[:200]}" for o in draft_options)
        return await client.chat(
            [
                {
                    "role": "system",
                    "content": "Critique these three drafts in 3-5 short bullets for the Creator.",
                },
                {
                    "role": "user",
                    "content": f"Profile:\n{profile_summary}\n\nDrafts:\n{bullets}",
                },
            ]
        )
