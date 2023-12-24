from kivy.lang import Builder
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Line, Color
from kivy.metrics import dp
from kivy.uix.popup import Popup
from applayout.toast import Toast
from camera4kivy import Preview
from PIL import Image


class CustomPreview(Preview):
    r = NumericProperty(0)
    g = NumericProperty(0)
    b = NumericProperty(0)
    analyse_w = NumericProperty(100)
    analyse_h = NumericProperty(100)
    sample = ListProperty([0, 0, 0])

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
        self.r = int(r / N)
        self.g = int(g / N)
        self.b = int(b / N)

    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        x, y = tex_pos
        w, h = tex_size
        Color(1, 1, 1, 1)
        Line(rectangle=(x + w / 2 - self.analyse_w / 2, y + h / 2 - self.analyse_h / 2, self.analyse_w,
                        self.analyse_h), width=dp(1))


class CapturePopup(Popup):
    sample = ListProperty([0, 0, 0])

    def on_open(self):
        self.ids.preview.connect_camera(camera_id='back', enable_video=False, enable_analyze_pixels=True)

    def on_dismiss(self):
        self.ids.preview.disconnect_camera()

    def sample_color(self, val: list):
        self.sample = val
        Toast().show("sampled: " + str(self.sample))
