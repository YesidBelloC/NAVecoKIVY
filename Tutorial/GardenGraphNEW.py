from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics.vertex_instructions import Ellipse
from kivy.graphics.context_instructions import Color
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window

from math import sin
from kivy_garden.graph import Graph, MeshLinePlot
# pip install kivy_garden.graph

# Window.size = (400,700)

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
KV = """
BoxLayout:
    ScreenManager:
        id: screen_manager

        Screen:
            id:menu
            name: "Menu"
            BoxLayout:
                id:graphID
                orientation:'vertical'
                BoxLayout:
                    orientation:'horizontal'
                    Button:
                        text: 'Goto settings'
                        on_press: root.ids.screen_manager.current = 'Settings'
                    Button:
                        text: 'Quit'

        Screen:
            id:settings
            name: "Settings"
            MyBoxLayout:
                id:PieChartID
                orientation:'vertical'
                BoxLayout:
                    orientation:'horizontal'
                    Button:
                        text: 'My settings button'
                    Button:
                        text: 'Back to menu'
                        on_press: root.ids.screen_manager.current = 'Menu'



"""
class MyBoxLayout(BoxLayout):
    grpEXT = ObjectProperty(None)
    grpINT = ObjectProperty(None)

class TestApp(App):

    def build(self):
        # Create the screen manager
        root = Builder.load_string(KV)

        DataElev = [0,1,2,4,1,5,7,4,8,5,4,1,2,4,5,1,0,1,45]

        graph = Graph(xlabel='Time [s]', ylabel='Speed [m/s]', x_ticks_minor=5,
        x_ticks_major=25, y_ticks_major=1,
        y_grid_label=True, x_grid_label=True, padding=5,
        x_grid=True, y_grid=True, xmin=0, xmax=len(DataElev), ymin=min(DataElev), ymax=max(DataElev))
        plot = MeshLinePlot(color=[103/255,59/255,183/255, 1])
        plot.points = [(x, DataElev[x]) for x in range(0, len(DataElev))]
        graph.add_plot(plot)

        root.ids.graphID.add_widget(graph)

        Data = 20
        DataMax = 100
        DistancePieChartEXT = Ellipse(angle_start=0,angle_end=20,pos=(300,300),size=(130,130))
        DistancePieChartINT = Ellipse(angle_start=0,angle_end=360,pos=(300,300),size=(130,130))

        if root.ids.PieChartID.grpINT is not None:
            # just update the group with updated lines lines
            root.ids.PieChartID.grpINT.clear()
            Color(188/255,168/255,231/255,1)  # line color blue
            root.ids.PieChartID.grpINT.add(DistancePieChartINT)
        else:
            with root.ids.PieChartID.canvas.after:
                Color(188/255,168/255,231/255,1)  # line color blue
                root.ids.PieChartID.grpINT = InstructionGroup()
                root.ids.PieChartID.grpINT.add(DistancePieChartINT)

        if root.ids.PieChartID.grpEXT is not None:
            # just update the group with updated lines lines
            root.ids.PieChartID.grpEXT.clear()
            Color(103/255,59/255,183/255,1)  # line color blue
            root.ids.PieChartID.grpEXT.add(DistancePieChartEXT)
        else:
            with root.ids.PieChartID.canvas.after:
                Color(103/255,59/255,183/255,1)  # line color blue
                root.ids.PieChartID.grpEXT = InstructionGroup()
                root.ids.PieChartID.grpEXT.add(DistancePieChartEXT)







        print('root loaded')

        return root

if __name__ == '__main__':
    TestApp().run()