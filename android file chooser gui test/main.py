from kivy.logger import Logger
import logging
Logger.setLevel(logging.DEBUG)

from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivymd.uix.label import MDLabel as Label
from kivymd.app import MDApp
from kivymd.uix.button.button import MDRectangleFlatButton
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from functools import partial
import pandas as pd
import os


from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android import api_version


BUTTON_TEXT_SIZE = 40



class FileChooserWidget(FileChooserIconView):
    excel_file_path = None
    def __init__(self, parent_screen, app, *args, **kwargs):
        super(FileChooserWidget, self).__init__(*args, **kwargs)
        self.parent_screen = parent_screen
        self.app = app
        self.path = self.app.user_media_dir
        self.rootpath = self.app.user_media_dir

    def on_selection(self, *args, **kwargs):
        print("On selection...Assign this path to somewhere")
        print("args: ", args[1][0])
        FileChooserWidget.excel_file_path = args[1][0]


class ChooseWindow(Screen):

    def __init__(self, app, *args, **kwargs):
        super(ChooseWindow, self).__init__(*args, **kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Укажите путь к excel файлу с оборудованием", halign='center', size_hint=(1.0, 0.1))

        self.home_button = MDRectangleFlatButton(text='Test', size_hint=(1.0, 0.1), font_size=BUTTON_TEXT_SIZE)
        self.home_button.bind(on_press = self.create_test_file)

        layout.add_widget(self.title)
        layout.add_widget(FileChooserWidget(self, self.app))
        layout.add_widget(self.home_button)


        self.add_widget(layout)

    def create_test_file(self, *args, **kwargs):
        empty_dict_with_cols = {"Наименование": [],
                                "Факультет": [],
                                "Кафедра": [],
                                "Инвентарный номер": [],
                                "Ответственный": [],
                                "Дата принятия": [],
                                "Кабинет": []
                                }
        self.app.excel_df = pd.DataFrame(empty_dict_with_cols)
        self.app.excel_df_path = os.path.join(self.app.user_media_dir, "Оборудование кафедры ЭЭО.xls") # TESTING !!!
        self.app.excel_df.to_excel(self.app.excel_df_path, index=False)
        print(FileChooserWidget.excel_file_path)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where


class ScreenManagement(ScreenManager):
    def __init__(self, *args, **kwargs):
        super(ScreenManagement, self).__init__(*args, **kwargs)



class Application(MDApp):

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        self.excel_created = False
        self.excel_choosen = False
        self.excel_to_create = False

        self.excel_df = None
        self.excel_df_path = None

        self.scan_with_delete = False
        self.scan_with_update = False
        self.scan_with_check = False

        self.current_item_QR = None
        self.current_item_inv_num = None

    def build(self):

        if platform == 'android':
            if api_version < 29: # Android 9 (API level 28) and below
                from android.storage import primary_external_storage_path
                self.user_media_dir = primary_external_storage_path() # only for Android < 10
            else: # Android 10 (API level 29) and greater
                from android.storage import primary_external_storage_path
                self.user_media_dir = primary_external_storage_path() # TEMPORARLY SOLUTION !!!

            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ])
        else:
            self.user_media_dir = self.user_data_dir

        self.theme_cls.theme_style = "Dark"

        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(ChooseWindow(self, name='choose page'))

        return sm




if __name__ == "__main__":
    application = Application()
    application.run()
