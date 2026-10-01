from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.staticfiles import (
    StaticFiles
)

from fastapi.templating import (
    Jinja2Templates
)

from app.config import get_settings

from app.routes import router


settings = get_settings()


@asynccontextmanager
async def lifespan(
    app: FastAPI
):

    settings.panels_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    settings.exports_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    yield


app = FastAPI(

    title=settings.app_name,

    description=(
        "AI Comic Story Creator "
        "using Gemini and image generation."
    ),

    version="1.0.0",

    lifespan=lifespan
)


app.mount(

    "/static",

    StaticFiles(
        directory=str(
            settings.static_dir
        )
    ),

    name="static"
)


app.state.templates = (
    Jinja2Templates(

        directory=str(
            settings.templates_dir
        )
    )
)


app.include_router(
    router
)