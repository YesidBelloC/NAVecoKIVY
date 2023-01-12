from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.menu import MDDropdownMenu


KV = '''
FloatLayout:
    MDRaisedButton:
        id: ButtonID
        text:'Press me'
        pos_hint:{"center_x":0.5,"center_y":0.5}
        on_release: app.drpdwon_()
'''


class Test(MDApp):
    def drpdwon_(self):
        self.menu_list = [
            {"viewclass":"OneLineListItem",
            "text":"example 1",
            "on_release":lambda x = "Example 1" : self.test1()
            },
            {"viewclass":"OneLineListItem",
            "text":"example 2",
            "on_release":lambda x = "Example 2" : self.test2()
            }
        ]
        self.menu = MDDropdownMenu(
            caller = self.root.ids.ButtonID,
            items = self.menu_list,
            width_mult = 4
        )
        self.menu.open()
    def test1(self):
        print("Pressed test 1")
        # self.menu.disabled()
        self.menu.dismiss()
    def test2(self):
        print("Pressed test 2")
        self.menu.dismiss()


    def build(self):
        self.root = Builder.load_string(KV)
        return self.root


Test().run()