from kivy.uix.screenmanager import Screen
from colorimetry import Session, Sample
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.properties import NumericProperty, ColorProperty, StringProperty, ListProperty, ObjectProperty
from kivy.app import App
from kivy.base import Builder
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior, TouchRippleButtonBehavior
from kivy.factory import Factory

kv_str = """
#:import Graph kivy_garden.graph.Graph

<DataGridItem>:
    orientation: "horizontal"
    Label:
        text: f"{root.concentration:.2e}"
    Label:
        text: f"{root.absorbance:.3f}" if root.absorbance is not None else "--"


<AnalysisScreen>:
    BoxLayout:
        padding: dp(10)
        spacing: dp(5)
        orientation: "vertical"
        # upper bar
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(50)
            ButtonIcon:
                source: "images/sample.png"
                size_hint_x: None
                width: self.height
                on_release: root.ask_concentration()
            ButtonIcon:
                id: baseline_button
                color: 1, 0, 0, 1
                source: "images/baseline.png"
                size_hint_x: None
                width: self.height
                on_release: root.ask_reference()
            Label:
                text: f"Analyse par colorimétrie (n°{root.number!s})"
            ButtonIcon:
                source: "images/trash.png"
                size_hint_x: None
                width: self.height
                on_release: app.ask_delete_session(root)
        BoxLayout:
            orientation: 'vertical'
            padding: dp(5)
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: dp(20)
                Label:
                    text: 'Concentration (mol/L)'
                Label:
                    text: 'Absorbance'
            DataGrid:
                id: data_grid
                viewclass: 'DataGridItem'
                RecycleBoxLayout:
                    default_size: None, dp(56)
                    # defines the size of the widget in reference to width and height
                    default_size_hint: 1, None
                    size_hint_y: None
                    height: self.minimum_height
                    orientation: 'vertical' # defines the orientation of data item
        Graph:
            xlabel: 'concentration (mol/L)'
            ylabel: 'absorbance'
            xmin: 0
            ymin: 0
            ymax: 3
            xmax: 0.01
            y_grid_label: True
            x_grid_label: True
            y_ticks_major: 0.2
            x_ticks_major: 0.001
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(50)
            ButtonIcon:
                source: "images/previous.png"
                size_hint_x: None
                width: self.height
                on_release: app.sm.change_screen('left')
            Label:
            ButtonIcon:
                source: "images/next.png"
                size_hint_x: None
                width: self.height
                on_release: app.sm.change_screen('right')
"""


Builder.load_string(kv_str)


class ButtonIcon(ButtonBehavior, Image):
    background_color = ColorProperty([1, 1, 1, 1])
    # background_normal = StringProperty('atlas://data/images/defaulttheme/button')
    background_normal = StringProperty('images/blank.png')
    background_down = StringProperty('atlas://data/images/defaulttheme/button_pressed')
    background_disabled_normal = StringProperty('atlas://data/images/defaulttheme/button_disabled')
    background_disabled_down = StringProperty('atlas://data/images/defaulttheme/button_disabled_pressed')
    border = ListProperty([16, 16, 16, 16])


class DataGridItem(TouchRippleButtonBehavior, BoxLayout):
    sample = ObjectProperty(None)
    remove_sample = ObjectProperty(None)
    absorbance = NumericProperty(0.0, allownone=True)
    concentration = NumericProperty(0.0)
    ripple_duration_in = 0.2

    def on_release(self):
        self.remove_sample(self.sample)


class DataGrid(RecycleView):
    pass


class AnalysisScreen(Screen):
    number = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = Session()
        # for test

    def ask_concentration(self):
        popup = App.get_running_app().concentration_popup
        popup.callback_method = self.ask_sample
        popup.open()

    def ask_sample(self, concentration):
        if concentration is not None:
            popup = App.get_running_app().capture_popup
            popup.concentration = concentration
            popup.callback_method = self.add_sample
            popup.open()

    def add_sample(self, concentration, sample_value):
        sample = Sample(red_value=sample_value[0], green_value=sample_value[1], blue_value=sample_value[2],
                        concentration=concentration)
        # Clock.schedule_once(lambda dt: ConcentrationPopup().open(), 0.2)
        self.session.add_sample(sample)
        self.update_data_grid()
        self.update_graph()

    def ask_reference(self):
        popup = App.get_running_app().capture_popup
        popup.concentration = None
        popup.callback_method = self.add_reference
        popup.open()

    def add_reference(self, _, sample_value):
        reference = Sample(red_value=sample_value[0], green_value=sample_value[1], blue_value=sample_value[2])
        # Clock.schedule_once(lambda dt: ConcentrationPopup().open(), 0.2)
        self.ids.baseline_button.color = [0, 1, 0, 1]
        self.session.reference = reference
        self.update_data_grid()
        self.update_graph()

    def ask_remove_sample(self, sample):
        popup = Factory.ConfirmPopup()
        popup.message = 'Voulez-vous effacer cet échantillon ?'
        popup.ok_callback = self.remove_sample
        popup.callback_data = sample
        popup.open()

    def remove_sample(self, sample):
        self.session.remove_sample(sample)
        self.update_data_grid()
        self.update_graph()

    def update_data_grid(self):
        list_data_points = self.session.absorbance_data_points
        self.ids.data_grid.data = [{'concentration': item[0], 'absorbance': item[1], 'sample': item[2], 'remove_sample': self.ask_remove_sample} for item in list_data_points]

    def update_graph(self):
        pass
