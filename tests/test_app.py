import os


# Tests should not call external image services.
os.environ["IMAGE_PROVIDER"] = "placeholder"


from fastapi.testclient import TestClient

from app.main import app

from app.config import get_settings

from app.services.image_generator import (
    ImageGenerator
)


client = TestClient(app)


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_homepage():

    response = client.get("/")

    assert response.status_code == 200

    assert (
        "Generate My Comic"
        in response.text
    )


def test_placeholder_image():

    settings = get_settings()

    generator = ImageGenerator(
        settings
    )

    image_path = generator.generate(

        "A fox exploring a forest",

        77
    )

    assert (
        image_path
        == "/static/panels/panel_77.png"
    )

    assert (
        settings.panels_dir
        / "panel_77.png"
    ).exists()


def test_validation():

    response = client.post(

        "/generate-comic/json",

        json={

            "story_prompt": "x",

            "character_name": "",

            "setting": "forest",

            "tone": "funny",

            "art_style": "comic book"
        }
    )

    assert (
        response.status_code
        == 422
    )