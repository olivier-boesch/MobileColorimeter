from kivy.properties import NumericProperty, ListProperty, ObjectProperty, BooleanProperty
from kivy.graphics import Line, Color
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.base import Builder
from camera4kivy import Preview
from kivy.logger import Logger
from kivy.clock import mainthread, Clock
from kivy.uix.textinput import TextInput
import re
from PIL import Image

kv_str = """


<CapturePopup>:
    auto_dismiss: False
    size_hint: 0.9, 0.9
    BoxLayout:
        orientation: "vertical"
        CustomPreview:
            id: preview
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 0.2
            padding: dp(10)
            spacing: dp(10)
            Button:
                text: 'Annuler'
                on_release: root.dismiss()
            ColorLabel:
                id: redlabel
                backcolor: 1,0,0,1
                color: 0,0,0,1
                text: "R:" + str(preview.r)
            ColorLabel:
                id: greenlabel
                backcolor: 0,1,0,1
                color: 0,0,0,1
                text: "G:" + str(preview.g)
            ColorLabel:
                id: bluelabel
                backcolor: 0,0,1,1
                color: 1,1,1,1
                text: "B:" + str(preview.b)
            ColorLabel:
                text: "Mean"
                backcolor: preview.r/255, preview.g/255, preview.b/255, 1
                color: 0,0,0,1
            Button:
                text: "Ok"
                on_release: root.sample_color((preview.r, preview.g, preview.b))

<ColorLabel@Label>
    backcolor: 1,1,1,1

    canvas.before:
        Color:
            rgba: self.backcolor
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0,0,0,1
            
<ConcentrationPopup>
    title: "Concentration (mol/L)"
    auto_dismiss: False
    size_hint: 0.5, None
    height: dp(200)
    BoxLayout:
        orientation: "vertical"
        Label:
            text: "Entrez la concentration en mol/L de l'échantillon"
        BoxLayout:
            padding: dp(10)
            spacing: dp(5)
            orientation: "horizontal"
            size_hint_y: None
            height: self.minimum_height
            FloatInput:
                size_hint_y: None
                height: self.minimum_height
                multiline: False
                id: concentration
                text: '0.0'
                on_text_validate: root.on_ok()
            Label:
                size_hint_y: None
                height: concentration.minimum_height
                size_hint_x: 0.2
                text: "mol/L"
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(50)
            Button:
                text: 'Annuler'
                on_release: root.on_cancel()
            Button:
                text: 'Ok'
                on_release: root.on_ok()
                
<EvalConcentrationPopup>:
    title: 'Concentration calculée'
    auto_dismiss: False
    size_hint: 0.5, None
    height: dp(150)
    BoxLayout:
        orientation: "vertical"
        Label:
            id: concentration
            text: f"A = {root.absorbance_value:0.3f}; C = {root.concentration_value:.2e} mol/L"
        Button:
            text: 'Ok'
            on_release: root.dismiss()
"""


Builder.load_string(kv_str)


class CustomPreview(Preview):
    r = NumericProperty(0)
    g = NumericProperty(0)
    b = NumericProperty(0)
    analyse_w = NumericProperty(100)
    analyse_h = NumericProperty(100)
    sample = ListProperty([0, 0, 0])
    analyze_on = BooleanProperty(False)

    def analyze_pixels_callback(self, pixels, image_size, image_pos,
                                image_scale, mirror):
        pil_image = Image.frombytes(mode='RGBA', size=image_size,
                                    data=pixels)
        w, h = image_size
        img = pil_image.crop((w / 2 - self.analyse_w / 2, h / 2 - self.analyse_h / 2, w / 2 + self.analyse_w / 2,
                              h / 2 + self.analyse_h / 2))
        r = 0
        g = 0
        b = 0
        N = img.size[0] * img.size[1]
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                ri, gi, bi, _ = img.getpixel((i, j))
                r += ri
                g += gi
                b += bi
        self.set_rgb_values((r/N, g/N, b/N))

    @mainthread
    def set_rgb_values(self, mean_color):
        self.r = int(mean_color[0])
        self.g = int(mean_color[1])
        self.b = int(mean_color[2])

    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        x, y = tex_pos
        w, h = tex_size
        Color(1, 1, 1, 1)
        Line(rectangle=(x + w / 2 - self.analyse_w / 2, y + h / 2 - self.analyse_h / 2, self.analyse_w,
                        self.analyse_h), width=dp(1))


class FloatInput(TextInput):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join(
                re.sub(pat, '', s)
                for s in substring.split('.', 1)
            )
        return super().insert_text(s, from_undo=from_undo)


class EvalConcentrationPopup(Popup):
    absorbance_value = NumericProperty(0.0)
    concentration_value = NumericProperty(0.0)


class ConcentrationPopup(Popup):
    callback_method = ObjectProperty(None)

    def on_open(self):
        if self.callback_method is not None:
            self.callback_method(None)
        self.ids.concentration.text = "0.0"
        self.ids.concentration.focus = True

    def on_cancel(self):
        self.dismiss()

    def on_ok(self):
        if self.callback_method is not None:
            self.callback_method(float(self.ids.concentration.text))
        self.dismiss()


class CapturePopup(Popup):
    title = "Capture"
    sample = ListProperty([0, 0, 0])
    callback_method = ObjectProperty(None)
    concentration = NumericProperty(0.0, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_open(self):
        self.ids['preview'].connect_camera(camera_id='back',
                                           enable_video=False,
                                           enable_analyze_pixels=True, mirror=False)
        self.ids.preview.analyze_on = True

    def on_dismiss(self):
        self.ids.preview.analyze_on = False
        self.ids['preview'].disconnect_camera()

    def sample_color(self, val: list):
        self.sample = val
        Logger.info(f"Sampled Color: {val}")
        if self.callback_method is not None:
            Clock.schedule_once(lambda dt: self.callback_method(self.concentration, self.sample), 0.1)
            self.dismiss()
