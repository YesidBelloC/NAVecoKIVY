from kivy.graphics.context_instructions import Color
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics.vertex_instructions import Line
from kivy.properties import ObjectProperty

from kivy.garden.mapview import MapView, MapMarker, MapMarkerPopup
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp

kv = '''
FloatLayout:
    MyMapView:
        id: map
        zoom: 15
        lat: 36.77418821888212
        lon: 3.052954737671183
        double_tap_zoom: True
'''

class MyMapView(MapView):
    grp = ObjectProperty(None)

class MapViewApp(App):
    def build(self):
        self.root = Builder.load_string(kv)
        self.Pin1 = MapMarkerPopup(lat=36.77418821888212,lon= 3.052954737671183, source='C:/Users/crybelloceferin/Documents/Kivy/NAVecoKivyPYKV/img/PinStart.png')
        self.Pin2 = MapMarkerPopup(lat=36.77,lon= 3.06, source='C:/Users/crybelloceferin/Documents/Kivy/NAVecoKivyPYKV/img/PinEnd.png')
        self.root.ids.map.add_widget(self.Pin1)
        self.root.ids.map.add_widget(self.Pin2)
        Clock.schedule_interval(self.info,1/60)
        return self.root

    def info(self, *args):

        Market1 = MapMarker(lat=36.77418821888212,lon= 3.052954737671183)
        Market2 = MapMarker(lat=36.78,lon= 3.0529)
        Market3 = MapMarker(lat=36.77,lon= 3.06)
        self.root.ids.map.add_marker(Market1)
        self.root.ids.map.add_marker(Market2)
        self.root.ids.map.add_marker(Market3)
        points = [[Market1.center_x, Market1.y],
                 [Market2.center_x, Market2.y],
                 [Market3.center_x, Market3.y],
                 ]
        lines = Line()
        lines.points = points
        lines.width = 2
        if self.root.ids.map.grp is not None:
            # just update the group with updated lines lines
            self.root.ids.map.grp.clear()
            # self.root.ids.map.remove_widget(self.Pin1)
            # self.root.ids.map.remove_widget(self.Pin2)
            self.root.ids.map.grp.add(lines)
        else:
            with self.root.ids.map.canvas.after:
                #  create the group and add the lines
                Color(1,0,0,1)  # line color
                self.root.ids.map.grp = InstructionGroup()
                self.root.ids.map.grp.add(lines)

MapViewApp().run()