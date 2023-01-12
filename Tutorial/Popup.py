import kivy
from kivy.app import App
kivy.require('1.9.0')

from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.config import Config

Config.set('graphics', 'resizable', True)


class PopupExample(App):

	def build(self):
		self.layout = GridLayout(cols = 1, padding = 10)

		self.button = Button(text ="Click for pop-up")
		self.layout.add_widget(self.button)

		self.button.bind(on_press = self.onButtonPress)

		return self.layout

	def onButtonPress(self, button):

		layout = GridLayout(cols = 1, padding = 10)

		popupLabel = Label(text = "Click for pop-up")
		closeButton = Button(text = "Close the pop-up")

		layout.add_widget(popupLabel)
		layout.add_widget(closeButton)

		popup = Popup(title ='Demo Popup',
					content = layout)
		popup.open()

		closeButton.bind(on_press = popup.dismiss)

if __name__ == '__main__':
	PopupExample().run()
