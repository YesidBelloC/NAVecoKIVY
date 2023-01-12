from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.screen import MDScreen


class MD3Card(MDCard):
    '''Implements a material design v3 card.'''


class Example(MDApp):
    def build(self):
        self.theme_cls.material_style = "M3"
        return (
            MDScreen(
                MDBoxLayout(
                    id="box",
                    adaptive_size=True,
                    spacing="56dp",
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                )
            )
        )

    def on_start(self):
        styles = {
            "elevated": "#f6eeee", "filled": "#f4dedc", "outlined": "#f8f5f4"
        }
        for style in styles.keys():
            self.root.ids.box.add_widget(
                MD3Card(
                    MDRelativeLayout(
                        MDIconButton(
                            icon="dots-vertical",
                            pos_hint={"top": 1, "right": 1}
                        ),
                        MDLabel(
                            text=style.capitalize(),
                            adaptive_size=True,
                            color="grey",
                            pos=("12dp", "12dp"),
                        ),
                    ),
                    line_color=(0.2, 0.2, 0.2, 0.8),
                    style=style,
                    padding="4dp",
                    size_hint=(None, None),
                    size=("200dp", "100dp"),
                    md_bg_color=styles[style],
                )
            )


Example().run()