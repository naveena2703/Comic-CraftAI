from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "ComicCraft"

    debug: bool = True

    # Gemini
    gemini_api_key: str | None = None
    gemini_outline_model: str = "gemini-2.5-flash"
    gemini_story_model: str = "gemini-2.5-pro"

    # Hugging Face
    hf_api_key: str | None = None
    hf_image_model: str = "stabilityai/stable-diffusion-xl-base-1.0"

    # Image provider
    image_provider: str = "placeholder"

    # Local diffusion model
    local_image_model: str = (
        "stable-diffusion-v1-5/stable-diffusion-v1-5"
    )

    # Comic
    panel_count: int = 5
    max_prompt_length: int = 2000

    # Directories
    static_dir: Path = BASE_DIR / "static"
    templates_dir: Path = BASE_DIR / "templates"

    panels_dir: Path = (
        BASE_DIR / "static" / "panels"
    )

    exports_dir: Path = (
        BASE_DIR / "static" / "exports"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:

    settings = Settings()

    settings.panels_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    settings.exports_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return settings