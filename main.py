import os
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from functools import partial

import cv2
import numpy
import pandas as pd
from PIL import Image


Builder.load_string("""
<FileChooserWidget>:
    id: file_chooser
    Button
        text: "Выбрать"
        on_release: file_chooser.open(filechooser.path, filechooser.selection)
    FileChooserListView:
        id: filechooser
        on_selection: file_chooser.selected(filechooser.selection)
""")


class FileChooserWidget(BoxLayout):

    def __init__(self, parent_screen, *args, **kwargs):
        super(FileChooserWidget, self).__init__(*args, **kwargs)
        self.parent_screen = parent_screen

    def open(self, path, filename):
        # Check if selected file .xlsx file and open with pandas

        file_name, file_extension = os.path.splitext(filename[0])
        if (file_extension in [".xlsx", ".xls"]):
            excel_df = pd.read_excel(filename[0])
            self.excel_df = excel_df
            print(excel_df)
        print()

        # Read selected file and save it
        # After reading and saving, transit to the the "main page"
        self.parent_screen.screen_transition("main page")


    def selected(self, filename):
        pass


class ChooseWindow(Screen):

    def __init__(self, *args, **kwargs):
        super(ChooseWindow, self).__init__(*args, **kwargs)

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Укажите путь к excel файлу с оборудованием")

        self.home_button = Button(text='Домой')
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        layout.add_widget(self.title)
        layout.add_widget(FileChooserWidget(self))
        layout.add_widget(self.home_button)


        self.add_widget(layout)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where



class ScreenManagement(ScreenManager):
    def __init__(self, *args, **kwargs):
        super(ScreenManagement, self).__init__(*args, **kwargs)


class ScanWindow(Screen):

    def __init__(self, *args, **kwargs):
        super(ScanWindow, self).__init__(*args, **kwargs)

        self.layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Подведите камеру к QR коду для прочтения данных.")

        self.layout.add_widget(self.title)

        self.add_widget(self.layout)


    def on_enter(self, *args, **kwargs):
        self.camera_object = Camera(play=True)
        self.camera_object.resolution = (600, 600)

        self.data = Label(text="")

        self.home_button = Button(text='Назад')
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        self.layout.add_widget(self.camera_object)
        self.layout.add_widget(self.data)
        self.layout.add_widget(self.home_button)

        self.scan_clock = Clock.schedule_interval(self.scan_for_QR_code, 1)

    def on_leave(self, *args, **kwargs):
        self.camera_object.play = False
        self.camera_object.texture = None
        self.layout.remove_widget(self.camera_object)
        self.layout.remove_widget(self.home_button)
        self.layout.remove_widget(self.data)
        self.scan_clock.cancel()

    def read_QR_code(self, image, *args, **kwargs):
        try:
            detect = cv2.QRCodeDetector()
            value, points, straight_qrcode = detect.detectAndDecode(image)
            return value
        except Exception as error:
            print("Error with reading image!", error)

    def camera_frame_to_image(self, camera_object, *args, **kwargs):
        texture = camera_object.texture
        size = texture.size
        pixels = texture.pixels
        pillow_image = Image.frombytes(mode='RGBA', size=size, data=pixels)
        image = numpy.array(pillow_image)
        return image

    def scan_for_QR_code(self, *args):
        image = self.camera_frame_to_image(self.camera_object)
        qr_code_value = self.read_QR_code(image)
        if qr_code_value:
            self.data.text = qr_code_value
        # self.camera_object.export_to_png('./selfie.png')

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where



class AboutWindow(Screen):

    def __init__(self, **kwargs):
        super(AboutWindow, self).__init__(**kwargs)

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Как пользоваться данной программой.")
        self.body = Label(text="<Тут более подробно расписывается инструкция по применению данной программы>.") #!!! Text wrapping issue !!!

        self.home_button = Button(text='Домой')
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        layout.add_widget(self.title)
        layout.add_widget(self.body)
        layout.add_widget(self.home_button)


        self.add_widget(layout)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where



class MainWindow(Screen):

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

        self.header_layout = BoxLayout(orientation='horizontal')
        self.footer_layout = BoxLayout(orientation='horizontal')
        self.main_layout = BoxLayout(orientation='vertical')

        self.home_button = Button(text='Домой')
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))
        self.about_button = Button(text='Инструкция')
        self.about_button.bind(on_press = self.call_about_page)

        self.add_button = Button(text='Добавить оборудование')
        self.add_button.bind(on_press = partial(self.screen_transition, "add page"))

        self.update_button = Button(text='Переместить/Обновить оборудование')
        self.update_button.bind(on_press = partial(self.screen_transition, "list page"))

        self.check_button = Button(text='Провести инвентаризацию')
        self.check_button.bind(on_press = partial(self.screen_transition, "list page"))

        self.delete_button = Button(text='Удалить оборудование')
        self.delete_button.bind(on_press = partial(self.screen_transition, "list page"))

        self.look_up_button = Button(text='Просмотр списка оборудовании')
        self.look_up_button.bind(on_press = partial(self.screen_transition, "list page"))

        self.save_button = Button(text='Сохранить')
        self.save_button.bind(on_press = partial(self.screen_transition, " page"))
        self.export_button = Button(text='Экспорт')
        self.export_button.bind(on_press = partial(self.screen_transition, " page"))


        self.header_layout.add_widget(self.home_button)
        self.header_layout.add_widget(self.about_button)
        self.footer_layout.add_widget(self.save_button)
        self.footer_layout.add_widget(self.export_button)

        self.main_layout.add_widget(self.header_layout)
        self.main_layout.add_widget(self.add_button)
        self.main_layout.add_widget(self.update_button)
        self.main_layout.add_widget(self.check_button)
        self.main_layout.add_widget(self.delete_button)
        self.main_layout.add_widget(self.look_up_button)
        self.main_layout.add_widget(self.footer_layout)


        self.add_widget(self.main_layout)


    def call_about_page(self, *args, **kwargs):
        popup_main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Как пользоваться данной программой.")
        self.body = Label(text="<Тут более подробно расписывается инструкция по применению данной программы>.") #!!! Text wrapping issue !!!

        self.close_button = Button(text='Закрыть')

        popup_main_layout.add_widget(self.title)
        popup_main_layout.add_widget(self.body)
        popup_main_layout.add_widget(self.close_button)

        popup = Popup(title='Как пользоваться данной программой', content=popup_main_layout, auto_dismiss=False)
        self.close_button.bind(on_press = popup.dismiss)

        popup.open()

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where


class StartUpWindow(Screen):

        def __init__(self, **kwargs):
            super(StartUpWindow, self).__init__(**kwargs)

            primary_layout = BoxLayout(orientation='vertical')
            secondary_layout = BoxLayout(orientation='horizontal')

            self.title = Label(text="Помощник лаборанта")
            self.hint = Label(text="Пожалуйста, выберете файл-список оборудовании (excel) или создайте его заново")

            self.choose_button = Button(text='Выбрать')
            self.choose_button.bind(on_press = partial(self.screen_transition, "choose page"))

            self.create_button = Button(text='Создать')
            self.create_button.bind(on_press = partial(self.screen_transition, "main page"))

            self.check_button = Button(text='Проверочное сканирование')
            self.check_button.bind(on_press = partial(self.screen_transition, "test scan page"))

            self.about_button = Button(text='О программе')
            self.about_button.bind(on_press = partial(self.screen_transition, "about page"))

            self.exit_button = Button(text='Выход')
            self.exit_button.bind(on_release=App.get_running_app().stop)

            secondary_layout.add_widget(self.choose_button)
            secondary_layout.add_widget(self.create_button)

            primary_layout.add_widget(self.title)
            primary_layout.add_widget(self.hint)
            primary_layout.add_widget(secondary_layout)
            primary_layout.add_widget(self.check_button)
            primary_layout.add_widget(self.about_button)
            primary_layout.add_widget(self.exit_button)

            self.add_widget(primary_layout)


        def screen_transition(self, to_where, *args):
            self.manager.current = to_where


class Application(App):
    def build(self):
        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(StartUpWindow(name='home page'))
        sm.add_widget(ChooseWindow(name='choose page'))
        sm.add_widget(MainWindow(name='main page'))
        sm.add_widget(ScanWindow(name='test scan page'))
        sm.add_widget(AboutWindow(name='about page'))
        return sm


if __name__ == "__main__":
    application = Application()
    application.run()
