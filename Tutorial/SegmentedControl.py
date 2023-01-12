from kivy.lang import Builder

from kivymd.app import MDApp


KV = '''
MDScreen:

    MDSegmentedControl:
        pos_hint: {"center_x": .5, "center_y": .5}

        MDSegmentedControlItem:
            size_hint: 0.2, 1
            MDIcon:
                icon:'car-hatchback'
                pos_hint : {'center_x':0.8,'center_y':0.5}

        MDSegmentedControlItem:
            size_hint: 0.2, 1
            MDIcon:
                icon:'car-hatchback'
                pos_hint : {'center_x':0.8,'center_y':0.5}

        MDSegmentedControlItem:
            size_hint: 0.2, 1
            MDIcon:
                icon:'car-hatchback'
                pos_hint : {'center_x':0.8,'center_y':0.5}
'''


class Example(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        return Builder.load_string(KV)


Example().run()