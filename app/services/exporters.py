from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fpdf import FPDF

from app.config import Settings
from app.models import ComicPanel


def _local_image_path(
    settings: Settings,
    image_path: str
) -> Path:

    parsed = urlparse(image_path)

    if not parsed.path.startswith(
        "/static/panels/"
    ):

        raise ValueError(
            "Invalid panel image path."
        )

    filename = Path(
        parsed.path
    ).name

    path = (
        settings.panels_dir
        / filename
    )

    if not path.exists():

        raise FileNotFoundError(
            f"Panel image not found: {path}"
        )

    return path


def save_pdf(
    settings: Settings,
    layout: list[ComicPanel]
) -> str:

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
        settings.exports_dir
        / f"comiccraft_{timestamp}.pdf"
    )

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4"
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    for panel in layout:

        pdf.add_page()

        # Panel title

        pdf.set_font(
            "Helvetica",
            "B",
            18
        )

        pdf.multi_cell(
            0,
            10,
            f"Panel {panel.panel_number}: "
            f"{panel.title}"
        )

        # Image

        image_path = _local_image_path(
            settings,
            panel.image_path
        )

        pdf.image(
            str(image_path),
            x=15,
            y=38,
            w=180
        )

        # Description

        pdf.set_y(150)

        pdf.set_font(
            "Helvetica",
            "I",
            10
        )

        pdf.multi_cell(
            0,
            6,
            panel.scene_description
        )

        # Caption

        pdf.ln(2)

        pdf.set_font(
            "Helvetica",
            "B",
            11
        )

        pdf.multi_cell(
            0,
            6,
            f"Caption: {panel.caption}"
        )

        # Narration

        pdf.ln(1)

        pdf.set_font(
            "Helvetica",
            "",
            11
        )

        pdf.multi_cell(
            0,
            6,
            panel.narration
        )

        # Dialogue

        if panel.dialogue:

            pdf.ln(2)

            pdf.set_font(
                "Helvetica",
                "B",
                11
            )

            pdf.multi_cell(
                0,
                6,
                f"Dialogue: {panel.dialogue}"
            )

    pdf.output(
        str(output_path)
    )

    return (
        f"/static/exports/"
        f"{output_path.name}"
    )