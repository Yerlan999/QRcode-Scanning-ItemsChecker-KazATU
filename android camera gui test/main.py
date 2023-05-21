# Uncomment these lines to see all the messages
from kivy.logger import Logger
import logging
Logger.setLevel(logging.TRACE)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
import time

from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission


Builder.load_string('''
<CameraClick>:
    orientation: 'vertical'
    Camera:
        id: camera
        play: False
    ToggleButton:
        text: 'Play'
        on_press: camera.play = not camera.play
        size_hint_y: None
        height: '48dp'
    Button:
        text: 'Capture'
        size_hint_y: None
        height: '48dp'
        on_press: root.capture()
''')


class CameraClick(BoxLayout):
    def capture(self):
        camera = self.ids['camera']
        timestr = time.strftime("%Y%m%d_%H%M%S")
        camera.export_to_png("IMG_{}.png".format(timestr))
        print("Captured")


class TestCamera(App):

    def build(self):

        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
            ])

        return CameraClick()


TestCamera().run()
