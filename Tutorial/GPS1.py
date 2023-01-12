from kivy.lang import Builder
from plyer import gps
from kivy.app import App
from kivy.properties import StringProperty
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.clock import Clock

UsrLat = 0.0
UsrLon = 0.0
UsrSpd = 0.0
UsrBrg = 0.0
UsrAlt = 0.0
UsrAcc = 0.0

kv = '''
BoxLayout:
    orientation: 'vertical'
    Label:
        text: app.gps_location
    Label:
        text: app.gps_status
    BoxLayout:
        size_hint_y: None
        height: '48dp'
        padding: '4dp'
        ToggleButton:
            text: 'Meassure'
            on_state:
                app.meassure
'''


class GpsTest(App):

    gps_location = StringProperty()
    gps_status = StringProperty('Click Start to get GPS location updates')

    def request_android_permissions(self):
        """
        Since API 23, Android requires permission to be requested at runtime.
        This function requests permission and handles the response via a
        callback.
        The request will produce a popup if permissions have not already been
        been granted, otherwise it will do nothing.
        """
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            """
            Defines the callback to be fired when runtime permission
            has been granted or denied. This is not strictly required,
            but added for the sake of completeness.
            """
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([Permission.ACCESS_COARSE_LOCATION,
                             Permission.ACCESS_FINE_LOCATION], callback)
        # # To request permissions without a callback, do:
        # request_permissions([Permission.ACCESS_COARSE_LOCATION,
        #                      Permission.ACCESS_FINE_LOCATION])

    def build(self):
        try:
            gps.configure(on_location=self.print_locations)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'

        Clock.schedule_interval(self.meassure, 1)

        if platform == "android":
            print("gps.py: Android detected. Requesting permissions")
            self.request_android_permissions()

        return Builder.load_string(kv)


    def meassure(self, **kwargs):
        gps.configure(on_location=self.print_locations)
        gps.start()

        print('Meassures has been done')

        gps.stop()

    def print_locations(**kwargs):
        # print 'lat: {lat}, lon: {lon}'.format(**kwargs)

        self.gps_location = '\n'.join([
            '{}={}'.format(k, v) for k, v in kwargs.items()])
        UsrLat = kwargs["lat"]
        UsrLon = kwargs["lon"]
        UsrSpd = kwargs["speed"]
        UsrBrg = kwargs["bearing"]
        UsrAlt = kwargs["altitude"]
        UsrAcc = kwargs["accuracy"]

        print('Data obtained from GPS:')
        print(UsrLat)
        print(UsrLon)
        print(UsrSpd)
        print(UsrBrg)
        print(UsrAlt)
        print(UsrAcc)



    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(1000, 0)
        pass


if __name__ == '__main__':
    GpsTest().run()