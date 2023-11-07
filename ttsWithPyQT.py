from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QVBoxLayout, QMessageBox
from gtts import gTTS
import pygame
import os
import sys

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.textbox = QLineEdit(self)
        layout.addWidget(self.textbox)

        btn = QPushButton('Speak', self)
        btn.clicked.connect(self.speak)
        layout.addWidget(btn)

        self.setLayout(layout)
        self.setWindowTitle('gTTS with PyQt')
        self.show()


    def speak(self):
        try:
            text = self.textbox.text()
            tts = gTTS(text=text, lang='ko')
            file_path = "temp_audio.mp3"
            tts.save(file_path)

            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
            os.remove(file_path)
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(f"An error occured : {e}")
            msg.setWindowTitle("Error")
            msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
