from io import BytesIO
from PIL import Image
import sqlite3
import io, os


user_data_dir = r"C:\Users\Пользователь\AppData\Roaming\application"
DEFAUL_IMAGE_SIZE = (100, 100)

def convert_image_to_bytes(image):
    byteImgIO = io.BytesIO()
    byteImg = image.resize(DEFAUL_IMAGE_SIZE)
    byteImg.save(byteImgIO, "JPEG")
    byteImgIO.seek(0)
    byteImg = byteImgIO.read()
    return byteImg


def convert_bytes_to_image(image_bytes):
    dataBytesIO = io.BytesIO(image_bytes)
    image = Image.open(dataBytesIO)
    return image


def create_db_table():
    try:
        if not os.path.isdir(os.path.join(user_data_dir, "db")):
            os.mkdir(os.path.join(user_data_dir, "db"))
        connection = sqlite3.connect(os.path.join(os.path.join(user_data_dir, "db"), "images.db"))
        cursor = connection.cursor()
        cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='images' ''')
        if not cursor.fetchone()[0]==1:
            cursor.execute("CREATE TABLE images (inventory_number INTEGER, image_bytes BLOB)")
            connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка:", error)
    finally:
        if connection:
            connection.close()


def create_db_row(inventory_number, image_bytes):
    try:
        connection = sqlite3.connect(os.path.join(os.path.join(user_data_dir, "db"), "images.db"))
        cursor = connection.cursor()
        cursor.execute("INSERT INTO images VALUES (:inventory_number, :image_bytes)", {"inventory_number":inventory_number, "image_bytes": image_bytes})
        connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка:", error)
    finally:
        if connection:
            connection.close()


def update_db_row(inventory_number, image_bytes):
    try:
        connection = sqlite3.connect(os.path.join(os.path.join(user_data_dir, "db"), "images.db"))
        cursor = connection.cursor()
        cursor.execute(("UPDATE images SET image_bytes =:image_bytes WHERE inventory_number=:inventory_number"), {"inventory_number":inventory_number, "image_bytes": image_bytes})
        connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка:", error)
    finally:
        if connection:
            connection.close()


def delete_db_row(inventory_number):
    try:
        connection = sqlite3.connect(os.path.join(os.path.join(user_data_dir, "db"), "images.db"))
        cursor = connection.cursor()
        cursor.execute(("DELETE FROM images WHERE inventory_number=:inventory_number"), {"inventory_number":inventory_number})
        connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка:", error)
    finally:
        if connection:
            connection.close()


def fetch_db_row(inventory_number):
    try:
        connection = sqlite3.connect(os.path.join(os.path.join(user_data_dir, "db"), "images.db"))
        cursor = connection.cursor()
        if inventory_number == -1:
            rows = cursor.execute("SELECT * FROM images").fetchall()
        rows = cursor.execute(("SELECT * FROM images WHERE inventory_number=:inventory_number"), {"inventory_number":inventory_number}).fetchall()
        connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка:", error)
    finally:
        if connection:
            connection.close()
    return rows



if __name__ == '__main__':
    create_db_table()

    image_bytes = convert_image_to_bytes(Image.open("img.jpg"))

    create_db_row(0, image_bytes)
    create_db_row(1, image_bytes)
    create_db_row(2, image_bytes)

    update_db_row(2, image_bytes)

    delete_db_row(1)

    rows = fetch_db_row(0)

    # print(rows)
