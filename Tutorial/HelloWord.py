# https://www.geeksforgeeks.org/kivy-tutorial/#kv

#!/usr/bin/env python3.6
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text="Hello World", font_size=8)

app = TestApp()
app.run()