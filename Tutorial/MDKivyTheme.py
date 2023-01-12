#!/usr/bin/env python3.7
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton, MDIconButton, MDFloatingActionButton
from kivy.core.window import Window

Window.clearcolor = (1,1,1,1)
Window.size = (360,600)


class TestApp(MDApp):
    def build(self):

        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "A700"
        self.theme_cls.theme_style = "Dark"


        scr = Screen()

        # btn_flt  = MDFlatButton(text ='Flat btn',
        #                pos_hint = {'center_x':0.5,'center_y':0.5})

        # btn_flt  = MDRectangleFlatButton(text ='Flat btn',
        #                pos_hint = {'center_x':0.5,'center_y':0.5})

        # btn_flt = MDIconButton(icon='android',
        #                        pos_hint = {'center_x':0.5,'center_y':0.5})

        btn_flt = MDFloatingActionButton(icon='android',
                               pos_hint = {'center_x':0.5,'center_y':0.5})

        scr.add_widget(btn_flt)

        return scr


app = TestApp()
app.run()