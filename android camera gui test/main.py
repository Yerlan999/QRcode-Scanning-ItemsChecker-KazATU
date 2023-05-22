from kivy.logger import Logger
import logging
Logger.setLevel(logging.DEBUG)

from kivy.app import App
from kivy.uix.camera import Camera
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission


class CamApp(App):

    def launch_camera(self, *args, **kwargs):
        if self.camera_obj.play:
            self.camera_obj.play = False
            self.button.text = "Start"
            self.camera_obj.texture = None
        else:
            self.camera_obj.play = True
            self.button.text = "Stop"


    def build(self):
        self.layout = BoxLayout(orientation="vertical")
        self.button = Button(text="Start", size_hint=(1, 0.1))
        self.button.bind(on_release=self.launch_camera)

        self.camera_obj = Camera()
        self.camera_obj.play = False
        self.layout.add_widget(self.camera_obj)
        self.layout.add_widget(self.button)

        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
            ])
        return self.layout

CamApp().run()
