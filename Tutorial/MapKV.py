from kivy.graphics.context_instructions import Color
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics.vertex_instructions import Line
from kivy.properties import ObjectProperty

from kivy_garden.mapview import MapView, MapMarker
from kivy.app import App
from kivy.lang import Builder

kv = '''
FloatLayout:
    MyMapView:
        m1: marker1
        m2: marker2
        size_hint: 1, 0.9
        pos_hint: {'y':0.1}
        zoom: 15
        lat: 36.77418821888212
        lon: 3.052954737671183
        double_tap_zoom: True
        MapMarker:
            id: marker1
            lat: 36.77418821888212
            lon: 3.052954737671183
            on_release: app.marker_released(self)
        MapMarker:
            id: marker2
            lat:  36.77
            lon: 3.06
            on_release: app.marker_released(self)

    Button:
        size_hint: 0.1, 0.1
        text: 'info'
        on_release: app.info()
'''

class MyMapView(MapView):
    grp = ObjectProperty(None)

    def do_update(self, dt):  # this over-rides the do_update() method of MapView
        super(MyMapView, self).do_update(dt)
        self.draw_lines()

    # draw the lines
    def draw_lines(self):
        points = [[self.m1.center_x, self.m1.y], [self.m2.center_x, self.m2.y]]  # get the points for the lines from somewhere
        lines = Line()
        lines.points = points
        lines.width = 2
        if self.grp is not None:
            # just update the group with updated lines lines
            self.grp.clear()
            self.grp.add(lines)
        else:
            with self.canvas.after:
                #  create the group and add the lines
                Color(1,0,0,1)  # line color
                self.grp = InstructionGroup()
                self.grp.add(lines)


class MapViewApp(App):
    def build(self):
        return Builder.load_string(kv)

    def info(self, *args):
        print(self.root.ids.marker1)
        print(self.root.ids.marker2)

    def marker_released(self, marker):
        print(marker)

MapViewApp().run()