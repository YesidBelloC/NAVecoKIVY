#!/usr/bin/env python3.7
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button

from functools import partial


# declaring the colours you can use directly also
red = [1, 0, 0, 1]
green = [0, 1, 0, 1]
blue = [0, 0, 1, 1]
purple = [1, 0, 1, 1]

class TestApp(App):
    def build(self):
        # use a (r, g, b, a) tuple
        btn = Button(text ="Push Me !",
                font_size ="20sp",
                background_color =red, # Button color
                color =blue, #Text color
                size =(15, 15),
                size_hint =(.2, .2),
                pos =(400, 250))

        btn.bind(on_press = self.clicko)

        return btn

    def clicko(self, event):
        print("Button pressed")
        print('Congratulations !!!!!!!!!!!')

app = TestApp()
app.run()