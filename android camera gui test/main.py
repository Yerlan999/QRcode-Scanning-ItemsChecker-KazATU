from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy_garden.zbarcam import ZBarCam

from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission


class QrScanner(BoxLayout):
    def __init__(self, **kwargs):
        super(QrScanner, self).__init__(**kwargs)
        self.orientation = "vertical"

        self.scan_button = Button(text='Scan Me',  font_size="50sp")
        self.scan_button.bind(on_press=self.scan_QR_code)
        self.add_widget(self.scan_button)

        self.capture_button = Button(text='Capture Me',  font_size="50sp")
        self.capture_button.bind(on_press=self.capture_image)
        self.add_widget(self.capture_button)

    def scan_QR_code(self, instance):
        """On click button, initiate zbarcam and schedule text reader"""
        self.remove_widget(self.capture_button) # remove button
        self.remove_widget(self.scan_button) # remove button
        self.scan_label = Label(text="Scan QR code", size_hint=(1, 0.1))

        self.zbarcam = ZBarCam()

        self.add_widget(self.scan_label)
        self.add_widget(self.zbarcam)
        Clock.schedule_interval(self.read_QR_code, 1)

    def capture_image(self, instance):
        """On click button, initiate zbarcam and schedule text reader"""
        self.remove_widget(self.capture_button) # remove button
        self.remove_widget(self.scan_button) # remove button
        self.capture_label = Label(text="Scan QR code", size_hint=(1, 0.1))

        self.zbarcam = ZBarCam()
        self.capture_btn = Button(text="Capture", size_hint=(1, 0.1))
        self.capture_btn.bind(on_press=self.capture)

        self.add_widget(self.capture_label)
        self.add_widget(self.zbarcam)
        self.add_widget(self.capture_btn)

    def read_QR_code(self, *args):
        """Check if zbarcam.symbols is filled and stop scanning in such case"""
        if(len(self.zbarcam.symbols) > 0): # when something is detected
            self.qr_text = self.zbarcam.symbols[0].data.decode('utf-8') # text from QR
            print(self.qr_text)
            Clock.unschedule(self.read_QR_code, 1)
            self.zbarcam.stop()
            if platform == 'android': self.zbarcam.ids['xcamera']._camera._android_camera.release()
            else: self.zbarcam.ids['xcamera']._camera._device.release()

    def capture(self, *args, **kwargs):
        image_bytes = self.zbarcam.xcamera.texture.pixels


class QrApp(App):
    def build(self):

        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
            ])

        return QrScanner()

if __name__ == '__main__':
    QrApp().run()
