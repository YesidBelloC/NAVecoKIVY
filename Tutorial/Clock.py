from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
import time

class Timer(Label):
    def Update(self, *args):
        self.text=time.asctime()

class MainApp(App):
    def build(self):
        t = Timer()
        Clock.schedule_interval(t.Update,1)

        return(t)

MainApp().run()