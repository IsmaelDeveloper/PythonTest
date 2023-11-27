import os
import sys
import socketio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QLabel, QStackedLayout, QSizePolicy
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import asyncio
import subprocess
import threading
from answerer import Answerer
from offerer import Offerer
import cv2
sio = socketio.Client()


class SocketIOThread(QThread):
    users_updated = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        sio.on('update_users', self.on_update_users)
        sio.wait()

    def on_update_users(self, data):
        self.users_updated.emit(data)


class CallReceiver(QWidget):
    def __init__(self):
        super().__init__()
        self.answerer = Answerer()

        self.initUI()
        self.setupAnswerer()

    def initUI(self):

        sio.connect('http://127.0.0.1:6969')
        sio.emit('register', {'username': os.getenv(
            "USERNAME", "default_user")})
        self.setWindowTitle("Incoming Call")
        self.setGeometry(300, 300, 800, 600)
        self.layout = QVBoxLayout(self)

        # Configurer videoLabel pour utiliser l'espace disponible
        self.videoLabel = QLabel()
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.videoLabel)

        # Ajouter le bouton Hangup
        self.hangupButton = QPushButton("Hangup")
        self.hangupButton.clicked.connect(self.hangupCall)
        self.layout.addWidget(self.hangupButton)

    async def connect_socketio(self):
        await self.sio.connect('http://127.0.0.1:6969')
        await self.sio.emit('register', {'username': self.username})
        self.sio.on('update_users', self.on_update_users)

    def setupAnswerer(self):
        self.answerer.offer_received.connect(self.on_offer_received)
        self.answerer.video_frame_received.connect(self.updateVideoFrame)
        self.answerer_thread = threading.Thread(
            target=self.run_answerer, daemon=True)
        self.answerer_thread.start()

    def updateVideoFrame(self, frame):
        print("Update video frame")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qImg = QImage(
            frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0], QImage.Format_RGB888)
        self.videoLabel.setPixmap(QPixmap.fromImage(qImg).scaled(
            self.videoLabel.width(), self.videoLabel.height(), Qt.KeepAspectRatio))

    def hangupCall(self):
        print("Hangup call")
        self.answerer.end_call()
        self.close()

    def on_offer_received(self):
        reply = QMessageBox.question(
            self, 'Call incoming', "Do you wanna accept the call ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answer_call(True)
            self.showFullScreen()
            self.show()
        else:
            self.answer_call(False)

    def answer_call(self, accept):
        if accept:
            asyncio.run_coroutine_threadsafe(
                self.answerer.handle_offer(), asyncio.get_event_loop())

    def run_answerer(self):
        asyncio.run(self.answerer.start())


class UserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupSocketThread()
        self.process_offerer = None
        self.callReceiver = CallReceiver()

    def initUI(self):
        self.setWindowTitle("User List")
        self.setGeometry(100, 100, 800, 600)

        self.stackedLayout = QStackedLayout(self)

        # Widget et layout principal
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.userListWidget = QListWidget()
        self.mainLayout.addWidget(self.userListWidget)
        self.stackedLayout.addWidget(self.mainWidget)

    def setupSocketThread(self):
        self.ws_thread = SocketIOThread()
        self.ws_thread.users_updated.connect(self.updateUserButtons)
        self.ws_thread.start()

    @pyqtSlot(list)
    def updateUserButtons(self, users):
        self.userListWidget.clear()
        for user in users:
            self.addUserButton(user)

    def addUserButton(self, username):
        current_user = os.getenv("USERNAME", "default_user")
        if username != current_user:
            button = QPushButton(username)
            button.clicked.connect(lambda: self.onUserButtonClicked(username))
            list_item = QListWidgetItem()
            self.userListWidget.addItem(list_item)
            self.userListWidget.setItemWidget(list_item, button)

    def onUserButtonClicked(self, username):
        print(f"Call to {username}")
        os.environ["TARGET_USERNAME"] = username
        self.startOfferer()

    def startOfferer(self):
        self.offerer = Offerer()
        self.offerer_thread = threading.Thread(
            target=self.run_offerer, daemon=True)
        self.offerer_thread.start()

    def run_offerer(self):
        asyncio.run(self.offerer.start())

    def closeEvent(self, event):
        if hasattr(self, 'offerer_thread') and self.offerer_thread.is_alive():
            self.offerer_thread.join()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    timer = QTimer()
    timer.timeout.connect(lambda: loop.run_until_complete(asyncio.sleep(0)))
    timer.start(10)

    app_window = UserWindow()
    app_window.showFullScreen()
    app_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
