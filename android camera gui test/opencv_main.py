import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window

class OpenCVCamera(Image):
    def __init__(self, capture, **kwargs):
        super(OpenCVCamera, self).__init__(**kwargs)
        self.capture = capture

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.flip(frame, 0)  # Flip the image vertically
            buf = frame.tostring()
            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.texture = texture


class MainApp(App):
    def build(self):
        # Initialize the video capture device
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, Window.height)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, Window.width)

        # Create the layout for the app
        layout = BoxLayout(orientation='vertical')

        # Create the OpenCV camera widget
        self.camera = OpenCVCamera(capture=self.capture)
        layout.add_widget(self.camera)

        # Create the capture button
        self.capture_button = Button(text='Capture', size_hint=(1, 0.1))
        self.capture_button.bind(on_release=self.capture_frame)
        layout.add_widget(self.capture_button)

        # Schedule the camera update at 30 FPS
        Clock.schedule_interval(self.camera.update, 1.0 / 30.0)

        return layout

    def capture_frame(self, *args):
        # Capture the current frame
        ret, frame = self.capture.read()
        if ret:
            # Save the frame as an image
            cv2.imwrite('captured_frame.jpg', frame)
            print("Frame captured and saved as 'captured_frame.jpg'.")

    def on_stop(self):
        # Release the video capture device
        self.capture.release()


# Run the Kivy app
if __name__ == '__main__':
    MainApp().run()
