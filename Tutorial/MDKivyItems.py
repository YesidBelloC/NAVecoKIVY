#!/usr/bin/env python3.7
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
from kivymd.uix.scrollview import ScrollView


class TestApp(MDApp):
    def build(self):

        scr = Screen()

        scroll = ScrollView()
        lstview = MDList()

        icon = IconLeftWidget(icon="android")

        item1 = OneLineListItem(text='android1')
        item2 = TwoLineListItem(text='android2',
                                secondary_text = 'Description')
        item3 = ThreeLineListItem(text='android2',
                                  secondary_text = 'Description',
                                  tertiary_text = 'Description')
        item4 = OneLineIconListItem(text='str(i) +  item')
        item4.add_widget(icon)

        lstview.add_widget(item1)
        lstview.add_widget(item2)
        lstview.add_widget(item3)
        lstview.add_widget(item4)

        scr.add_widget(scroll)

        scroll.add_widget(lstview)

        return scr


app = TestApp()
app.run()