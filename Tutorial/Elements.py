# Program to Show how to use multiple UX widget

# import kivy module
import kivy

# base Class of your App inherits from the App class.
# app:always refers to the instance of your application
from kivy.app import App
from kivy.lang import Builder

# this restrict the kivy version i.e
# below this kivy version you cannot
# use the app or software
kivy.require('1.9.0')

# Here for providing colour to the background
from kivy.core.window import Window

# Setting the window size
Window.size = (1120, 630)


Builder.load_string("""
# .kv file implementation of the App

# Using Grid layout
GridLayout:

    cols: 4
    rows: 3
    padding: 10

    # Adding label
    Label:
        text: "I am a Label"

    # Add Button
    Button:
        text: "button 1"

    # Add CheckBox
    CheckBox:
        active: True

    # Add Image
    Image:
        source: 'html.png'

    # Add Slider
    Slider:
        min: -100
        max: 100
        value: 25

    # Add progress Bar
    ProgressBar:
        min: 50
        max: 100

    # Add TextInput
    TextInput:
        text: "Enter the text"

    # Add toggle Button
    ToggleButton:
        text: " Poetry Mode "

    # Add Switch
    Switch:
        active: True

""")

# Add the App class
class ClassiqueApp(App):
	def build(FloatLayout):
		pass

# Run the App
if __name__ == '__main__':
	ClassiqueApp().run()
