#!/usr/bin/env python3.6
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        lbl  = Label(text ="Label is Added on screen !!:):)")
        lbl2 = Label(text ="Label is Added on \n screen !!:):) and its Multi\nLine",
            color =[0.41, 0.42, 0.74, 1],
            font_size='40sp')

        lbl3 = Label(text="[color=ff3333][b]Hello[/b][/color][color=3333ff][u]World[/u][/color]",
            markup = True)

        return lbl3

app = TestApp()
app.run()
