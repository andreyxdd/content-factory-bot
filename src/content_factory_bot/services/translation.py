from __future__ import annotations

from dataclasses import dataclass

from content_factory_bot.llm.client import LLMClient


@dataclass(frozen=True)
class ArtifactBundle:
    style_card_text: str
    values_block_text: str
    tribal_block_text: str
    system_prompt_text: str


class ArtifactTranslator:
    async def translate_bundle(
        self,
        *,
        source_locale: str,
        target_locale: str,
        bundle: ArtifactBundle,
    ) -> ArtifactBundle:
        translated_style = await self._translate_text(
            source_locale=source_locale,
            target_locale=target_locale,
            text=bundle.style_card_text,
        )
        translated_values = await self._translate_text(
            source_locale=source_locale,
            target_locale=target_locale,
            text=bundle.values_block_text,
        )
        translated_tribal = await self._translate_text(
            source_locale=source_locale,
            target_locale=target_locale,
            text=bundle.tribal_block_text,
        )
        translated_prompt = await self._translate_text(
            source_locale=source_locale,
            target_locale=target_locale,
            text=bundle.system_prompt_text,
        )
        return ArtifactBundle(
            style_card_text=translated_style,
            values_block_text=translated_values,
            tribal_block_text=translated_tribal,
            system_prompt_text=translated_prompt,
        )

    async def _translate_text(
        self,
        *,
        source_locale: str,
        target_locale: str,
        text: str,
    ) -> str:
        client = LLMClient.from_settings(fast=True)
        prompt = (
            "You are a localization translator.\n"
            f"Translate from {source_locale} to {target_locale}.\n"
            "Keep structure, markdown, bullets, and headers intact.\n"
            "Do not add commentary.\n\n"
            f"{text}"
        )
        return await client.chat([{"role": "user", "content": prompt}])

