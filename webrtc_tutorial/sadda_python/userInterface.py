import os
import sys
import socketio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QTimer
import asyncio
import subprocess
import threading
from answerer import Answerer
sio = socketio.Client()


class SocketIOThread(QThread):
    users_updated = pyqtSignal(list)

    def __init__(self, username):
        super().__init__()
        self.username = username

    def run(self):
        sio.connect('http://127.0.0.1:6969')
        sio.emit('register', {'username': self.username})
        sio.on('update_users', self.on_update_users)
        sio.wait()

    def on_update_users(self, data):
        self.users_updated.emit(data)


class UserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupSocketThread()
        self.process_offerer = None
        self.setupAnswerer()

    def initUI(self):
        self.setWindowTitle("User List")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout(self)
        self.userListWidget = QListWidget()
        self.layout.addWidget(self.userListWidget)

    def setupSocketThread(self):
        self.ws_thread = SocketIOThread(os.getenv("USERNAME", "default_user"))
        self.ws_thread.users_updated.connect(self.updateUserButtons)
        self.ws_thread.start()

    def setupAnswerer(self):
        self.answerer = Answerer()  # Création de l'instance d'Answerer
        self.answerer.offer_received.connect(self.on_offer_received)
        self.answerer_thread = threading.Thread(
            target=self.run_answerer, daemon=True)
        self.answerer_thread.start()

    def on_offer_received(self):
        reply = QMessageBox.question(
            self, 'Call incoming', "Do you wanna accept the call ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answer_call(True)
        else:
            self.answer_call(False)

    def answer_call(self, accept):
        if accept:
            asyncio.run_coroutine_threadsafe(
                self.answerer.handle_offer(), asyncio.get_event_loop())

    def run_answerer(self):
        asyncio.run(self.answerer.start())

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
        self.launchScript()

    def launchScript(self):
        self.process = subprocess.Popen([sys.executable, 'offerer.py'])

    def closeEvent(self, event):
        if self.process_offerer:
            self.process_offerer.terminate()
            self.process_offerer.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    timer = QTimer()
    timer.timeout.connect(lambda: loop.run_until_complete(asyncio.sleep(0)))
    timer.start(10)

    app_window = UserWindow()
    app_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
