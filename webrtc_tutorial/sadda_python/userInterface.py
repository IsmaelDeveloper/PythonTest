import os
import sys
import socketio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QListWidget, QListWidgetItem, QMessageBox, QLabel, QStackedLayout, QSizePolicy, QHBoxLayout
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QTimer, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import asyncio
import subprocess
import threading
from answerer import Answerer
from audioAnswerer import AudioAnswerer
from offerer import Offerer
from audioOfferer import AudioOfferer
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


class CenteredMessageBox(QMessageBox):
    def __init__(self, *args, **kwargs):
        super(CenteredMessageBox, self).__init__(*args, **kwargs)

    def showEvent(self, event):
        super(CenteredMessageBox, self).showEvent(event)
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)


class CallingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.shouldLoopAudio = True
        self.setModal(True)
        self.autoCloseTimer = QTimer(self)
        self.autoCloseTimer.timeout.connect(self.autoClose)
        self.autoCloseTimer.setSingleShot(True)
        self.autoCloseTimer.start(30000)

    def initUI(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        audio_file_path = os.path.join(current_dir, "isCalling.mp3")
        self.player = QMediaPlayer()
        self.player.mediaStatusChanged.connect(self.checkMediaStatus)

        url = QUrl.fromLocalFile(audio_file_path)
        self.player.setMedia(QMediaContent(url))
        self.player.play()

        self.setWindowTitle("Calling")
        self.resize(400, 200)

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        layout = QVBoxLayout()

        label = QLabel("is calling...")
        layout.addWidget(label)
        layout.setAlignment(label, Qt.AlignCenter)

        self.setLayout(layout)

    def autoClose(self):
        self.shouldLoopAudio = False  # Mettre à jour le drapeau
        self.player.stop()
        self.close()

    def checkMediaStatus(self, status):
        if status == QMediaPlayer.EndOfMedia and self.shouldLoopAudio:
            self.player.setPosition(0)
            self.player.play()

    def closeEvent(self, event):
        self.shouldLoopAudio = False  # Mettre à jour le drapeau
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.stop()
        super().closeEvent(event)


class CallReceiver(QWidget):
    hangupRequested = pyqtSignal()
    closeCallingDialog = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.audioAnswerer = AudioAnswerer()
        self.answerer = Answerer()
        self.videoAccepted = False
        self.audioEvent = False
        self.windowCanBeOpen = True
        self.initUI()
        self.setupAnswerer()
        self.setupAnswererAudio()

    def initUI(self):
        if sio.connected:
            sio.disconnect()
        sio.connect('http://192.168.0.136:6969')
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
        # Largeur fixe, ajustez selon vos besoins
        self.hangupButton.setFixedWidth(100)
        self.hangupButton.setStyleSheet(
            "background-color: red; border-radius: 10px; color: white; padding: 5px;")

        self.hangupButton.clicked.connect(self.hangupCall)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.hangupButton, 0, Qt.AlignCenter)

        # Ajoutez le layout du bouton au layout principal
        self.layout.addLayout(buttonLayout)

    async def connect_socketio(self):
        await self.sio.connect('http://192.168.0.136:6969')
        await self.sio.emit('register', {'username': self.username})
        self.sio.on('update_users', self.on_update_users)

    def setupAnswerer(self):
        self.answerer.offer_received.connect(self.on_offer_received)

        self.answerer.video_frame_received.connect(self.updateVideoFrame)
        self.answerer_thread = threading.Thread(
            target=self.run_answerer, daemon=True)
        self.answerer_thread.start()

    def setupAnswererAudio(self):
        self.audioAnswerer.audio_offer_received.connect(
            self.on_audio_offer_received)
        self.answerer_audio_thread = threading.Thread(
            target=self.run_answerer_audio, daemon=True)
        self.answerer_audio_thread.start()

    def openCallReceiver(self):
        if self.windowCanBeOpen:
            self.closeCallingDialog.emit()
            self.windowCanBeOpen = False
            self.showFullScreen()
            self.show()

    def updateVideoFrameForOffer(self, frame):
        self.openCallReceiver()
        self.updateVideoFrame(frame)

    def updateVideoFrame(self, frame):
        print("Update video frame")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qImg = QImage(
            frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0], QImage.Format_RGB888)
        self.videoLabel.setPixmap(QPixmap.fromImage(qImg).scaled(
            self.videoLabel.width(), self.videoLabel.height(), Qt.KeepAspectRatio))

    def hangupCall(self):
        # disconnect signal
        self.answerer.offer_received.disconnect()
        self.answerer.video_frame_received.disconnect()
        self.audioAnswerer.audio_offer_received.disconnect()

        # stop and close rtc connection properly
        self.answerer.end_call()
        self.audioAnswerer.end_call()
        self.hangupRequested.emit()

        # reinitialize call related components
        self.audioAnswerer = AudioAnswerer()
        self.answerer = Answerer()
        self.videoAccepted = False
        self.audioEvent = False

        # reinitialize call related threads
        self.setupAnswerer()
        self.setupAnswererAudio()

        self.videoLabel.clear()

        print("Hangup call")
        self.close()

    def on_audio_offer_received(self):
        print("Audio offer received")
        self.audioEvent = True
        if self.videoAccepted:
            print("Audio offer accepted")
            asyncio.run_coroutine_threadsafe(
                self.audioAnswerer.handle_offer(), asyncio.get_event_loop())

    def on_offer_received(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        audio_file_path = os.path.join(current_dir, "calling.mp3")
        self.player = QMediaPlayer()
        # Utilisez le chemin absolu ici
        url = QUrl.fromLocalFile(audio_file_path)
        self.player.setMedia(QMediaContent(url))
        self.player.play()
        messagebox = CenteredMessageBox()
        messagebox.setWindowTitle('Call incoming')
        messagebox.setText("Do you wanna accept the call?")
        messagebox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        messagebox.setDefaultButton(QMessageBox.No)

        self.messageBoxTimer = QTimer()
        self.messageBoxTimer.setSingleShot(True)
        self.messageBoxTimer.timeout.connect(
            lambda: self.closeMessageBox(messagebox))

        # Démarrer le QTimer
        self.messageBoxTimer.start(20000)

        reply = messagebox.exec_()

        if reply == QMessageBox.Yes:
            self.player.stop()
            self.answer_call(True)
            self.showFullScreen()
            self.show()
            if self.audioEvent == True:
                asyncio.run_coroutine_threadsafe(
                    self.audioAnswerer.handle_offer(), asyncio.get_event_loop())
                self.videoAccepted = True
        else:
            self.player.stop()
            self.answer_call(False)

    def closeMessageBox(self, messagebox: CenteredMessageBox):
        messagebox.done(0)

    def answer_call(self, accept):
        if accept:
            asyncio.run_coroutine_threadsafe(
                self.answerer.handle_offer(), asyncio.get_event_loop())

    def run_answerer(self):
        asyncio.run(self.answerer.start())

    def run_answerer_audio(self):
        asyncio.run(self.audioAnswerer.start())


class UserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupSocketThread()
        self.process_offerer = None
        self.offererAudio = None
        self.offererVideo = None
        self.callingDialog = None
        self.callReceiver = CallReceiver()
        self.callReceiver.hangupRequested.connect(self.hangupCall)
        self.callReceiver.closeCallingDialog.connect(self.callingDialogClose)

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

    def hangupCall(self):
        # Fermer la connexion RTC pour l'offreur
        if self.offererVideo is not None:
            self.offererVideo.end_call()
            self.offererVideo = None

        if self.offererAudio is not None:
            self.offererAudio.end_call()
            self.offererAudio = None

    def onUserButtonClicked(self, username):
        print(f"Call to {username}")
        os.environ["TARGET_USERNAME"] = username

        self.callingDialog = CallingDialog()
        self.callingDialog.show()

        self.startOfferer()
        self.callReceiver.windowCanBeOpen = True

    def callingDialogClose(self):
        print("calling dialog event close received")
        if self.callingDialog:
            self.callingDialog.autoClose()

    def startOfferer(self):
        # Pour l'audio
        self.offererAudio = AudioOfferer()
        self.audio_offerer_thread = threading.Thread(
            target=self.run_offerer_audio, daemon=True)
        self.audio_offerer_thread.start()

        # Pour la vidéo
        self.offererVideo = Offerer()
        self.offererVideo.video_frame_received.connect(
            self.run_videoForOfferer)
        self.video_offerer_thread = threading.Thread(
            target=self.run_offerer_video, daemon=True)
        self.video_offerer_thread.start()

    def run_videoForOfferer(self, frame):
        print("run video for offerer")
        self.callReceiver.updateVideoFrameForOffer(frame)

    def run_offerer_audio(self):
        asyncio.run(self.offererAudio.start())

    def run_offerer_video(self):
        asyncio.run(self.offererVideo.start())

    def closeEvent(self, event):
        # if hasattr(self, 'offerer_thread') and self.audio_offerer_thread.is_alive():
        #     self.audio_offerer_thread.join()
        if hasattr(self, 'offerer_thread') and self.video_offerer_thread.is_alive():
            self.video_offerer_thread.join()
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
