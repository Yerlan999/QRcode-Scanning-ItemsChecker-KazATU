from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy_garden.zbarcam import ZBarCam


from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission


class QrScanner(BoxLayout):
    def __init__(self, **kwargs):
        super(QrScanner, self).__init__(**kwargs)
        btn1 = Button(text='Scan Me',  font_size="50sp")
        btn1.bind(on_press=self.callback)
        self.add_widget(btn1)

    def callback(self, instance):
        """On click button, initiate zbarcam and schedule text reader"""
        self.remove_widget(instance) # remove button
        self.zbarcam = ZBarCam()
        self.add_widget(self.zbarcam)
        Clock.schedule_interval(self.read_qr_text, 1)

    def read_qr_text(self, *args):
        """Check if zbarcam.symbols is filled and stop scanning in such case"""
        if(len(self.zbarcam.symbols) > 0): # when something is detected
            self.qr_text = self.zbarcam.symbols[0].data # text from QR
            print(self.qr_text.decode('utf-8'))
            Clock.unschedule(self.read_qr_text, 1)
            self.zbarcam.stop() # stop zbarcam
            print(dir(self.zbarcam.ids['xcamera']._camera))
            self.zbarcam.ids['xcamera']._camera._device.release() # release camera !!! ERROR no ._device attribute




class QrApp(App):
    def build(self):

        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
            ])

        return QrScanner()

if __name__ == '__main__':
    QrApp().run()
