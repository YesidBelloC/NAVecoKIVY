import os

from kivy.core.window import Window
from kivy.uix.image import Image

from kivymd import images_path
from kivymd.uix.backdrop import MDBackdrop
from kivymd.uix.backdrop.backdrop import (
    MDBackdropBackLayer, MDBackdropFrontLayer
)
from kivymd.uix.list import TwoLineAvatarListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp


class Example(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        return (
            MDScreen(
                MDBackdrop(
                    MDBackdropBackLayer(
                        Image(
                            size_hint=(0.8, 0.8),
                            source=os.path.join(images_path, "logo", "kivymd-icon-512.png"),
                            pos_hint={"center_x": 0.5, "center_y": 0.6},
                        )
                    ),
                    MDBackdropFrontLayer(
                        TwoLineAvatarListItem(
                            IconLeftWidget(icon="transfer-down"),
                            text="Lower the front layer",
                            secondary_text=" by 50 %",
                            on_press=self.backdrop_open_by_50_percent,
                            pos_hint={"top": 1},
                            _no_ripple_effect=True,
                        ),
                    ),
                    id="backdrop",
                    title="Example Backdrop",
                    radius_left="25dp",
                    radius_right="0dp",
                    header_text="Menu:",
                )
            )
        )

    def backdrop_open_by_50_percent(self, *args):
        self.root.ids.backdrop.open(-Window.height / 2)


Example().run()