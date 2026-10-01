from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
)

from app.config import get_settings

from app.models import (
    ImageTestRequest,
    PromptRequest,
)

from app.services.exporters import save_pdf

from app.services.gemini import (
    GeminiService
)

from app.services.image_generator import (
    ImageGenerator
)

from app.services.layout_builder import (
    build_comic_layout
)


router = APIRouter()

settings = get_settings()


# ==========================================
# TEMPLATE HELPER
# ==========================================

def templates(request: Request):

    return request.app.state.templates


# ==========================================
# GENERATE REQUEST
# ==========================================

def create_prompt_request(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
) -> PromptRequest:

    return PromptRequest(

        story_prompt=story_prompt,

        character_name=character_name,

        setting=setting,

        tone=tone,

        art_style=art_style
    )


# ==========================================
# COMPLETE COMIC PIPELINE
# ==========================================

def generate_comic(
    request_data: PromptRequest
):

    gemini = GeminiService(
        settings
    )

    image_generator = ImageGenerator(
        settings
    )

    # --------------------------------------
    # STEP 1
    # Generate outline
    # --------------------------------------

    outline = (
        gemini.generate_outline(
            request_data
        )
    )

    # --------------------------------------
    # STEP 2
    # Generate complete story
    # --------------------------------------

    story = (
        gemini.generate_story(
            request_data,
            outline
        )
    )

    # --------------------------------------
    # STEP 3
    # Generate images
    # --------------------------------------

    image_paths = []

    for panel in story.panels:

        image_path = (
            image_generator.generate(
                panel.image_prompt,
                panel.panel_number
            )
        )

        image_paths.append(
            image_path
        )

    # --------------------------------------
    # STEP 4
    # Build layout
    # --------------------------------------

    layout = build_comic_layout(
        story,
        image_paths
    )

    # --------------------------------------
    # STEP 5
    # Export PDF
    # --------------------------------------

    pdf_path = save_pdf(
        settings,
        layout
    )

    return (
        outline,
        story,
        layout,
        pdf_path
    )


# ==========================================
# HOME
# ==========================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):

    return templates(
        request
    ).TemplateResponse(

        request=request,

        name="index.html",

        context={
            "app_name":
                settings.app_name,

            "error":
                None
        }
    )


# ==========================================
# FORM GENERATION
# ==========================================

@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate_form(

    request: Request,

    story_prompt: Annotated[
        str,
        Form()
    ],

    character_name: Annotated[
        str,
        Form()
    ],

    setting: Annotated[
        str,
        Form()
    ],

    tone: Annotated[
        str,
        Form()
    ],

    art_style: Annotated[
        str,
        Form()
    ]
):

    try:

        data = create_prompt_request(

            story_prompt,

            character_name,

            setting,

            tone,

            art_style
        )

        (
            outline,
            story,
            layout,
            pdf_path
        ) = await asyncio.to_thread(

            generate_comic,

            data
        )

        return templates(
            request
        ).TemplateResponse(

            request=request,

            name="comic_preview.html",

            context={

                "app_name":
                    settings.app_name,

                "layout":
                    layout,

                "pdf_path":
                    pdf_path,

                "request_data":
                    data,

                "story":
                    story,

                "outline":
                    outline
            }
        )

    except Exception as exc:

        return templates(
            request
        ).TemplateResponse(

            request=request,

            name="index.html",

            context={

                "app_name":
                    settings.app_name,

                "error":
                    str(exc)
            },

            status_code=500
        )


# ==========================================
# JSON API
# ==========================================

@router.post(
    "/generate-comic/json"
)
async def generate_json(
    data: PromptRequest
):

    try:

        (
            outline,
            story,
            layout,
            pdf_path
        ) = await asyncio.to_thread(

            generate_comic,

            data
        )

        return JSONResponse(

            content={

                "success":
                    True,

                "outline":
                    outline.model_dump(),

                "story":
                    story.model_dump(),

                "layout":
                    [
                        panel.model_dump()
                        for panel in layout
                    ],

                "pdf_path":
                    pdf_path
            }
        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc)
        ) from exc


# ==========================================
# IMAGE TEST
# ==========================================

@router.post(
    "/test-image"
)
async def test_image(
    data: ImageTestRequest
):

    try:

        generator = (
            ImageGenerator(
                settings
            )
        )

        image_path = await asyncio.to_thread(

            generator.generate,

            data.prompt,

            999
        )

        return {

            "success":
                True,

            "image_path":
                image_path
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc)
        ) from exc


# ==========================================
# EXPORT SUCCESS
# ==========================================

@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(

    request: Request,

    pdf: str = ""
):

    return templates(
        request
    ).TemplateResponse(

        request=request,

        name="export_success.html",

        context={

            "app_name":
                settings.app_name,

            "pdf_path":
                pdf
        }
    )


# ==========================================
# HEALTH CHECK
# ==========================================

@router.get(
    "/health"
)
async def health():

    return {

        "status":
            "ok",

        "app":
            settings.app_name,

        "image_provider":
            settings.image_provider,

        "gemini_configured":
            bool(
                settings.gemini_api_key
            ),

        "huggingface_configured":
            bool(
                settings.hf_api_key
            )
    }