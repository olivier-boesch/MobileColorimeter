"""
Main application file
=====================
Colorimeter App
"""
import webbrowser
from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.logger import Logger
from kivy.utils import platform
from kivy.uix.rst import RstDocument
from kivy.properties import NumericProperty, ColorProperty, StringProperty, ListProperty
from kivy.uix.image import Image
from kivy.factory import Factory
from kivy.lang import Builder
from android_permissions import AndroidPermissions
from screens.mainscreen import MainScreen
from screens.analysisscreen import AnalysisScreen
from popups import CapturePopup, ConcentrationPopup

LINKS: dict[str, str] = {
    'github': "https://github.com/olivier-boesch/MobileColorimeter",
    'icone': "https://thenounproject.com/icon/spectrometer-5707903/",
    'kivy': "https://kivy.org/"
}


__version__ = "0.9.6"


if platform not in ["android", "ios"]:
    Logger.info("Config: disabling multi touch on desktop")
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_multitouch')

kv: str = """
<ButtonIcon>:
    state_image: self.background_normal if self.state == 'normal' else self.background_down
    disabled_image: self.background_disabled_normal if self.state == 'normal' else self.background_disabled_down
    canvas.before:
        Color:
            rgba: self.background_color
        BorderImage:
            border: self.border
            pos: self.pos
            size: self.size
            source: self.disabled_image if self.disabled else self.state_image
"""

Builder.load_string(kv)


class ButtonIcon(ButtonBehavior, Image):
    """
    Button with image
    """
    background_color = ColorProperty([1, 1, 1, 1])
    background_normal = StringProperty('images/blank.png')
    background_down = StringProperty(
        'atlas://data/images/defaulttheme/button_pressed'
    )
    background_disabled_normal = StringProperty('atlas://data/images/defaulttheme/button_disabled')
    background_disabled_down = StringProperty(
        'atlas://data/images/defaulttheme/button_disabled_pressed'
    )
    border = ListProperty([16, 16, 16, 16])


class InfoRstDocument(RstDocument):
    """
    Class to display custom RST doc on main screen
    """

    def on_source(self, instance: "InfoRstDocument", value: str) -> None:
        """
        Called when a file is loaded
        replace the version in the content
        :param instance: InfoRstDocument object (not used)
        :param value: value of the source (not used)
        :return:
        """
        super().on_source(instance, value)
        self.text = self.text.replace('{version}', App.get_running_app().version)

    def on_ref_press(self, node, ref: str) -> None:
        """
        Called when a link is pressed
        :param node: which node is it (not used)
        :param ref: what ref was pressed
        """
        try:
            webbrowser.open(LINKS[ref])
        except KeyError:
            Logger.info(f"Rst: Bad link ref -> {ref}")


class MyScreenManager(ScreenManager):
    """
    Screen manager of the app
    """
    # higher number for session number (always higher in a use)
    last_number_for_analysis = NumericProperty(0)

    def change_screen(self, direction: str) -> None:
        """
        Screen change with transition
        :param direction: where to move the screen
        """
        Logger.info(f"Ui: Moving \"{direction}\"")
        if direction == 'left':
            self.transition.direction = 'right'
            cur = self.screen_names.index(self.current)
            self.current = self.screen_names[(cur - 1) % len(self.screen_names)]
        if direction == 'right':
            self.transition.direction = 'left'
            cur = self.screen_names.index(self.current)
            self.current = self.screen_names[(cur + 1) % len(self.screen_names)]

    def add_session(self) -> None:
        """
        Add a new session to the screen manager (a new screen analysis)
        :return:
        """
        session_screen_name = 'analysis_screen' + str(self.last_number_for_analysis)
        Logger.info(f"Session: Adding \"{session_screen_name}\"")
        self.add_widget(AnalysisScreen(name=session_screen_name,
                                       number=self.last_number_for_analysis))
        self.transition.direction = 'up'
        self.current = session_screen_name
        Logger.info(f"Session: Updated screens list {self.screen_names!s}")
        self.last_number_for_analysis += 1

    def ask_delete_session(self, screen: str) -> None:
        """
        Ask the user to delete or not a session
        :param screen: screen where the button was pressed
        """
        popup = Factory.ConfirmPopup()
        popup.message = 'Voulez-vous effacer cette session ?'
        popup.ok_callback = self.delete_session
        popup.callback_data = screen
        popup.open()

    def find_screen(self, screen_name: str) -> Screen:
        """
        Finds the screen
        :param screen_name: name of the screen
        """
        for screen in self.screens:
            if screen.name == screen_name:
                return screen
        return None

    def delete_session(self, screen: Screen) -> None:
        """
        Effectively deletes the session
        :param screen: screen object to delete
        """
        Logger.info(f"Session: Deleting \"{screen.name}\"")
        cur = self.screen_names.index(screen.name)
        self.transition.direction = 'down'
        self.remove_widget(screen)
        Logger.info(f"Session: Updated screens list {self.screen_names!s}")
        self.current = self.screen_names[(cur - 1) % len(self.screen_names)]


class MobileColorimeterApp(App):
    """
    Mobile colorimeter main class
    """
    title = "Mobile Colorimeter"
    icon = "images/logo.png"
    capture_popup = CapturePopup()
    concentration_popup = ConcentrationPopup()
    version = __version__
    dont_gc = None
    sm = None

    def build(self):
        self.sm = MyScreenManager()
        self.sm.add_widget(MainScreen(name='main_screen'))
        self.sm.current = "main_screen"
        return self.sm

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)

    def start_app(self):
        """
        called when the app starts
        """
        self.dont_gc = None


if __name__ == "__main__":
    MobileColorimeterApp().run()
