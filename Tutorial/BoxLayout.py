#!/usr/bin/env python3.6
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window

Window.clearcolor = (1,1,1,1)
Window.size = (360,600)

# declaring the colours you can use directly also
red = [1, 0, 0, 1]
green = [0, 1, 0, 1]
blue = [0, 0, 1, 1]
purple = [1, 0, 1, 1]

class TestApp(App):
    def build(self):

        layout = BoxLayout(orientation ='vertical',
                           spacing = 10,
                           padding = 40)

        lbl  = Label(text ="Label 1")
        lbl2 = Label(text ="Label is Added on \n screen !!:):) and its Multi\nLine",
            color =[0.41, 0.42, 0.74, 1],
            font_size='40sp')

        lbl3 = Label(text="[color=ff3333][b]Hello[/b][/color][color=3333ff][u]World[/u][/color]",
            markup = True)

        btn = Button(text ="Accept !",
                font_size ="20sp",
                background_color =red, # Button color
                color =blue) #Text color

        btn1 = Button(text ="Push Me !",
                font_size ="20sp",
                background_color =green, # Button color
                color =blue) #Text color

        # img = Image(source = '/img/Logo.png')
        img = Image(source = 'C:/Users/crybelloceferin/Documents/Kivy/Tutorial/img/Logo.png')

        layout.add_widget(img)
        layout.add_widget(lbl)
        layout.add_widget(btn)
        layout.add_widget(btn1)

        return layout

app = TestApp()
app.run()