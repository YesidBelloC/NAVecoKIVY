#!/usr/bin/env python3.7
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRectangleFlatButton, MDFlatButton
from kivy.lang import Builder

username_input = """
MDTextField:
    hint_text: "Enter username"
    helper_text: "or click on forgot username"
    helper_text_mode: "on_focus"
    icon_right: "android"
    icon_right_color: app.theme_cls.primary_color
    pos_hint:{'center_x': 0.5, 'center_y': 0.5}
    size_hint_x:None
    width:300
"""

class DemoApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette="Green"
        screen = Screen()

        layout = BoxLayout(orientation ='vertical',
                           spacing = 10,
                           padding = 40)

        # username = MDTextField(
        #     pos_hint={'center_x': 0.5, 'center_y': 0.5},
        #     size_hint_x=None, width=200)

        self.username = Builder.load_string(username_input)

        btn_flt  = MDRectangleFlatButton(text ='Flat btn',
                        pos_hint = {'center_x':0.5,'center_y':0.5},
                        on_release = self.show_data)

        layout.add_widget(self.username)
        layout.add_widget(btn_flt)
        screen.add_widget(layout)
        return screen

    def show_data(self,obj):
        print(self.username.text)

        if self.username.text is "":
            check_string = "Please write"
        else:
            check_string = self.username.text+" Encontrado"

        cls_btn = MDFlatButton(text='Close',
                        on_release = self.close_dialog)
        mr_btn = MDFlatButton(text='More')
        self.dlg = MDDialog(title = 'Answer',
                       text = check_string,
                       size_hint = (0.7,1),
                       buttons= [cls_btn,mr_btn])
        self.dlg.open()
        if self.username.text is "":
            check_string = 'Please enter'

    def close_dialog(self,obj):
        self.dlg.dismiss()

DemoApp().run()