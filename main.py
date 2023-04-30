import os
import re
from io import BytesIO
from kivy.app import App
from kivy import platform
from kivy.metrics import dp
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.popup import Popup
# from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.setupconfig import USE_SDL2
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as kiImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.image import Image as CoreImage
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, OptionProperty
from functools import partial

from kivymd.uix.label import MDLabel as Label
from kivymd.uix.datatables import MDDataTable

import cv2
import numpy
import qrcode
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


COLUMNS_NAME = ["Наименование", "Факультет", "Кафедра", "Инвентарный номер", "Ответственный", "Дата принятия", "Кабинет"]

class IntegerInput(TextInput):

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



Builder.load_string("""
<FileChooserWidget>:
    id: file_chooser
    Button
        text: "Выбрать"
        on_release: file_chooser.open(filechooser.path, filechooser.selection)
        size_hint: 1.0, 0.1
        pos_hint: {'right': 1, 'top': 1}
    FileChooserListView:
        id: filechooser
        on_selection: file_chooser.selected(filechooser.selection)
""")


class FileChooserWidget(BoxLayout):

    def __init__(self, parent_screen, app, *args, **kwargs):
        super(FileChooserWidget, self).__init__(*args, **kwargs)
        self.parent_screen = parent_screen
        self.app = app

    def open(self, path, filename):
        if (filename) and os.path.splitext(filename[0])[1] in [".xlsx", ".xls"]:
            excel_df = pd.read_excel(filename[0])
            self.excel_df = excel_df
            setattr(self.app, "excel_df", excel_df)
            setattr(self.app, "excel_df_path", filename[0])
            self.parent_screen.screen_transition("main page")


    def selected(self, filename):
        pass


class ChooseWindow(Screen):

    def __init__(self, app, *args, **kwargs):
        super(ChooseWindow, self).__init__(*args, **kwargs)

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Укажите путь к excel файлу с оборудованием", halign='center', size_hint=(1.0, 0.1))

        self.home_button = Button(text='Домой', size_hint=(1.0, 0.1))
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        layout.add_widget(self.title)
        layout.add_widget(FileChooserWidget(self, app))
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

        self.title = Label(text="Подведите камеру к QR коду для прочтения данных.", halign='center', size_hint=(1.0, 0.1))

        self.layout.add_widget(self.title)

        self.add_widget(self.layout)


    def on_enter(self, *args, **kwargs):
        self.camera_object = Camera(play=True)
        self.camera_object.resolution = (600, 600)

        self.data = Label(text="", halign="center", valign="middle", size_hint=(1.0, 0.2))

        self.home_button = Button(text='Назад', size_hint=(1.0, 0.1))
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
            item_name_entry, faculty_entry, department_entry, inventory_number_entry, responsible_entry, date_accepted_entry, room_entry = qr_code_value.split("$")
            qr_code_value = "Наименование: " + item_name_entry + "\nФакультет: " + faculty_entry + "\nКафедра: " + department_entry + "\nИнв. номер: " + inventory_number_entry + "\nОтветственный: " + responsible_entry + "\nДата принятия: " + date_accepted_entry + "\nКабинет: " + room_entry
            self.data.text = qr_code_value

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where



class AddWindow(Screen):

    def __init__(self, app, *args, **kwargs):
        super(AddWindow, self).__init__(*args, **kwargs)
        self.app = app

        self.title = Label(text="Введите данные оборудования.", halign='center')

        self.header_layout = BoxLayout(orientation='horizontal')
        self.main_layout = BoxLayout(orientation="vertical")

        self.back_button = Button(text='Назад')
        self.back_button.bind(on_press = partial(self.screen_transition, "main page"))
        self.about_button = Button(text='Инструкция')
        self.about_button.bind(on_press = self.call_about_page)

        self.label_entiry_pair_layout1 = BoxLayout(orientation='horizontal')
        self.label_entiry_pair_layout2 = BoxLayout(orientation='horizontal')
        self.label_entiry_pair_layout3 = BoxLayout(orientation='horizontal')
        self.label_entiry_pair_layout4 = BoxLayout(orientation='horizontal')
        self.label_entiry_pair_layout5 = BoxLayout(orientation='horizontal')
        self.label_entiry_pair_layout6 = BoxLayout(orientation='horizontal')
        self.label_entiry_pair_layout7 = BoxLayout(orientation='horizontal')

        self.item_name_label = Label(text="Наименование оборудования", halign="center"); self.item_name_entry = TextInput()
        self.faculty_label = Label(text="Факультет", halign="center");                   self.faculty_entry = TextInput()
        self.department_label = Label(text="Кафедра", halign="center");                  self.department_entry = TextInput()
        self.inventory_number_label = Label(text="Инвентарный номер", halign="center");  self.inventory_number_entry = IntegerInput()
        self.responsible_label = Label(text="Ответственный", halign="center");           self.responsible_entry = TextInput()
        self.date_accepted_label = Label(text="Дата принятия", halign="center");         self.date_accepted_entry = TextInput()
        self.room_label = Label(text="Кабинет", halign="center");                        self.room_entry = IntegerInput()


        self.generate_button = Button(text='Сгенерировать QR код')
        self.generate_button.bind(on_press = self.show_QR_code)

        self.label_entiry_pair_layout1.add_widget(self.item_name_label); self.label_entiry_pair_layout1.add_widget(self.item_name_entry);
        self.label_entiry_pair_layout2.add_widget(self.faculty_label); self.label_entiry_pair_layout2.add_widget(self.faculty_entry);
        self.label_entiry_pair_layout3.add_widget(self.department_label); self.label_entiry_pair_layout3.add_widget(self.department_entry);
        self.label_entiry_pair_layout4.add_widget(self.inventory_number_label); self.label_entiry_pair_layout4.add_widget(self.inventory_number_entry);
        self.label_entiry_pair_layout5.add_widget(self.responsible_label); self.label_entiry_pair_layout5.add_widget(self.responsible_entry);
        self.label_entiry_pair_layout6.add_widget(self.date_accepted_label); self.label_entiry_pair_layout6.add_widget(self.date_accepted_entry);
        self.label_entiry_pair_layout7.add_widget(self.room_label); self.label_entiry_pair_layout7.add_widget(self.room_entry);

        self.header_layout.add_widget(self.back_button)
        self.header_layout.add_widget(self.about_button)

        self.main_layout.add_widget(self.header_layout)
        self.main_layout.add_widget(self.title)
        self.main_layout.add_widget(self.label_entiry_pair_layout1); self.main_layout.add_widget(self.label_entiry_pair_layout2);
        self.main_layout.add_widget(self.label_entiry_pair_layout3); self.main_layout.add_widget(self.label_entiry_pair_layout4);
        self.main_layout.add_widget(self.label_entiry_pair_layout5); self.main_layout.add_widget(self.label_entiry_pair_layout6);
        self.main_layout.add_widget(self.label_entiry_pair_layout7);
        self.main_layout.add_widget(self.generate_button)


        self.add_widget(self.main_layout)


    def call_about_page(self, *args, **kwargs):
        popup_main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Как пользоваться данной программой.", halign="center")
        self.body = Label(text="<Тут более подробно расписывается инструкция по применению данной программы>.", halign="center")

        self.close_button = Button(text='Закрыть')

        popup_main_layout.add_widget(self.title)
        popup_main_layout.add_widget(self.body)
        popup_main_layout.add_widget(self.close_button)

        popup = Popup(title='Инструкция', content=popup_main_layout, auto_dismiss=False)
        self.close_button.bind(on_press = popup.dismiss)

        popup.open()

    def save_QR_code(self, *args):
        if not os.path.isdir(os.path.join(self.app.user_data_dir, "QR коды")):
            os.mkdir(os.path.join(self.app.user_data_dir, "QR коды"))
        qr_code_image_name = os.path.join(os.path.join(self.app.user_data_dir, "QR коды"), f"{self.inventory_number_entry.text}.png")
        self.QR_code_core_image.save(qr_code_image_name)

    def share_QR_code(self, *args):
        if platform == 'android':
            from jnius import cast
            from jnius import autoclass
            if USE_SDL2:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
            else:
                PythonActivity = autoclass('org.renpy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            String = autoclass('java.lang.String')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')

            shareIntent = Intent(Intent.ACTION_SEND)
            shareIntent.setType('"image/*"')
            imageFile = self.QR_code_core_image
            uri = Uri.fromFile(imageFile)

            parcelable = cast('android.os.Parcelable', uri)
            shareIntent.putExtra(Intent.EXTRA_STREAM, parcelable)

            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(shareIntent)

    def show_QR_code(self, *args):

        item_name_entry = self.item_name_entry.text; faculty_entry = self.faculty_entry.text; department_entry = self.department_entry.text; inventory_number_entry = self.inventory_number_entry.text; responsible_entry = self.responsible_entry.text; date_accepted_entry = self.date_accepted_entry.text; room_entry = self.room_entry.text
        data_to_encode = item_name_entry + "_" + faculty_entry + "_" + department_entry + "_" + inventory_number_entry + "_" + responsible_entry + "_" + date_accepted_entry + "_" + room_entry

        qr = qrcode.QRCode(version = 1, box_size = 10, border = 5)
        qr.add_data(data_to_encode)
        qr.make(fit = True)
        QR_code_pillow_image = qr.make_image(fill_color = 'black', back_color = 'white')

        data = BytesIO()
        QR_code_pillow_image.save(data, format='png')
        data.seek(0)
        image = CoreImage(BytesIO(data.read()), ext='png')
        self.QR_code_core_image = image
        self.QR_code_image = kiImage()
        self.QR_code_image.texture = image.texture


        self.popup_main_layout = BoxLayout(orientation='vertical')
        self.footer_layout = BoxLayout(orientation='horizontal')

        self.title = Label(text="Получен QR код для оборудования", halign="center")

        self.close_button = Button(text='Закрыть')
        self.save_button = Button(text='Сохранить'); self.save_button.bind(on_press = self.save_QR_code)
        self.export_button = Button(text='Экспортировать'); self.export_button.bind(on_press = self.share_QR_code)

        self.footer_layout.add_widget(self.close_button)
        self.footer_layout.add_widget(self.save_button)
        self.footer_layout.add_widget(self.export_button)

        self.popup_main_layout.add_widget(self.title)
        self.popup_main_layout.add_widget(self.QR_code_image)
        self.popup_main_layout.add_widget(self.footer_layout)

        popup = Popup(title='Ваш QR код', content=self.popup_main_layout, auto_dismiss=False)
        self.close_button.bind(on_press = popup.dismiss)

        popup.open()

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where


class ListWindow(Screen):

    def __init__(self, app, **kwargs):
        super(ListWindow, self).__init__(**kwargs)
        self.app = app

        self.main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Список оборудовании.", halign='center', size_hint=(1.0, 0.1))

        self.back_button = Button(text='Назад', size_hint=(1.0, 0.1))
        self.back_button.bind(on_press = partial(self.screen_transition, "main page"))

        self.add_widget(self.main_layout)

    def on_enter(self, *args, **kwargs):
        self.table_layout = AnchorLayout()

        table_content = [[row["Наименование"], row["Факультет"], row["Кафедра"], row["Инвентарный номер"], row["Ответственный"], row["Дата принятия"], row["Кабинет"]] for index, row in self.app.excel_df.iterrows()]

        self.data_tables = MDDataTable(
            use_pagination=True,
            check=True,

            column_data=[
                ("Наименование оборудования", dp(30), None, "Custom tooltip"),
                ("Факультет", dp(30)),
                ("Кафедра", dp(60)),
                ("Инвентарный номер", dp(30)),
                ("Ответственный", dp(30)),
                ("Дата принятия", dp(30),),
                ("Кабинет", dp(30)),
            ],
            row_data = table_content,
        )
        self.table_layout.add_widget(self.data_tables)

        self.main_layout.add_widget(self.title)
        self.main_layout.add_widget(self.table_layout)
        self.main_layout.add_widget(self.back_button)

    def on_leave(self, *args, **kwargs):
        self.main_layout.remove_widget(self.title)
        self.main_layout.remove_widget(self.back_button)
        self.main_layout.remove_widget(self.table_layout)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where



class MainWindow(Screen):

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

        self.header_layout = BoxLayout(orientation='horizontal', spacing=10)
        self.footer_layout = BoxLayout(orientation='horizontal', spacing=10)
        self.main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

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

        self.title = Label(text="Как пользоваться данной программой.", halign="center")
        self.body = Label(text="<Тут более подробно расписывается инструкция по применению данной программы>.", halign="center")

        self.close_button = Button(text='Закрыть')

        popup_main_layout.add_widget(self.title)
        popup_main_layout.add_widget(self.body)
        popup_main_layout.add_widget(self.close_button)

        popup = Popup(title='Инструкция', content=popup_main_layout, auto_dismiss=False)
        self.close_button.bind(on_press = popup.dismiss)

        popup.open()

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where


class StartUpWindow(Screen):

        def __init__(self, **kwargs):
            super(StartUpWindow, self).__init__(**kwargs)

            primary_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
            secondary_layout = BoxLayout(orientation='horizontal', spacing=10)

            self.title = Label(text="Помощник лаборанта", halign='center')
            self.hint = Label(text="Пожалуйста, выберете файл-список оборудовании (excel) или создайте его заново", halign='center')

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


class AboutWindow(Screen):

    def __init__(self, **kwargs):
        super(AboutWindow, self).__init__(**kwargs)

        layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Как пользоваться данной программой.", halign='center', size_hint=(1.0, 0.1))
        self.body = Label(text="<Тут более подробно расписывается инструкция по применению данной программы>.", halign='center', size_hint=(1.0, 0.8))
        self.home_button = Button(text='Домой', size_hint=(1.0, 0.1))
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        layout.add_widget(self.title)
        layout.add_widget(self.body)
        layout.add_widget(self.home_button)


        self.add_widget(layout)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where


class Application(MDApp):

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.excel_df = None
        self.excel_df_path = None

    def build(self):
        self.theme_cls.theme_style = "Dark"

        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(StartUpWindow(name='home page'))
        sm.add_widget(ChooseWindow(self, name='choose page'))
        sm.add_widget(MainWindow(name='main page'))
        sm.add_widget(AddWindow(self, name='add page'))
        sm.add_widget(ListWindow(self, name='list page'))
        sm.add_widget(ScanWindow(name='test scan page'))
        sm.add_widget(AboutWindow(name='about page'))
        return sm


if __name__ == "__main__":
    application = Application()
    application.run()

# ["Наименование", "Факультет", "Инвентарный номер", "Ответственный", "Дата принятия", "Кабинет"]
