from kivy.uix.screenmanager import Screen
from kivy.base import Builder

kv_str = """
<MainScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(5)
        Image:
            size_hint_y: 0.3
            source: "images/logo.png"
        InfoRstDocument:
            document_root: "./docs"
            source: "intro.rst"
            colors: {'background': '000000ff', 'link': 'ce5c00ff', 'paragraph': 'ffffffff', 'title': '204a87ff', 'bullet': '000000ff'}
        Button:
            size_hint_y: None
            height: dp(70)
            background_normal: 'images/blank.png'
            text: "Créer session d'analyse"
            font_size: '20sp'
            on_release: app.add_session()
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
                text: ">"
                on_release: app.sm.change_screen('right')
"""


Builder.load_string(kv_str)


class MainScreen(Screen):
    pass
