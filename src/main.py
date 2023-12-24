from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from android_permissions import AndroidPermissions
from screens.mainscreen import MainScreen
from screens.analysisscreen import AnalysisScreen
from kivy.logger import Logger


__version__ = "0.2"


class MyScreenManager(ScreenManager):

    def change_screen(self, direction):
        Logger.info(f"Ui: Moving \"{direction}\"")
        self.transition.direction = direction
        if direction == 'right':
            cur = self.screen_names.index(self.current)
            self.current = self.screen_names[(cur - 1) % len(self.screen_names)]
        if direction == 'left':
            cur = self.screen_names.index(self.current)
            self.current = self.screen_names[(cur + 1) % len(self.screen_names)]

    def add_session(self):
        session_screen_name = 'analysisscreen' + str(len(self.screen_names) - 1)
        Logger.info(f"Session: Adding \"{session_screen_name}\"")
        self.add_widget(AnalysisScreen(name=session_screen_name))
        self.transition.direction = 'up'
        self.current = session_screen_name
        Logger.info(f"Session: Updated screens list {self.screen_names!s}")

    def find_screen(self, screen_name):
        for screen in self.screens:
            if screen.name == screen_name:
                return screen

    def delete_session(self, name):
        Logger.info(f"Session: Deleting \"{name}\"")
        cur = self.screen_names.index(name)
        self.transition.direction = 'down'
        scr = self.find_screen(name)
        self.remove_widget(scr)
        Logger.info(f"Session: Updated screens list {self.screen_names!s}")
        self.current = self.screen_names[(cur - 1) % len(self.screen_names)]


class MobileColorimeterApp(App):

    def build(self):
        self.sm = MyScreenManager()
        self.sm.add_widget(MainScreen(name='mainscreen'))
        self.sm.current = "mainscreen"
        return self.sm

    def add_session(self):
        self.sm.add_session()

    def delete_session(self, session_name):
        self.sm.delete_session(session_name)

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)

    def start_app(self):
        self.dont_gc = None


if __name__ == "__main__":
    MobileColorimeterApp().run()
