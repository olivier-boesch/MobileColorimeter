"""
Custom popup for the project
"""
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, BooleanProperty, StringProperty
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

kv_str: str = """
<ConfirmPopup@Popup>:
    title: 'Confirmer ?'
    message: ''
    ok_callbkack: None
    callback_data: None
    size_hint: 0.8, None
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
                
<MessagePopup>:
    title: 'Information'
    size_hint: 0.8, None
    height: dp(150)
    Label:
        text: root.message

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
                text: "V:" + str(preview.g)
            ColorLabel:
                id: bluelabel
                backcolor: 0,0,1,1
                color: 1,1,1,1
                text: "B:" + str(preview.b)
            ColorLabel:
                text: "Moyenne"
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
    size_hint: 0.8, None
    height: dp(200)
    BoxLayout:
        orientation: "vertical"
        Label:
            text: "Concentration (mol/L)"
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
    size_hint: 0.8, None
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
    """
    Custom preview
    Class for data analysis of image colors
    """
    r = NumericProperty(0)
    g = NumericProperty(0)
    b = NumericProperty(0)
    analyse_w = NumericProperty(100)
    analyse_h = NumericProperty(100)
    sample = ListProperty([0, 0, 0])
    analyze_on = BooleanProperty(False)

    def analyze_pixels_callback(self, pixels: bytes, image_size: tuple[int, int], image_pos: tuple[int, int],
                                image_scale: float, mirror: bool):
        """
        Custom callback for image analysis of a rectangle (analyse_w x analyse_h)
        computes the mean color of this rectangle
        :param pixels: image pixels in rgba format
        :param image_size: tuple (width, height) of the image
        :param image_pos: position of the image
        :param image_scale: scale of the image
        :param mirror: is the image mirrored ?
        :return: None
        """
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
    def set_rgb_values(self, mean_color: tuple[int, int, int]):
        """
        sets the r,g and b values in the main thread (where kivy's loop is running)
        :param mean_color: tuple (r,g,b) of the mean color
        """
        self.r = int(mean_color[0])
        self.g = int(mean_color[1])
        self.b = int(mean_color[2])

    def canvas_instructions_callback(self, texture: "Texture", tex_size: tuple[int, int], tex_pos: tuple[int, int]):
        x, y = tex_pos
        w, h = tex_size
        Color(1, 1, 1, 1)
        Line(rectangle=(x + w / 2 - self.analyse_w / 2, y + h / 2 - self.analyse_h / 2, self.analyse_w,
                        self.analyse_h), width=dp(1))


class FloatInput(TextInput):
    """
    A float only input widget
    """
    pat = re.compile('[^0-9]')

    def insert_text(self, substring: str, from_undo: bool = False):
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
    """
    Displays the result of the evaluation for a concentration
    """
    absorbance_value = NumericProperty(0.0)
    concentration_value = NumericProperty(0.0)


class ConcentrationPopup(Popup):
    """
    asks for a concentration value
    """
    callback_method = ObjectProperty(None)

    def on_open(self):
        if self.callback_method is not None:
            self.callback_method(None)
        self.ids.concentration.text = "0.0"
        self.ids.concentration.focus = True

    def on_cancel(self):
        self.dismiss()

    def on_ok(self):
        """
        Called when the ok button is pressed
        """
        if self.callback_method is not None:
            self.callback_method(float(self.ids.concentration.text))
        self.dismiss()


class CapturePopup(Popup):
    """
    captures the image for analysing (the analysis is made in realtime)
    """
    title = "Capture"
    sample = ListProperty([0, 0, 0])
    callback_method = ObjectProperty(None)
    concentration = NumericProperty(0.0, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_open(self):
        """
        Called when the popup is about to be opened
        """
        self.ids['preview'].connect_camera(camera_id='back',
                                           enable_video=False,
                                           enable_analyze_pixels=True, mirror=False)
        self.ids.preview.analyze_on = True

    def on_dismiss(self):
        """
        Called when the popup is about to be closed
        """
        self.ids.preview.analyze_on = False
        self.ids['preview'].disconnect_camera()

    def sample_color(self, val: tuple[int, int, int]):
        """
        Called when the sample button is pressed
        :param val: sampled color (tuple of r,g, and b values)
        """
        self.sample = val
        Logger.info(f"Sampled Color: {val}")
        if self.callback_method is not None:
            self.callback_method(self.concentration, self.sample)
            self.dismiss()


class MessagePopup(Popup):
    """
    Simple message popup which dismisses itself
    """
    message = StringProperty('')
    auto_close = BooleanProperty(True)
    auto_close_delay = NumericProperty(2)

    def on_open(self):
        """
        Called when the popup is about to be opened
        """
        if self.auto_close:
            Clock.schedule_once(lambda dt: self.dismiss(), self.auto_close_delay)