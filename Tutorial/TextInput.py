#!/usr/bin/env python3.6
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
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

        grid = GridLayout(cols = 2,
                          row_force_default = True,
                          row_default_height=30,
                          spacing = 10,
                          padding = 10)

        lbl  = Label(text ="Label 1")

        txtint  = TextInput(text ="Write 1")

        grid.add_widget(lbl)
        grid.add_widget(txtint)

        btn1 = Button(text ="Push Me !",
                font_size ="20sp",
                background_color =green, # Button color
                color =blue) #Text color

        # img = Image(source = '/img/Logo.png')
        img = Image(source = 'C:/Users/crybelloceferin/Documents/Kivy/Tutorial/img/Logo.png')

        layout.add_widget(img)
        layout.add_widget(grid)
        layout.add_widget(btn1)

        return layout

app = TestApp()
app.run()