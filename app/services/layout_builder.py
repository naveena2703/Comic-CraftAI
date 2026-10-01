from app.models import (
    ComicPanel,
    ComicStory,
)


def build_comic_layout(
    story: ComicStory,
    image_paths: list[str]
) -> list[ComicPanel]:

    if len(story.panels) != len(image_paths):

        raise ValueError(
            "Number of story panels and "
            "images must be the same."
        )

    layout = []

    for panel, image_path in zip(
        story.panels,
        image_paths
    ):

        comic_panel = ComicPanel(

            panel_number=panel.panel_number,

            title=panel.title,

            image_path=image_path,

            scene_description=(
                panel.scene_description
            ),

            caption=panel.caption,

            narration=panel.narration,

            dialogue=panel.dialogue,

            image_prompt=panel.image_prompt
        )

        layout.append(
            comic_panel
        )

    return layout