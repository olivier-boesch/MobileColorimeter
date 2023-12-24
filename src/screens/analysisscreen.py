from kivy.uix.screenmanager import Screen
from colorimetry import Session, Sample
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.properties import NumericProperty


class DataGridItem(BoxLayout):
    absorbance = NumericProperty(0.0)
    concentration = NumericProperty(0.0)


class DataGrid(RecycleView):
    pass


class AnalysisScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = Session()

    def ask_sample(self):
        print("Adding sample")

    def ask_reference(self):
        print("Adding reference")
