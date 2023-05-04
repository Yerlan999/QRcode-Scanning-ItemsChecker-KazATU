from io import BytesIO
from PIL import Image
import sqlite3
import io


byteImgIO = io.BytesIO()
byteImg = Image.open("img.jpg").resize((100, 100))
byteImg.save(byteImgIO, "JPEG")
byteImgIO.seek(0)
byteImg = byteImgIO.read()


connection = sqlite3.connect("test.db")
cursor = connection.cursor()


cursor.execute("CREATE TABLE images (inv_num INTEGER, image BLOB)")

for i in range(400):
    cursor.execute("INSERT INTO images VALUES (:id, :image)", {"image": byteImg, "id":i})
connection.commit()

# rows = cursor.execute("SELECT * FROM images").fetchall()
# dataBytesIO = io.BytesIO(rows[0][1])
# im = Image.open(dataBytesIO)
# im.save('result.jpg')
