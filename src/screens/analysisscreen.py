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
from math import isclose


# UI elements
kv_str: str = """
#:import Graph kivy_garden.graph.Graph

<DataGridItem>:
    orientation: "horizontal"
    Label:
        text: f"{root.concentration:.2e}"
    Label:
        text: f"{root.absorbance:.3f}" if root.absorbance is not None else "--"
        
        
<DataGrid@RecycleView>:
    viewclass: 'DataGridItem'
    RecycleBoxLayout:
        default_size: None, dp(56)
        # defines the size of the widget in reference to width and height
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical' # defines the orientation of data item


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
                on_release: app.sm.ask_delete_session(root)
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
                    text: 'Absorbance (U.A.)'
            DataGrid:
                id: data_grid
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
                background_disabled_normal: 'images/blank.png'
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
                id: report_button
                disabled: True
                background_normal: 'images/blank.png'
                background_disabled_normal: 'images/blank.png'
                text: 'Exporter Document'
                on_release: root.export_report()
            ButtonIcon:
                source: "images/next.png"
                size_hint_x: None
                width: self.height
                on_release: app.sm.change_screen('right')
"""


Builder.load_string(kv_str)


class DataGridItem(TouchRippleButtonBehavior, BoxLayout):
    """
    Item class for recycle view
    """
    sample = ObjectProperty(None)
    remove_sample = ObjectProperty(None)
    absorbance = NumericProperty(0.0, allownone=True)
    concentration = NumericProperty(0.0)
    ripple_duration_in = 0.2

    def on_release(self) -> None:
        self.remove_sample(self.sample)


class AnalysisScreen(Screen):
    """
    Analysis screen for display sessions's data as table and graph
    number: id of this session
    """
    number = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = Session()  # class to handle data and perform all operations
        self.data_plot = PointPlot(point_size=dp(5), color=(0, 0, 1, 1))  # plot for measures
        self.regression_plot = LinePlot(color=(0, 1, 1, 1), line_width=dp(2))  # plot for regression line

    def ask_concentration(self):
        """
        Ask user for concentration
        open a popup
        """
        popup = App.get_running_app().concentration_popup
        popup.callback_method = self.ask_sample
        popup.open()

    def ask_sample(self, concentration: float):
        """
        Return method after asking for concentration asks for a data capture
        :param concentration: if None, action is cancelled
        :return:
        """
        if concentration is not None:
            popup = App.get_running_app().capture_popup
            popup.concentration = concentration
            popup.callback_method = self.add_sample
            popup.open()

    def add_sample(self, concentration: float, sample_value: tuple[int, int, int]):
        """
        Add sample to session data
        :param concentration: concentration of this sample
        :param sample_value: tuple (r,g,b) of this sample
        :return:
        """
        sample = Sample(red_value=sample_value[0], green_value=sample_value[1], blue_value=sample_value[2],
                        concentration=concentration)
        self.session.add_sample(sample)
        self.update_data_grid()
        self.update_graph()

    def ask_reference(self):
        """
        Ask user for reference sample
        opens of popup
        """
        popup = App.get_running_app().capture_popup
        popup.concentration = None
        popup.callback_method = self.add_reference
        popup.open()

    def add_reference(self, _, sample_value: tuple[int, int, int]):
        """
        return method to effectively add reference to session
        :param sample_value: tuple(r,g,b) to set as reference sample
        """
        reference = Sample(red_value=sample_value[0], green_value=sample_value[1], blue_value=sample_value[2])
        # Clock.schedule_once(lambda dt: ConcentrationPopup().open(), 0.2)
        self.ids.baseline_button.color = [0, 1, 0, 1]
        self.session.reference = reference
        self.update_data_grid()
        self.update_graph()

    def ask_remove_sample(self, sample: Sample):
        """
        asks if the user wants to remove a specific sample
        :param sample: sample to remove
        """
        popup = Factory.ConfirmPopup()
        popup.message = 'Voulez-vous effacer cet échantillon ?'
        popup.ok_callback = self.remove_sample
        popup.callback_data = sample
        popup.open()

    def remove_sample(self, sample: Sample):
        """
        return mathod to remove a specific sample after confirmation
        :param sample: sample to be removed
        """
        self.session.remove_sample(sample)
        self.update_data_grid()
        self.update_graph()

    def ask_evaluate_concentration(self):
        """
        asks the user to perform a capture to evaluate a concentration
        open a capture popup
        """
        popup = App.get_running_app().capture_popup
        popup.concentration = None
        popup.callback_method = self.evaluate_concentration
        popup.open()

    def evaluate_concentration(self, _, value: tuple[int, int, int]):
        """
        evaluate a concentration effectively for a given sample and displays the result
        :param value: tuple(r,g,b) of the sample
        """
        sample = Sample(red_value=value[0], green_value=value[1], blue_value=value[2])
        concentration = self.session.compute_concentration_from_sample(sample)
        popup = EvalConcentrationPopup()
        popup.absorbance_value = sample.absorbance
        popup.concentration_value = concentration
        popup.open()

    def update_data_grid(self):
        """
        updates the data grid after changes
        """
        self.ids.data_grid.data = [{'concentration': item[0], 'absorbance': item[1], 'sample': item[2], 'remove_sample': self.ask_remove_sample} for item in self.session.absorbance_data_points]

    def update_graph(self):
        """
        updates the graphs after changes
        """
        try:
            graph: Graph = self.ids.data_plot
            # if we can plot data
            if self.session.reference is not None and len(self.session.absorbance_data_points) > 0:
                # prepare plot data (points)
                max_absorbance = 0
                max_concentration = 0
                data_points = self.session.absorbance_data_points
                coordinates_list = []
                for i in range(len(data_points)):
                    if data_points[i][1] is not None and data_points[i][1] > max_absorbance:
                        max_absorbance = data_points[i][1]
                    if data_points[i][0] > max_concentration:
                        max_concentration = data_points[i][0]
                    coordinates_list.append((data_points[i][0], data_points[i][1]))
                self.data_plot.points = coordinates_list
                # max graphique = max val + 10%
                if isclose(max_concentration, 0.0):
                    graph.xmax = 0.001
                else:
                    graph.xmax = max_concentration * 1.1
                if isclose(max_absorbance, 0.0):
                    graph.ymax = 0.1
                else:
                    graph.ymax = max_absorbance * 1.1
                # plot data (line)
                a, r2 = self.session.absorbance_data_line
                line_points = [(0, 0), (max_concentration, max_concentration * a)]
                self.regression_plot.points = line_points
                # equation
                self.ids.equation.text = f'A = {a:.3e} C'
                if r2 is not None:
                    self.ids.equation.text += f' (R²={r2:.4f})'
                # enable buttons
                self.ids.concentration_button.disabled = False
                self.ids.report_button.disabled = False
                # add plots if not already in graph
                if self.data_plot not in graph.plots:
                    graph.add_plot(self.data_plot)
                if self.regression_plot not in graph.plots:
                    graph.add_plot(self.regression_plot)
            # remove plots / disable buttons / remove equation if we can't plot
            else:
                raise TypeError  # to eliminate duplicate... same code as if there were errors
        except (ZeroDivisionError, TypeError):
            # remove plots
            if self.data_plot is not None:
                graph.remove_plot(self.data_plot)
            if self.regression_plot is not None:
                graph.remove_plot(self.regression_plot)
            # disable buttons
            self.ids.concentration_button.disabled = True
            self.ids.report_button.disabled = True
            # clear equation
            self.ids.equation.text = ''
    
    def export_report(self):
        """
        Exports the session data and graph to a pdf document
        """
        self.session.export_report(self.number)
        popup = Factory.MessagePopup(message='le fichier est disponible dans votre dossier document.')
        popup.open()
