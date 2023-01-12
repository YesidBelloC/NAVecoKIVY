#!/usr/bin/env python3.7

import kivy

kivy.require("1.9.1")

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button

from functools import partial

# to change the kivy default settings we use this module config
from kivy.config import Config

# 0 being off 1 being on as in true / false
# you can use 0 or 1 && True or False
Config.set('graphics', 'resizable', True)

class TestApp(App):
    def build(self):
        # use a (r, g, b, a) tuple
        btn = Button(text ="Push Me !",
                font_size ="20sp",
                background_normal = 'C:/Users/crybelloceferin/Documents/Kivy/Tutorial/img/img_vehicules/P508.jpg',
                background_down ='C:/Users/crybelloceferin/Documents/Kivy/Tutorial/img/img_vehicules/P308.jpg',
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
