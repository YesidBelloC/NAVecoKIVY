#!/usr/bin/env python3.7
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel, MDIcon


class TestApp(MDApp):
    def build(self):

        lbl  = MDLabel(text ='Label 1',
                       haling= 'center',
                       theme_Text_color='Error',
                       font_style='H2')
        icon = MDIcon(icon = 'language-python',
                      haling= 'center')

        return icon


app = TestApp()
app.run()