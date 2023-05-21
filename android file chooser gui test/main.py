from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
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
    from android import mActivity, autoclass, api_version
    from androidstorage4kivy import SharedStorage, Chooser
    from android_permissions import AndroidPermissions


BUTTON_TEXT_SIZE = 40


Builder.load_string("""
<FileChooserWidget>:
    id: file_chooser
    MDRectangleFlatButton
        text: "Выбрать"
        on_release: file_chooser.open(filechooser.path, filechooser.selection)
        size_hint: 1.0, 0.1
        pos_hint: {'right': 1, 'top': 1}
    FileChooserIconView:
        id: filechooser
        path: root.get_default_path()
        on_selection: file_chooser.selected(filechooser.selection)
""")


class FileChooserWidget(BoxLayout):

    def __init__(self, parent_screen, app, *args, **kwargs):
        super(FileChooserWidget, self).__init__(*args, **kwargs)
        self.parent_screen = parent_screen
        self.app = app

    def open(self, path, filename):
        if (filename) and os.path.splitext(filename[0])[1] in [".xlsx", ".xls"]:
            excel_df = pd.read_excel(filename[0], dtype={"Инвентарный номер": str, "Кабинет": str})
            self.app.excel_choosen = True
            self.app.excel_created = False
            self.app.excel_to_create = False
            self.app.excel_df = excel_df
            self.app.excel_df_path = filename[0]
            self.parent_screen.screen_transition("main page")
        elif (filename) and os.path.splitext(filename[0])[1] in [".jpg", ".jpeg", ".png"] and self.app.current_item_inv_num:
            pillow_image = Image.open(filename[0])
            image_bytes = convert_image_to_bytes(pillow_image)
            update_db_row(self.app.current_item_inv_num, image_bytes, self.app.user_data_dir)
            self.app.current_item_inv_num = None
            self.parent_screen.screen_transition("main page")

    def get_default_path(self):
        if platform == 'android':
            self.path = self.app.user_media_dir
        else:
            self.path = os.path.expanduser("~/Desktop")
        return self.path


    def selected(self, filename):
        print("ENVOKED")
        try:
            self.ids.image.source = filename[0]
        except:
            pass



class ChooseWindow(Screen):

    def __init__(self, app, *args, **kwargs):
        super(ChooseWindow, self).__init__(*args, **kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Укажите путь к excel файлу с оборудованием", halign='center', size_hint=(1.0, 0.1))

        self.home_button = MDRectangleFlatButton(text='Test', size_hint=(1.0, 0.1), font_size=BUTTON_TEXT_SIZE)
        self.home_button.bind(on_press = self.create_test_file)

        layout.add_widget(self.title)
        layout.add_widget(FileChooserWidget(self, app))
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
        self.app.excel_df_path = os.path.join(self.app.user_media_dir, "test.xls") # TESTING !!!
        self.app.excel_df.to_excel(self.app.excel_df_path, index=False)

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
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.MANAGE_EXTERNAL_STORAGE
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
