from __future__ import annotations

import re
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.config import Settings


class ImageGenerator:

    def __init__(self, settings: Settings):

        self.settings = settings

        self._local_pipeline = None

    # ==========================================
    # MAIN GENERATOR
    # ==========================================

    def generate(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        provider = (
            self.settings.image_provider
            .lower()
            .strip()
        )

        if provider == "placeholder":

            return self._placeholder(
                prompt,
                panel_number
            )

        if provider == "huggingface":

            return self._huggingface(
                prompt,
                panel_number
            )

        if provider == "local":

            return self._local(
                prompt,
                panel_number
            )

        raise RuntimeError(
            f"Unsupported IMAGE_PROVIDER: {provider}. "
            "Use placeholder, huggingface, or local."
        )

    # ==========================================
    # FILE PATH
    # ==========================================

    def _output_path(
        self,
        panel_number: int
    ) -> Path:

        return (
            self.settings.panels_dir
            / f"panel_{panel_number}.png"
        )

    # ==========================================
    # PLACEHOLDER IMAGE
    # ==========================================

    def _placeholder(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        width = 768
        height = 512

        image = Image.new(
            "RGB",
            (width, height),
            "white"
        )

        draw = ImageDraw.Draw(image)

        try:

            font = ImageFont.truetype(
                "arial.ttf",
                34
            )

            small_font = ImageFont.truetype(
                "arial.ttf",
                18
            )

        except OSError:

            font = ImageFont.load_default()

            small_font = ImageFont.load_default()

        # Border

        draw.rectangle(
            (
                20,
                20,
                width - 20,
                height - 20
            ),
            outline="black",
            width=5
        )

        # Header

        draw.text(
            (45, 50),
            f"COMICCRAFT - PANEL {panel_number}",
            fill="black",
            font=font
        )

        # Prompt wrapping

        words = prompt[:500].split()

        lines = []

        current_line = ""

        for word in words:

            candidate = (
                f"{current_line} {word}"
            ).strip()

            if len(candidate) > 55:

                lines.append(current_line)

                current_line = word

            else:

                current_line = candidate

        if current_line:

            lines.append(current_line)

        y = 140

        for line in lines[:10]:

            draw.text(
                (50, y),
                line,
                fill="black",
                font=small_font
            )

            y += 30

        # Save

        path = self._output_path(
            panel_number
        )

        image.save(
            path,
            "PNG"
        )

        return (
            f"/static/panels/{path.name}"
        )

    # ==========================================
    # HUGGING FACE
    # ==========================================

    def _huggingface(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        if not self.settings.hf_api_key:

            raise RuntimeError(
                "HF_API_KEY is missing. "
                "Add it to .env or use "
                "IMAGE_PROVIDER=placeholder."
            )

        url = (
            "https://router.huggingface.co/"
            f"hf-inference/models/"
            f"{self.settings.hf_image_model}"
        )

        headers = {
            "Authorization":
                f"Bearer {self.settings.hf_api_key}"
        }

        try:

            response = httpx.post(

                url,

                headers=headers,

                json={
                    "inputs": prompt
                },

                timeout=180.0
            )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:

            raise RuntimeError(
                "Hugging Face image generation "
                f"failed: {exc.response.text[:500]}"
            ) from exc

        except httpx.HTTPError as exc:

            raise RuntimeError(
                f"Hugging Face request failed: {exc}"
            ) from exc

        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
        )

        if not content_type.startswith(
            "image/"
        ):

            raise RuntimeError(
                "Hugging Face did not return "
                "an image."
            )

        path = self._output_path(
            panel_number
        )

        path.write_bytes(
            response.content
        )

        try:

            with Image.open(path) as image:

                image.verify()

        except Exception as exc:

            path.unlink(
                missing_ok=True
            )

            raise RuntimeError(
                "Invalid image returned "
                "by Hugging Face."
            ) from exc

        return (
            f"/static/panels/{path.name}"
        )

    # ==========================================
    # LOCAL DIFFUSERS
    # ==========================================

    def _local(
        self,
        prompt: str,
        panel_number: int
    ) -> str:

        try:

            import torch

            from diffusers import (
                StableDiffusionPipeline
            )

        except ImportError as exc:

            raise RuntimeError(
                "Local image generation requires "
                "PyTorch and Diffusers."
            ) from exc

        if self._local_pipeline is None:

            dtype = (
                torch.float16
                if torch.cuda.is_available()
                else torch.float32
            )

            self._local_pipeline = (
                StableDiffusionPipeline
                .from_pretrained(
                    self.settings.local_image_model,
                    torch_dtype=dtype,
                    use_safetensors=True
                )
            )

            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

            self._local_pipeline = (
                self._local_pipeline
                .to(device)
            )

            if not torch.cuda.is_available():

                self._local_pipeline.enable_attention_slicing()

        result = self._local_pipeline(

            prompt,

            num_inference_steps=20,

            height=512,

            width=768
        )

        image = result.images[0]

        path = self._output_path(
            panel_number
        )

        image.save(
            path,
            "PNG"
        )

        return (
            f"/static/panels/{path.name}"
        )