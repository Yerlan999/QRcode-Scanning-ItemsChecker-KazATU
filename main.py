import os, re, sqlite3, io
from io import BytesIO
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics.texture import Texture
from kivy.uix.image import Image as kiImage
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.image import Image as CoreImage
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from functools import partial


from kivymd.app import MDApp
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.label import MDLabel as Label
from kivymd.uix.datatables import MDDataTable

import cv2
import numpy
import qrcode
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
# xlwt in needed for this version of pandas !!!


DEFAUL_IMAGE_SIZE = (300, 300)
DEFAUL_CAMERA_SIZE = (600, 600)


def convert_image_to_bytes(image):
    byteImgIO = io.BytesIO()
    byteImg = image.resize(DEFAUL_IMAGE_SIZE)
    byteImg.save(byteImgIO, "PNG")
    byteImgIO.seek(0)
    byteImg = byteImgIO.read()
    return byteImg


def convert_bytes_to_image(image_bytes):
    dataBytesIO = io.BytesIO(image_bytes)
    image = Image.open(dataBytesIO)
    return image


def create_db_table(root_directory):
    if not os.path.isdir(os.path.join(root_directory, "db")):
        os.mkdir(os.path.join(root_directory, "db"))
    connection = sqlite3.connect(os.path.join(os.path.join(root_directory, "db"), "images.db"))
    cursor = connection.cursor()
    cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='images' ''')
    if not cursor.fetchone()[0]==1:
        cursor.execute("CREATE TABLE images (inventory_number INTEGER, image_bytes BLOB)")
        connection.commit()
    cursor.close()
    if connection:
        connection.close()


def create_db_row(inventory_number, image_bytes, root_directory):
    connection = sqlite3.connect(os.path.join(os.path.join(root_directory, "db"), "images.db"))
    cursor = connection.cursor()
    cursor.execute("INSERT INTO images VALUES (:inventory_number, :image_bytes)", {"inventory_number":inventory_number, "image_bytes": image_bytes})
    connection.commit()
    cursor.close()
    if connection:
        connection.close()


def update_db_row(inventory_number, image_bytes, root_directory):
    connection = sqlite3.connect(os.path.join(os.path.join(root_directory, "db"), "images.db"))
    cursor = connection.cursor()
    cursor.execute(("UPDATE images SET image_bytes =:image_bytes WHERE inventory_number=:inventory_number"), {"inventory_number":inventory_number, "image_bytes": image_bytes})
    connection.commit()
    cursor.close()
    if connection:
        connection.close()


def delete_db_row(inventory_number, root_directory):
    connection = sqlite3.connect(os.path.join(os.path.join(root_directory, "db"), "images.db"))
    cursor = connection.cursor()
    cursor.execute(("DELETE FROM images WHERE inventory_number=:inventory_number"), {"inventory_number":inventory_number})
    connection.commit()
    cursor.close()
    if connection:
        connection.close()


def fetch_db_image(inventory_number, root_directory):
    image_bytes = None
    connection = sqlite3.connect(os.path.join(os.path.join(root_directory, "db"), "images.db"))
    cursor = connection.cursor()
    try:
        image_bytes = cursor.execute(("SELECT * FROM images WHERE inventory_number=:inventory_number"), {"inventory_number":inventory_number}).fetchall()[0][1]
    except:
        pass
    cursor.close()
    if connection:
        connection.close()
    return image_bytes


class SorterClass():

    def __init__(self):
        pass

    def populate_table(self, use_checks=True, checking_mode=False):

        if checking_mode: # Checking mode

            if not self.table_content:
                self.table_content = []
                for index, row in self.app.excel_df.iterrows():
                    row_content = []
                    for column_name in list(self.app.excel_df.columns):
                        try:
                            row_content.append(row[column_name].date())
                        except:
                            row_content.append(row[column_name])
                    supplemented_row = ["Нет"] + row_content
                    self.table_content.append(supplemented_row)

            self.column_headers = []
            for column_name in ["Наличие"] + list(self.app.excel_df.columns):
                if column_name == "Ответственный":
                    self.column_headers.append((column_name, dp(30), self.sort_on_responsible))
                elif column_name == "Кабинет":
                    self.column_headers.append((column_name, dp(30), self.sort_on_room))
                elif column_name == "Наименование":
                    self.column_headers.append((column_name, dp(30), self.sort_on_item_name))
                elif column_name == "Инвентарный номер":
                    self.column_headers.append((column_name, dp(30), self.sort_on_inventory_number))
                elif column_name == "Дата принятия":
                    self.column_headers.append((column_name, dp(30), self.sort_on_data_accepted))
                else:
                    self.column_headers.append((column_name, dp(30)))

        else: # Other modes

            self.table_content = []
            for index, row in self.app.excel_df.iterrows():
                row_content = []
                for column_name in list(self.app.excel_df.columns):
                    try:
                        row_content.append(row[column_name].date())
                    except:
                        row_content.append(row[column_name])
                self.table_content.append(row_content)

            self.column_headers = []
            for column_name in list(self.app.excel_df.columns):
                if column_name == "Ответственный":
                    self.column_headers.append((column_name, dp(30), self.sort_on_responsible))
                elif column_name == "Кабинет":
                    self.column_headers.append((column_name, dp(30), self.sort_on_room))
                elif column_name == "Наименование":
                    self.column_headers.append((column_name, dp(30), self.sort_on_item_name))
                elif column_name == "Инвентарный номер":
                    self.column_headers.append((column_name, dp(30), self.sort_on_inventory_number))
                elif column_name == "Дата принятия":
                    self.column_headers.append((column_name, dp(30), self.sort_on_data_accepted))
                else:
                    self.column_headers.append((column_name, dp(30)))

        self.data_tables = MDDataTable(
            check=use_checks,
            rows_num = len(self.app.excel_df),
            column_data= self.column_headers,
            row_data = self.table_content,
        )


    def sort_on_responsible(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][4]
            )
        )
    def sort_on_data_accepted(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][5]
            )
        )
    def sort_on_room(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][6]
            )
        )
    def sort_on_item_name(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][0]
            )
        )
    def sort_on_inventory_number(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][3]
            )
        )


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


    def selected(self, filename):
        try:
            self.ids.image.source = filename[0]
        except:
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



class CaptureWindow(Screen):

    def __init__(self, app, **kwargs):
        super(CaptureWindow, self).__init__(**kwargs)
        self.app = app

        create_db_table(self.app.user_data_dir)

        self.layout = BoxLayout(orientation='vertical')
        self.buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1.0, 0.1))

        self.title = Label(text="Сфотграфируйте оборудование", halign='center', size_hint=(1.0, 0.1))

        self.caputre_button = Button(text='Сфоткать')
        self.caputre_button.bind(on_press = self.capture_frame)

        self.later_button = Button(text='Потом')
        self.later_button.bind(on_press = self.postpone)

        self.buttons_layout.add_widget(self.caputre_button)
        self.buttons_layout.add_widget(self.later_button)

        self.layout.add_widget(self.title)

        self.add_widget(self.layout)

    def capture_frame(self, *args, **kwargs):
        self.camera_object.play = False
        texture = self.camera_object.texture
        size = texture.size
        pixels = texture.pixels
        pillow_image = Image.frombytes(mode='RGBA', size=size, data=pixels)

        image_bytes = convert_image_to_bytes(pillow_image)
        update_db_row(self.app.current_item_inv_num, image_bytes, self.app.user_data_dir)
        self.app.current_item_inv_num = None
        self.screen_transition("main page")

    def postpone(self, *args, **kwargs):
        self.camera_object.play = False
        self.camera_object.texture = None
        self.screen_transition("main page")

    def on_enter(self, *args, **kwargs):
        self.camera_object = Camera(play=True)
        self.camera_object.resolution = DEFAUL_CAMERA_SIZE

        self.layout.add_widget(self.camera_object)
        self.layout.add_widget(self.buttons_layout)


    def on_leave(self, *args, **kwargs):
        self.camera_object.play = False
        self.camera_object.texture = None
        self.layout.remove_widget(self.camera_object)
        self.layout.remove_widget(self.buttons_layout)

    def screen_transition(self, to_where, *args):
        self.manager.current = to_where


class ScanWindow(Screen):

    def __init__(self, app, *args, **kwargs):
        super(ScanWindow, self).__init__(*args, **kwargs)
        self.app = app

        self.layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Подведите камеру к QR коду для прочтения данных.", halign='center', size_hint=(1.0, 0.1))

        self.layout.add_widget(self.title)

        self.add_widget(self.layout)


    def on_enter(self, *args, **kwargs):
        self.camera_object = Camera(play=True)
        self.camera_object.resolution = DEFAUL_CAMERA_SIZE

        if self.app.scan_with_delete:
            self.title.text = "Подведите камеру к QR коду для удаления оборудования."
            self.home_button = Button(text='Назад', size_hint=(1.0, 0.1))
            self.home_button.bind(on_press = partial(self.screen_transition, "delete page"))
        elif self.app.scan_with_update:
            self.title.text = "Подведите камеру к QR коду для обновления оборудования."
            self.home_button = Button(text='Назад', size_hint=(1.0, 0.1))
            self.home_button.bind(on_press = partial(self.screen_transition, "update page"))
        elif self.app.scan_with_check:
            self.title.text = "Подведите камеру к QR коду для отметки оборудования."
            self.home_button = Button(text='Назад', size_hint=(1.0, 0.1))
            self.home_button.bind(on_press = partial(self.screen_transition, "check page"))
        else:
            self.home_button = Button(text='Назад', size_hint=(1.0, 0.1))
            self.home_button.bind(on_press = partial(self.screen_transition, "home page"))

        self.data = Label(text="", halign="center", valign="middle", size_hint=(1.0, 0.2))

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
        self.title.text = "Подведите камеру к QR коду для прочтения данных"
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
        if qr_code_value and len(qr_code_value.split("_")) > 1:
            item_name_entry, faculty_entry, department_entry, inventory_number_entry, responsible_entry, date_accepted_entry, room_entry = qr_code_value.split("_")
            self.app.current_item_QR = qr_code_value.split("_")

            indexes_found = None
            if (self.app.excel_choosen or self.app.excel_created) and self.app.excel_df_path:
                indexes_found = self.app.excel_df.index[self.app.excel_df[self.app.excel_df.columns[3]] == inventory_number_entry].tolist()

            if self.app.scan_with_delete and indexes_found:
                self.app.excel_df = self.app.excel_df.drop(indexes_found)
                delete_db_row(self.app.current_item_QR[3], self.app.user_data_dir)
                self.app.excel_df.to_excel(self.app.excel_df_path, index=False)
                self.app.scan_with_delete = False
                self.app.current_item_QR = None
                self.screen_transition("delete page")
            elif self.app.scan_with_update and indexes_found:
                self.screen_transition("add page")
            elif self.app.scan_with_check and indexes_found:
                self.screen_transition("check page")
            if (self.app.scan_with_update or self.app.scan_with_delete) and not indexes_found:
                qr_code_value = "Данного оборудования нет в excel файле!\n\n" + "Наименование: " + item_name_entry + "\nФакультет: " + faculty_entry + "\nКафедра: " + department_entry + "\nИнв. номер: " + inventory_number_entry + "\nОтветственный: " + responsible_entry + "\nДата принятия: " + date_accepted_entry + "\nКабинет: " + room_entry
            else:
                qr_code_value = "Наименование: " + item_name_entry + "\nФакультет: " + faculty_entry + "\nКафедра: " + department_entry + "\nИнв. номер: " + inventory_number_entry + "\nОтветственный: " + responsible_entry + "\nДата принятия: " + date_accepted_entry + "\nКабинет: " + room_entry
            self.data.text = qr_code_value

    def screen_transition(self, to_where, *args):
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where


class AddWindow(Screen):

    def __init__(self, app, *args, **kwargs):
        super(AddWindow, self).__init__(*args, **kwargs)
        self.app = app

        self.title = Label(text="Введите данные оборудования.", halign='center')

        self.header_layout = BoxLayout(orientation='horizontal')
        self.main_layout = BoxLayout(orientation="vertical")

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
        self.room_label = Label(text="Кабинет", halign="center");                        self.room_entry = TextInput()

        self.date_accepted_entry.bind(on_touch_down=self.show_date_picker)

        self.generate_button = Button(text='Сгенерировать QR код')
        self.generate_button.bind(on_press = self.show_QR_code)

        self.label_entiry_pair_layout1.add_widget(self.item_name_label); self.label_entiry_pair_layout1.add_widget(self.item_name_entry);
        self.label_entiry_pair_layout2.add_widget(self.faculty_label); self.label_entiry_pair_layout2.add_widget(self.faculty_entry);
        self.label_entiry_pair_layout3.add_widget(self.department_label); self.label_entiry_pair_layout3.add_widget(self.department_entry);
        self.label_entiry_pair_layout4.add_widget(self.inventory_number_label); self.label_entiry_pair_layout4.add_widget(self.inventory_number_entry);
        self.label_entiry_pair_layout5.add_widget(self.responsible_label); self.label_entiry_pair_layout5.add_widget(self.responsible_entry);
        self.label_entiry_pair_layout6.add_widget(self.date_accepted_label); self.label_entiry_pair_layout6.add_widget(self.date_accepted_entry);
        self.label_entiry_pair_layout7.add_widget(self.room_label); self.label_entiry_pair_layout7.add_widget(self.room_entry);

        self.main_layout.add_widget(self.header_layout)
        self.main_layout.add_widget(self.title)
        self.main_layout.add_widget(self.label_entiry_pair_layout1); self.main_layout.add_widget(self.label_entiry_pair_layout2);
        self.main_layout.add_widget(self.label_entiry_pair_layout3); self.main_layout.add_widget(self.label_entiry_pair_layout4);
        self.main_layout.add_widget(self.label_entiry_pair_layout5); self.main_layout.add_widget(self.label_entiry_pair_layout6);
        self.main_layout.add_widget(self.label_entiry_pair_layout7);
        self.main_layout.add_widget(self.generate_button)

        self.add_widget(self.main_layout)


    def on_touch_down(self, touch):
        if self.date_accepted_entry.collide_point(*touch.pos):
            date_dialog = MDDatePicker()
            date_dialog.bind(on_save=self.on_date_save)
            date_dialog.open()
        return super(AddWindow, self).on_touch_down(touch)

    def on_date_save(self, instance, value, date_range):
        self.date_accepted_entry.text = str(value)

    def show_date_picker(self, *args, **kwargs):
        pass

    def on_enter(self, *args, **kwargs):

        self.item_name_entry.text = ""
        self.faculty_entry.text = ""
        self.department_entry.text = ""
        self.inventory_number_entry.text = ""
        self.responsible_entry.text = ""
        self.date_accepted_entry.text = ""
        self.room_entry.text = ""

        self.back_button = Button(text='Назад')

        if self.app.scan_with_update and self.app.current_item_QR:
            self.title.text = "Обновите данные для оборудования"
            indexes_found = self.app.excel_df.index[self.app.excel_df[self.app.excel_df.columns[3]] == self.app.current_item_QR[3]].tolist()
            if indexes_found:
                item_name_entry, faculty_entry, department_entry, inventory_number_entry, responsible_entry, date_accepted_entry, room_entry = self.app.excel_df.loc[indexes_found[0],:]

                if hasattr(date_accepted_entry, 'date'):
                    self.date_accepted_entry.text = str(date_accepted_entry.date())
                else:
                    self.date_accepted_entry.text = date_accepted_entry
                self.item_name_entry.text = item_name_entry
                self.faculty_entry.text = faculty_entry
                self.department_entry.text = department_entry
                self.inventory_number_entry.text = inventory_number_entry
                self.responsible_entry.text = responsible_entry
                self.room_entry.text = room_entry

                self.generate_button.text = "Обновить и сгенерировать QR код"

                self.back_button.bind(on_press = partial(self.screen_transition, "update page"))
        else:
            self.generate_button.text = "Сгенерировать QR код"
            self.back_button.bind(on_press = partial(self.screen_transition, "main page"))

        self.header_layout.add_widget(self.back_button)
        self.header_layout.add_widget(self.about_button)


    def on_leave(self, *args, **kwargs):
        self.header_layout.remove_widget(self.back_button)
        self.header_layout.remove_widget(self.about_button)

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
        # self.app.excel_df = pd.read_excel(self.app.excel_df_path, dtype={"Инвентарный номер": str, "Кабинет": str})
        if not os.path.isdir(os.path.join(self.app.user_data_dir, "QR коды")):
            os.mkdir(os.path.join(self.app.user_data_dir, "QR коды"))

        qr_code_image_name = os.path.join(os.path.join(self.app.user_data_dir, "QR коды"), f"{self.inventory_number_entry.text}.png")
        self.QR_code_core_image.save(qr_code_image_name)

        found_indexes = self.app.excel_df.index[self.app.excel_df[self.app.excel_df.columns[3]] == self.inventory_number_entry.text].tolist()

        if self.app.scan_with_update and found_indexes:
            self.app.excel_df.loc[found_indexes,:] = [self.item_name_entry.text, self.faculty_entry.text, self.department_entry.text, self.inventory_number_entry.text, self.responsible_entry.text, self.date_accepted_entry.text, self.room_entry.text]
        else:
            self.app.excel_df.loc[len(self.app.excel_df),:] = [self.item_name_entry.text, self.faculty_entry.text, self.department_entry.text, self.inventory_number_entry.text, self.responsible_entry.text, self.date_accepted_entry.text, self.room_entry.text]
        self.app.excel_df.to_excel(self.app.excel_df_path, index=False)

        self.title.text = "QR код успешно сохранен"

        if self.app.scan_with_update:
            self.app.scan_with_update = False
            self.app.current_item_QR = None
            self.screen_transition("update page")
            return
        self.screen_transition("main page")


    def show_QR_code(self, *args):

        if not (self.item_name_entry.text and self.faculty_entry.text and self.department_entry.text and self.inventory_number_entry.text and self.responsible_entry.text and self.date_accepted_entry.text and self.room_entry.text):
            return
        item_name_entry = self.item_name_entry.text; faculty_entry = self.faculty_entry.text; department_entry = self.department_entry.text; inventory_number_entry = self.inventory_number_entry.text; responsible_entry = self.responsible_entry.text; date_accepted_entry = self.date_accepted_entry.text; room_entry = self.room_entry.text
        data_to_encode = item_name_entry + "_" + faculty_entry + "_" + department_entry + "_" + inventory_number_entry + "_" + responsible_entry + "_" + date_accepted_entry + "_" + room_entry

        # Создание временного изображения если нет
        current_image = fetch_db_image(inventory_number_entry, self.app.user_data_dir)
        if not current_image:
            temporal_image = Image.new('RGBA', DEFAUL_IMAGE_SIZE, color = (75, 110, 140))
            image_bytes = convert_image_to_bytes(temporal_image)
            create_db_row(inventory_number_entry, image_bytes, self.app.user_data_dir)

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
        self.capture_button = Button(text='Сфоткать'); self.capture_button.bind(on_press = partial(self.capture_frame, inventory_number_entry))

        self.footer_layout.add_widget(self.close_button)
        self.footer_layout.add_widget(self.save_button)
        self.footer_layout.add_widget(self.capture_button)

        self.popup_main_layout.add_widget(self.title)
        self.popup_main_layout.add_widget(self.QR_code_image)
        self.popup_main_layout.add_widget(self.footer_layout)

        self.popup = Popup(title='Ваш QR код', content=self.popup_main_layout, auto_dismiss=False)
        self.close_button.bind(on_press = self.popup.dismiss)

        self.popup.open()

    def capture_frame(self, inventory_number_entry, *args, **kwargs):
        self.popup.dismiss()
        self.app.current_item_inv_num = inventory_number_entry
        self.screen_transition("capture page")

    def screen_transition(self, to_where, *args):
        self.app.scan_with_update = False
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where


class ListWindow(Screen, SorterClass):

    def __init__(self, app, **kwargs):
        super(ListWindow, self).__init__(**kwargs)
        self.app = app

        self.main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Список оборудовании.", halign='center', size_hint=(1.0, 0.1))

        self.back_button = Button(text='Назад', size_hint=(1.0, 0.1))
        self.back_button.bind(on_press = partial(self.screen_transition, "main page"))

        self.main_layout.add_widget(self.title)

        self.add_widget(self.main_layout)

    def on_enter(self, *args, **kwargs):
        self.table_layout = AnchorLayout()

        self.populate_table(use_checks=False)
        self.data_tables.bind(on_row_press=self.on_row_press)

        self.table_layout.add_widget(self.data_tables)

        self.main_layout.add_widget(self.table_layout)
        self.main_layout.add_widget(self.back_button)

    def on_row_press(self, *args, **kwargs):
        temporal_row_values = self.table_content[int(args[1].index/len(self.column_headers))]

        self.app.current_item_inv_num = temporal_row_values[3]

        self.popup_main_layout = BoxLayout(orientation='vertical')
        self.popup_buttons_layout = BoxLayout(orientation='horizontal')

        self.title = Label(text=f"Наименование оборудования: {temporal_row_values[0]}.\nИнвентарный номер: {temporal_row_values[3]}", halign="center")

        image_bytes = fetch_db_image(temporal_row_values[3], self.app.user_data_dir)

        pillow_image = convert_bytes_to_image(image_bytes)
        if pillow_image:
            open_cv_image = numpy.array(pillow_image)
            open_cv_image = open_cv_image[:,:,:].copy()
            width, height, _ = open_cv_image.shape
            texture = Texture.create(size=(width, height))
            texture.blit_buffer(numpy.rot90(open_cv_image, 2).flatten(), colorfmt='rgba', bufferfmt='ubyte')
            image_widget = kiImage(size=(width, height), texture=texture)

        self.close_button = Button(text='Закрыть')
        self.select_image_button = Button(text='Указать')
        self.recapture_image_button = Button(text='Сфоткать')
        self.close_button.bind(on_press = self.close_popup)
        self.select_image_button.bind(on_press = self.select_image)
        self.recapture_image_button.bind(on_press = self.recapture_image)

        self.popup_main_layout.add_widget(self.title)
        self.popup_buttons_layout.add_widget(self.close_button)
        self.popup_buttons_layout.add_widget(self.select_image_button)
        self.popup_buttons_layout.add_widget(self.recapture_image_button)
        if pillow_image:
            self.popup_main_layout.add_widget(image_widget)
        self.popup_main_layout.add_widget(self.popup_buttons_layout)

        self.popup = Popup(title='Подробности оборудования', content=self.popup_main_layout, auto_dismiss=False)

        self.popup.open()

    def close_popup(self, *args, **kwargs):
        self.app.current_item_inv_num = None
        self.popup.dismiss()

    def select_image(self, *args, **kwargs):
        self.popup.dismiss()
        self.screen_transition("choose page")

    def recapture_image(self, *args, **kwargs):
        self.popup.dismiss()
        self.screen_transition("capture page")

    def on_leave(self, *args, **kwargs):
        self.main_layout.remove_widget(self.back_button)
        self.main_layout.remove_widget(self.table_layout)

    def screen_transition(self, to_where, *args):
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where



class CheckWindow(Screen, SorterClass):

    def __init__(self, app, **kwargs):
        super(CheckWindow, self).__init__(**kwargs)
        self.app = app

        self.table_content = []

        self.main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Инвентаризация оборудовании", halign='center', size_hint=(1.0, 0.1))

        self.check_by_QR_button = Button(text='Отметка по QR коду', size_hint=(1.0, 0.1))
        self.check_by_QR_button.bind(on_press = self.check_by_QR_code)

        self.add_widget(self.main_layout)

    def on_enter(self, *args, **kwargs):

        self.buttons_layout = BoxLayout(orientation="horizontal", size_hint=(1.0, 0.1))

        self.back_button = Button(text='Назад')
        self.back_button.bind(on_press = partial(self.screen_transition, "main page"))

        self.finish_button = Button(text='Сохранить и завершить')
        self.finish_button.bind(on_press = self.finish_checking)

        # After scaning by QR code
        if self.app.current_item_QR:
            this_row = None; current_symbol = None;
            for i, row in enumerate(self.table_content):
                if str(row[4]) == str(self.app.current_item_QR[3]):
                    this_row = i
                    current_symbol = row[0]
            temporal_row_values = self.table_content[this_row]
            if current_symbol == "Нет":
                temporal_row_values[0] =  "Да"
            else:
                temporal_row_values[0] =  "Нет"

            self.data_tables.update_row(self.data_tables.row_data[this_row], temporal_row_values)
            self.app.current_item_QR = None

        self.table_layout = AnchorLayout()

        self.populate_table(use_checks=False, checking_mode=True)

        self.data_tables.bind(on_row_press=self.on_row_press)

        self.table_layout.add_widget(self.data_tables)

        self.main_layout.add_widget(self.title)
        self.main_layout.add_widget(self.check_by_QR_button)
        self.buttons_layout.add_widget(self.back_button)
        self.buttons_layout.add_widget(self.finish_button)
        self.main_layout.add_widget(self.table_layout)
        self.main_layout.add_widget(self.buttons_layout)

    def finish_checking(self, *args, **kwargs):
        check_df = pd.DataFrame(self.table_content, columns=["Наличие"] + list(self.app.excel_df.columns))
        check_df.to_excel(os.path.join(self.app.user_data_dir, "Инвентаризация "+str(datetime.today().date())+".xls"), index=False)

    def on_row_press(self, *args, **kwargs):
        temporal_row_values = self.table_content[int(args[1].index/len(self.column_headers))]
        if temporal_row_values[0] == "Нет":
            temporal_row_values[0] = "Да"
        else:
            temporal_row_values[0] = "Нет"
        self.data_tables.update_row(self.data_tables.row_data[int(args[1].index/len(self.column_headers))], temporal_row_values)

    def on_leave(self, *args, **kwargs):
        self.main_layout.remove_widget(self.title)
        self.main_layout.remove_widget(self.check_by_QR_button)
        self.main_layout.remove_widget(self.buttons_layout)
        self.main_layout.remove_widget(self.table_layout)

    def check_by_QR_code(self, *args, **kwargs):
        self.app.scan_with_check = True
        self.screen_transition("test scan page")

    def screen_transition(self, to_where, *args):
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where



class DeleteWindow(Screen, SorterClass):

    def __init__(self, app, **kwargs):
        super(DeleteWindow, self).__init__(**kwargs)
        self.app = app

        self.main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Удаление оборудовании", halign='center', size_hint=(1.0, 0.1))

        self.delete_by_QR_button = Button(text='Удалить по QR коду', size_hint=(1.0, 0.1))
        self.delete_by_QR_button.bind(on_press = self.delete_by_QR_code)

        self.back_button = Button(text='Назад')
        self.back_button.bind(on_press = partial(self.screen_transition, "main page"))

        self.delete_button = Button(text='Удалить')
        self.delete_button.bind(on_press = self.delete_checked_rows)

        self.add_widget(self.main_layout)

    def on_enter(self, *args, **kwargs):

        self.buttons_layout = BoxLayout(orientation="horizontal", size_hint=(1.0, 0.1))
        self.table_layout = AnchorLayout()

        self.populate_table(use_checks=True)

        self.table_layout.add_widget(self.data_tables)
        self.buttons_layout.add_widget(self.back_button)
        self.buttons_layout.add_widget(self.delete_button)
        self.main_layout.add_widget(self.title)
        self.main_layout.add_widget(self.delete_by_QR_button)
        self.main_layout.add_widget(self.table_layout)
        self.main_layout.add_widget(self.buttons_layout)

    # !!! NEEDED TO BE CORRECTED SLIGHTLY !!!
    def delete_checked_rows(self, *args):

        def deselect_rows(*args):
            self.data_tables.table_data.select_all("normal")

        row_index = None
        for data in self.data_tables.get_row_checks():
            counter = 0
            for row in self.data_tables.row_data:
                if str(row[3]) == str(data[3]):
                    row_index = counter
                counter += 1
            try:
                self.data_tables.remove_row(self.data_tables.row_data[row_index])
                self.app.excel_df = self.app.excel_df.drop(self.app.excel_df.index[self.app.excel_df[self.column_headers[3][0]] == data[3]].tolist())
                delete_db_row(self.data_tables.row_data[row_index][3], self.app.user_data_dir)
            except Exception as error:
                print("Something went wrong: ", error)

        self.app.excel_df.to_excel(self.app.excel_df_path, index=False)
        Clock.schedule_once(deselect_rows)

    def delete_by_QR_code(self, *args, **kwargs):
        self.app.scan_with_delete = True
        self.screen_transition("test scan page")

    def on_leave(self, *args, **kwargs):
        self.buttons_layout.remove_widget(self.back_button)
        self.buttons_layout.remove_widget(self.delete_button)
        self.main_layout.remove_widget(self.delete_by_QR_button)
        self.main_layout.remove_widget(self.title)
        self.main_layout.remove_widget(self.table_layout)
        self.main_layout.remove_widget(self.buttons_layout)

    def screen_transition(self, to_where, *args):
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where


class UpdateWindow(Screen, SorterClass):

    def __init__(self, app, **kwargs):
        super(UpdateWindow, self).__init__(**kwargs)
        self.app = app

        self.main_layout = BoxLayout(orientation='vertical')

        self.title = Label(text="Перемещение/Обновление оборудовании", halign='center', size_hint=(1.0, 0.1))

        self.update_by_QR_button = Button(text='Обновить/Переместить по QR коду', size_hint=(1.0, 0.1))
        self.update_by_QR_button.bind(on_press = self.update_by_QR_code)

        self.back_button = Button(text='Назад', size_hint=(1.0, 0.1))
        self.back_button.bind(on_press = partial(self.screen_transition, "main page"))

        self.add_widget(self.main_layout)

    def on_enter(self, *args, **kwargs):

        self.table_layout = AnchorLayout()

        self.populate_table(use_checks=False)

        self.data_tables.bind(on_row_press=self.on_row_press)

        self.table_layout.add_widget(self.data_tables)

        self.main_layout.add_widget(self.title)
        self.main_layout.add_widget(self.update_by_QR_button)
        self.main_layout.add_widget(self.table_layout)
        self.main_layout.add_widget(self.back_button)

    def on_row_press(self, *args, **kwargs):
        self.app.current_item_QR = self.table_content[int(args[1].index/len(self.app.excel_df.columns))]
        self.app.scan_with_update = True
        self.screen_transition("add page")

    def update_by_QR_code(self, *args, **kwargs):
        self.app.scan_with_update = True
        self.screen_transition("test scan page")

    def on_leave(self, *args, **kwargs):
        self.main_layout.remove_widget(self.title)
        self.main_layout.remove_widget(self.update_by_QR_button)
        self.main_layout.remove_widget(self.back_button)
        self.main_layout.remove_widget(self.table_layout)

    def screen_transition(self, to_where, *args):
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where


class MainWindow(Screen):

    def __init__(self, app, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.app = app

        self.header_layout = BoxLayout(orientation='horizontal', spacing=10)
        self.main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

        self.home_button = Button(text='Домой')
        self.home_button.bind(on_press = partial(self.screen_transition, "home page"))
        self.about_button = Button(text='Инструкция')
        self.about_button.bind(on_press = self.call_about_page)

        self.add_button = Button(text='Добавить оборудование')
        self.add_button.bind(on_press = partial(self.screen_transition, "add page"))

        self.update_button = Button(text='Переместить/Обновить оборудование')
        self.update_button.bind(on_press = partial(self.screen_transition, "update page"))

        self.check_button = Button(text='Провести инвентаризацию')
        self.check_button.bind(on_press = partial(self.screen_transition, "check page"))

        self.delete_button = Button(text='Удалить оборудование')
        self.delete_button.bind(on_press = partial(self.screen_transition, "delete page"))

        self.look_up_button = Button(text='Просмотр списка оборудовании')
        self.look_up_button.bind(on_press = partial(self.screen_transition, "list page"))

        self.header_layout.add_widget(self.home_button)
        self.header_layout.add_widget(self.about_button)

        self.main_layout.add_widget(self.header_layout)
        self.main_layout.add_widget(self.add_button)
        self.main_layout.add_widget(self.update_button)
        self.main_layout.add_widget(self.check_button)
        self.main_layout.add_widget(self.delete_button)
        self.main_layout.add_widget(self.look_up_button)

        self.add_widget(self.main_layout)

    def on_enter(self, *args, **kwargs):
        if self.app.excel_to_create and not self.app.excel_created and not self.app.excel_choosen:
            self.app.excel_df = pd.DataFrame(columns=["Наименование", "Факультет", "Кафедра", "Инвентарный номер", "Ответственный", "Дата принятия", "Кабинет"])
            self.app.excel_df_path = os.path.join(self.app.user_data_dir, "Оборудование кафедры ЭЭО.xls")
            self.app.excel_df.to_excel(self.app.excel_df_path, index=False)
            self.app.excel_created = True
            self.app.excel_choosen = False
            self.app.excel_to_create = False


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
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where


class StartUpWindow(Screen):

        def __init__(self, app, **kwargs):
            super(StartUpWindow, self).__init__(**kwargs)
            self.app = app

            primary_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
            secondary_layout = BoxLayout(orientation='horizontal', spacing=10)

            self.title = Label(text="Помощник лаборанта", halign='center')
            self.hint = Label(text="Пожалуйста, выберете файл-список оборудовании (excel) или создайте его заново", halign='center')

            self.choose_button = Button(text='Выбрать')
            self.choose_button.bind(on_press = partial(self.screen_transition, "choose page"))

            self.create_button = Button(text='Создать')
            self.create_button.bind(on_press = self.create_new_excel_file)

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

        def create_new_excel_file(self, *args, **kwargs):
            self.app.excel_to_create = True
            self.app.excel_choosen = False
            self.app.excel_created = False
            self.screen_transition("main page")

        def screen_transition(self, to_where, *args):
            if to_where in ["main page", "home page"]:
                self.app.current_item_QR = None
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
        if to_where in ["main page", "home page"]:
            self.app.current_item_QR = None
        self.manager.current = to_where


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
        self.theme_cls.theme_style = "Dark"

        sm = ScreenManagement(transition=FadeTransition())
        sm.add_widget(StartUpWindow(self, name='home page'))
        sm.add_widget(ChooseWindow(self, name='choose page'))
        sm.add_widget(MainWindow(self, name='main page'))
        sm.add_widget(AddWindow(self, name='add page'))
        sm.add_widget(ListWindow(self, name='list page'))
        sm.add_widget(DeleteWindow(self, name='delete page'))
        sm.add_widget(UpdateWindow(self, name='update page'))
        sm.add_widget(CheckWindow(self, name='check page'))
        sm.add_widget(ScanWindow(self, name='test scan page'))
        sm.add_widget(CaptureWindow(self, name='capture page'))
        sm.add_widget(AboutWindow(name='about page'))
        return sm




if __name__ == "__main__":
    application = Application()
    application.run()
