import time
from functools import partial

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Rectangle, Color
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission

class ScreenManagement(ScreenManager):
    def __init__(self, *args, **kwargs):
        super(ScreenManagement, self).__init__(*args, **kwargs)


class StartUpWindow(Screen):

    def __init__(self, app, **kwargs):
        super(StartUpWindow, self).__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Home page", halign='center', size_hint=(1.0, 0.1))
        self.camera_button = Button(text='Start camera', size_hint=(1.0, 0.1), font_size=20)
        self.camera_button.bind(on_press = partial(self.screen_transition, "camera page"))

        layout.add_widget(self.title)
        layout.add_widget(self.camera_button)

        self.add_widget(layout)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where



class CameraWindow(Screen):

    def __init__(self, app, **kwargs):
        super(CameraWindow, self).__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical')
        buttons_layout = BoxLayout(orientation='horizontal')

        self.title = Label(text="Here is the camera", halign='center', size_hint=(1.0, 0.1))
        self.home_button = Button(text='to Home', size_hint=(1.0, 0.1), font_size=20)
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        self.toggle_camera_button = Button(text='Start camera', size_hint=(1.0, 0.1), font_size=20)
        self.toggle_camera_button.bind(on_press = self.toggle_camera)

        self.camera = Camera(play=False, resolution=(Window.width, Window.height))

        with self.camera.canvas:
            print("Canvas")
        with self.camera.canvas.before:
            PushMatrix()
            Rotate(angle=-90, origin=Window.center)
            print("Canvas before")
        with self.camera.canvas.after:
            PopMatrix()
            print("Canvas after")

        layout.add_widget(self.title)
        layout.add_widget(self.camera)
        buttons_layout.add_widget(self.home_button)
        buttons_layout.add_widget(self.toggle_camera_button)

        self.add_widget(layout)
        self.add_widget(buttons_layout)


    def toggle_camera(self, *args, **kwargs):
        self.camera.play = not self.camera.play
        self.toggle_camera_button.text = "Stop camera" if self.camera.play else "Start camera"

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where




class Application(App):

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)


    def build(self):

        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(StartUpWindow(self, name='home page'))
        sm.add_widget(CameraWindow(self, name='camera page'))
        return sm




if __name__ == "__main__":
    application = Application()
    application.run()
