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
from kivy_garden.graph import Graph, LinePlot, PointPlot
from kivy.metrics import dp
from popups import EvalConcentrationPopup


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
            id: data_plot
            xlabel: 'concentration (mol/L)'
            ylabel: 'absorbance'
            xmin: 0
            ymin: 0
            ymax: 3
            xmax: 0.01
            y_grid_label: True
            x_grid_label: True
            y_ticks_major: 0.1
            x_ticks_major: 0.001
            y_grid: True
            x_grid: True
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.2
            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: 'Equation'
                Label:
                    id: equation
            Button:
                id: concentration_button
                disabled: True
                background_normal: 'images/blank.png'
                text: 'Calculer une concentration'
                on_release: root.ask_evaluate_concentration()
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(50)
            ButtonIcon:
                source: "images/previous.png"
                size_hint_x: None
                width: self.height
                on_release: app.sm.change_screen('left')
            Button:
                background_normal: 'images/blank.png'
                text: 'Exporter Doocument'
                on_release: root.export_report()
            ButtonIcon:
                source: "images/next.png"
                size_hint_x: None
                width: self.height
                on_release: app.sm.change_screen('right')
"""


Builder.load_string(kv_str)


class ButtonIcon(ButtonBehavior, Image):
    background_color = ColorProperty([1, 1, 1, 1])
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
        self.data_plot = PointPlot(point_size=dp(5), color=(0, 0, 1, 1))
        self.regression_plot = LinePlot(color=(0, 1, 1, 1), line_width=dp(2))

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

    def ask_evaluate_concentration(self):
        popup = App.get_running_app().capture_popup
        popup.concentration = None
        popup.callback_method = self.evaluate_concentration
        popup.open()

    def evaluate_concentration(self, _, value):
        sample = Sample(red_value=value[0], green_value=value[1], blue_value=value[2])
        concentration = self.session.compute_concentration_from_sample(sample)
        popup = EvalConcentrationPopup()
        popup.absorbance_value = sample.absorbance
        popup.concentration_value = concentration
        popup.open()

    def update_data_grid(self):
        self.ids.data_grid.data = [{'concentration': item[0], 'absorbance': item[1], 'sample': item[2], 'remove_sample': self.ask_remove_sample} for item in self.session.absorbance_data_points]

    def update_graph(self):
        try:
            if self.session.reference is not None and len(self.session.absorbance_data_points) > 0:
                graph: Graph = self.ids.data_plot
                Amax = 0
                Cmax = 0
                data_points = self.session.absorbance_data_points
                coordonates_list = []
                for i in range(len(data_points)):
                    if data_points[i][1]is not None and data_points[i][1] > Amax:
                        Amax = data_points[i][1]
                    if data_points[i][0] > Cmax:
                        Cmax = data_points[i][0]
                    coordonates_list.append((data_points[i][0], data_points[i][1]))
                self.data_plot.points = coordonates_list
                graph.xmax = Cmax * 1.1
                graph.ymax = Amax * 1.1
                coefs, r2 = self.session.absorbance_data_line
                self.ids.concentration_button.disabled = False
                self.ids.equation.text = f'A = {coefs[1]:.3e} C'
                if r2 is not None:
                    self.ids.equation.text += f' (R²={r2:.4f})'
                line_points = [(0, 0), (Cmax, Cmax*coefs[1])]
                self.regression_plot.points = line_points
                if self.data_plot not in graph.plots:
                    graph.add_plot(self.data_plot)
                if self.regression_plot not in graph.plots:
                    graph.add_plot(self.regression_plot)
        except ZeroDivisionError:
            self.ids.concentration_button.disabled = True
        except TypeError:
            self.ids.concentration_button.disabled = True

    def export_report(self):
        self.session.export_report(self.number)
