from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from android_permissions import AndroidPermissions
from screens.mainscreen import MainScreen
from screens.analysisscreen import AnalysisScreen
from kivy.logger import Logger
from kivy.utils import platform
from kivy.uix.rst import RstDocument
from popups import CapturePopup, ConcentrationPopup
from kivy.properties import NumericProperty
from kivy.factory import Factory
from kivy.base import Builder
import webbrowser

LINKS = {
    'github': "https://github.com/olivier-boesch/MobileColorimeter",
    'icone': "https://thenounproject.com/icon/spectrometer-5707903/",
    'kivy': "https://kivy.org/"
}

__version__ = "0.5"

if platform not in ["android", "ios"]:
    Logger.info("Config: disabling multitouch on desktop")
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_multitouch')


kv = """
<ConfirmPopup@Popup>:
    title: 'Confirmer ?'
    message: ''
    ok_callbkack: None
    callback_data: None
    size_hint: 0.5, None
    height: dp(70) + box.minimum_height
    BoxLayout:
        size_hint_y: None
        height: self.minimum_height
        id: box
        orientation: 'vertical'
        spacing: dp(10)
        Label:
            size_hint_y: None
            height: self.texture_size[1]
            id: label
            text: root.message
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            orientation: 'horizontal'
            Button:
                text: 'Annuler'
                on_release: root.dismiss()
            Button:
                text: 'Ok'
                on_release: root.ok_callback(root.callback_data); root.dismiss()

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


class InfoRstDocument(RstDocument):

    def on_source(self, instance, value):
        super().on_source(instance, value)
        self.text = self.text.replace('{version}', App.get_running_app().version)

    def on_ref_press(self, node, ref):
        try:
            webbrowser.open(LINKS[ref])
        except KeyError:
            Logger.info(f"Rst: Bad link ref -> {ref}")


class MyScreenManager(ScreenManager):
    last_number_for_analysis = NumericProperty(0)

    def change_screen(self, direction):
        Logger.info(f"Ui: Moving \"{direction}\"")
        if direction == 'left':
            self.transition.direction = 'right'
            cur = self.screen_names.index(self.current)
            self.current = self.screen_names[(cur - 1) % len(self.screen_names)]
        if direction == 'right':
            self.transition.direction = 'left'
            cur = self.screen_names.index(self.current)
            self.current = self.screen_names[(cur + 1) % len(self.screen_names)]

    def add_session(self):
        session_screen_name = 'analysisscreen' + str(self.last_number_for_analysis)
        Logger.info(f"Session: Adding \"{session_screen_name}\"")
        self.add_widget(AnalysisScreen(name=session_screen_name, number=self.last_number_for_analysis))
        self.transition.direction = 'up'
        self.current = session_screen_name
        Logger.info(f"Session: Updated screens list {self.screen_names!s}")
        self.last_number_for_analysis += 1

    def ask_delete_session(self, screen):
        popup = Factory.ConfirmPopup()
        popup.message = 'Voulez-vous effacer cette session ?'
        popup.ok_callback = self.delete_session
        popup.callback_data = screen
        popup.open()

    def find_screen(self, screen_name):
        for screen in self.screens:
            if screen.name == screen_name:
                return screen

    def delete_session(self, screen):
        Logger.info(f"Session: Deleting \"{screen.name}\"")
        cur = self.screen_names.index(screen.name)
        self.transition.direction = 'down'
        self.remove_widget(screen)
        Logger.info(f"Session: Updated screens list {self.screen_names!s}")
        self.current = self.screen_names[(cur - 1) % len(self.screen_names)]


class MobileColorimeterApp(App):
    title = "Mobile Colorimter"
    icon = "images/logo.png"
    capture_popup = CapturePopup()
    concentration_popup = ConcentrationPopup()
    version = __version__

    def build(self):
        self.sm = MyScreenManager()
        self.sm.add_widget(MainScreen(name='mainscreen'))
        self.sm.current = "mainscreen"
        return self.sm

    def add_session(self):
        self.sm.add_session()

    def ask_delete_session(self, screen):
        self.sm.ask_delete_session(screen)

    def delete_session(self, session_name):
        self.sm.delete_session(session_name)

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)

    def start_app(self):
        self.dont_gc = None


if __name__ == "__main__":
    MobileColorimeterApp().run()
