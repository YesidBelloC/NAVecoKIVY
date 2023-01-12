import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.graph import Graph, LinePlot
import numpy as np

KV = '''
#:import utils kivy.utils

<MainGrid>:
    canvas.before:
        Color:
            rgb: utils.get_color_from_hex('#212946')
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint: 1, 1
        orientation: 'vertical'
        padding: 10, 10, 0, 10

        ScrollView:
            id: view
            do_scroll_x: True
            do_scroll_y: False
            orientation: 'vertical'
            size_hint: 1, 0.5
            valign: 'middle'
            bar_width: 4
            bar_color: 1, 1, 1, 1
            bar_inactive_color: 1, 1, 1, 0.5
            scroll_type: ['content']

            BoxLayout:
                orientation: 'vertical'
                size_hint: None, 1
                width: view.width*root.zoom
                BoxLayout:
                    id: modulation
                    size_hint_x: 1
                    size_hint_y: 1

# without scroll
#    BoxLayout:
#        size_hint: 1, 1
#        orientation: 'vertical'
#        padding: 10, 10, 0, 10
#        BoxLayout:
#            size_hint: 1, 0.5
#            id: modulation

        BoxLayout:
            id: zoom
            orientation: 'horizontal'
            size_hint: 1, 0.1
            padding: 10

            Button:
                text: '-'
                size_hint_x: None
                width: self.height
                on_release: root.update_zoom(self.text)

            Label:
                text: str(int(root.zoom)) + 'x'

            Button:
                text: '+'
                size_hint_x: None
                width: self.height
                on_release: root.update_zoom(self.text)

        BoxLayout:
            size_hint: 1, 0.1
            orientation: 'vertical'

            Label:
                text: 'Frequency: ' + str(freq.value) + ' hz'

            Slider:
                id: freq
                min: 1
                max: 20
                step: 0.5
                on_value: root.update_plot(freq.value)

        BoxLayout:
            size_hint: 1, 0.3
'''

class MainApp(App):

    def build(self):
		Builder.load_string(KV)
        return MainGrid()


class MainGrid(BoxLayout):

    zoom = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.samples = 512
        self.zoom = 1
        self.graph = Graph(y_ticks_major=0.5,
                           x_ticks_major=64,
                           border_color=[0, 1, 1, 1],
                           tick_color=[0, 1, 1, 0.7],
                           x_grid=True, y_grid=True,
                           xmin=0, xmax=self.samples,
                           ymin=-1.0, ymax=1.0,
                           draw_border=False,
                           x_grid_label=True, y_grid_label=False)

        self.ids.modulation.add_widget(self.graph)
        self.plot_x = np.linspace(0, 1, self.samples)
        self.plot_y = np.zeros(self.samples)
        self.plot = LinePlot(color=[1, 1, 0, 1], line_width=1.5)
        self.graph.add_plot(self.plot)
        self.update_plot(1)

    def update_plot(self, freq):
        self.plot_y = np.sin(2*np.pi*freq*self.plot_x)
        self.plot.points = [(x, self.plot_y[x]) for x in range(self.samples)]

    def update_zoom(self, value):
        if value == '+' and self.zoom < 8:
            self.zoom *= 2
            self.graph.x_ticks_major /= 2
        elif value == '-' and self.zoom > 1:
            self.zoom /= 2
            self.graph.x_ticks_major *= 2


MainApp().run()