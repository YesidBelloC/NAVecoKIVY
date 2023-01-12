# Sample Python application demonstrating
# How to create GridLayout in Kivy

# import kivy module
import kivy

# base Class of your App inherits from the App class.
# app:always refers to the instance of your application
from kivy.app import App

# creates the button in kivy
# if not imported shows the error
from kivy.uix.button import Button
from kivy.core.window import Window

# The GridLayout arranges children in a matrix.
# It takes the available space and
# divides it into columns and rows,
# then adds widgets to the resulting “cells”.
from kivy.uix.gridlayout import GridLayout


# Setting the window size
Window.size = (1120, 630)

# creating the App class
# creating the App class
class Grid_LayoutApp(App):

    # to build the application we have to
    # return a widget on the build() function.
    def build(self):

        # adding GridLayouts in App
        # Defining number of column and size of the buttons i.e height
        layout = GridLayout(cols = 2, row_force_default = True,
                            row_default_height = 30)

        # 1st row
        layout.add_widget(Button(text ='Hello 1', size_hint_x = None, width = 100))
        layout.add_widget(Button(text ='World 1'))

        # 2nd row
        layout.add_widget(Button(text ='Hello 2', size_hint_x = None, width = 100))
        layout.add_widget(Button(text ='World 2'))

        # 3rd row
        layout.add_widget(Button(text ='Hello 3', size_hint_x = None, width = 100))
        layout.add_widget(Button(text ='World 3'))

        # 4th row
        layout.add_widget(Button(text ='Hello 4', size_hint_x = None, width = 100))
        layout.add_widget(Button(text ='World 4'))

        # returning the layout
        return layout


# creating object of the App class
root = Grid_LayoutApp()
# run the App
root.run()
