from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.pickers import MDTimePicker
from kivymd.uix.screen import MDScreen


class Test(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        return (
            MDScreen(
                MDRaisedButton(
                    text="Open time picker",
                    pos_hint={'center_x': .5, 'center_y': .5},
                    on_release=self.show_time_picker,
                )
            )
        )

    def show_time_picker(self, *args):
        '''Open time picker dialog.'''

        ClockTime = MDTimePicker()
        ClockTime.bind(on_cancel=self.on_cancel, time=self.get_time)
        ClockTime.open()

    def get_time(self, instance, time):

        print(time)
        return time

    def on_cancel(self, instance, time):

        print('Calcel')


Test().run()