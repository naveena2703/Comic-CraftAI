from __future__ import annotations

from google import genai
from google.genai import types

from app.config import Settings
from app.models import (
    ComicOutline,
    ComicStory,
    PromptRequest,
)


class GeminiService:

    def __init__(self, settings: Settings):

        self.settings = settings

        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Add your Gemini API key to the .env file."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def _generate_structured(
        self,
        model: str,
        prompt: str,
        schema
    ):

        response = self.client.models.generate_content(

            model=model,

            contents=prompt,

            config=types.GenerateContentConfig(

                response_mime_type="application/json",

                response_schema=schema,

                temperature=0.9,
            ),
        )

        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        try:

            return schema.model_validate_json(
                response.text
            )

        except Exception as exc:

            raise RuntimeError(
                "Gemini returned invalid structured data."
            ) from exc

    # ==========================================
    # GENERATE OUTLINE
    # ==========================================

    def generate_outline(
        self,
        request: PromptRequest
    ) -> ComicOutline:

        prompt = f"""
You are the story-outline engine for ComicCraft.

Create exactly {self.settings.panel_count}
sequential comic panels.

USER STORY:
{request.story_prompt}

MAIN CHARACTER:
{request.character_name}

SETTING:
{request.setting}

TONE:
{request.tone}

ART STYLE:
{request.art_style}

IMPORTANT REQUIREMENTS:

1. Create exactly {self.settings.panel_count} panels.

2. Keep the same main character throughout
the complete story.

3. The story must have:

- beginning
- development
- conflict
- climax
- ending

4. Every panel must advance the story.

5. scene_description must explain what is
visually happening.

6. image_prompt must describe:

- character
- appearance
- pose
- action
- environment
- lighting
- camera composition
- requested art style

7. Do not place speech text inside image prompts.

8. Keep the story appropriate for a general audience.

Return only the structured response.
"""

        outline = self._generate_structured(

            self.settings.gemini_outline_model,

            prompt,

            ComicOutline
        )

        if len(outline.panels) != self.settings.panel_count:

            raise RuntimeError(
                f"Gemini generated "
                f"{len(outline.panels)} panels. "
                f"Expected "
                f"{self.settings.panel_count}."
            )

        return outline

    # ==========================================
    # GENERATE STORY
    # ==========================================

    def generate_story(
        self,
        request: PromptRequest,
        outline: ComicOutline
    ) -> ComicStory:

        outline_text = outline.model_dump_json(
            indent=2
        )

        prompt = f"""
You are the comic narration and dialogue
writer for ComicCraft.

USER INFORMATION:

Story:
{request.story_prompt}

Main Character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art Style:
{request.art_style}

PANEL OUTLINE:

{outline_text}

Create the complete story for every panel.

REQUIREMENTS:

1. Preserve the exact panel order.

2. Preserve the panel titles.

3. Keep character continuity.

4. Keep location continuity.

5. Keep the requested tone.

6. caption should be short and cinematic.

7. narration should contain approximately
1-3 sentences.

8. dialogue should sound natural.

9. If no dialogue is needed, return an
empty string.

10. image_prompt should remain visually
consistent with the outline.

11. Do not include Markdown.

12. Return only the structured response.
"""

        story = self._generate_structured(

            self.settings.gemini_story_model,

            prompt,

            ComicStory
        )

        if len(story.panels) != self.settings.panel_count:

            raise RuntimeError(
                f"Gemini generated "
                f"{len(story.panels)} story panels. "
                f"Expected "
                f"{self.settings.panel_count}."
            )

        return story