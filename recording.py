import sys
import cv2
import pyautogui
import numpy as np
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel

class ScreenRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.recording = False
        self.video_writer = None

    def initUI(self):
        self.setWindowTitle("Screen Recorder")
        self.setGeometry(100, 100, 400, 200)

        self.label = QLabel("Click 'Start Recording' to begin", self)
        self.button_start = QPushButton("Start Recording", self)
        self.button_stop = QPushButton("Stop Recording", self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button_start)
        layout.addWidget(self.button_stop)
        self.setLayout(layout)

        self.button_start.clicked.connect(self.startRecording)
        self.button_stop.clicked.connect(self.stopRecording)

    def startRecording(self):
        if not self.recording:
            self.recording = True
            self.label.setText("Recording...")
            screen_size = pyautogui.size()
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter('recorded_video.mp4', fourcc, 20, screen_size)

            # Start screen recording in a separate thread
            self.recording_thread = threading.Thread(target=self.recordScreen)
            self.recording_thread.start()

    def stopRecording(self):
        if self.recording:
            self.recording = False
            self.label.setText("Recording stopped")
            self.video_writer.release()

    def recordScreen(self):
        while self.recording:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.video_writer.write(frame)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScreenRecorder()
    window.show()
    sys.exit(app.exec_())
