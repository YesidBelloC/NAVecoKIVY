import time

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
import threading

Window.size = (400,700)

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
Builder.load_string("""
<MenuScreen>:
    BoxLayout:
        Button:
            text: 'Goto settings'
            on_press: root.manager.current = 'settings'
        Button:
            text: 'Quit'
            on_press: app.ButtonFunct()

<SettingsScreen>:
    BoxLayout:
        Button:
            text: 'My settings button'
        Button:
            text: 'Back to menu'
            on_press: root.manager.current = 'menu'
""")

# Declare both screens
class MenuScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class TestApp(App):

    def build(self):
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(SettingsScreen(name='settings'))

        return sm

    def LongAlgo(self):
        for i in range(0,10):
            time.sleep(1)
            print(i)
        text = "Done Algo"
        print(text)

        return text

    def ButtonFunct(self):
        # t1 = threading.Thread(target=print_square, args=(10,))
        # self.LongAlgo()

        t1 = threading.Thread(target=self.LongAlgo)
        t1.start()
        # wait until thread 1 is completely executed
        # t1.join()

        text = "Done Button"
        print(text)

        return text

if __name__ == '__main__':
    TestApp().run()