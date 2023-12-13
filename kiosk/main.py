import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWebEngineWidgets import QWebEngineView


class MainApp(QWidget):
    dustClicked = pyqtSignal()
    weatherClicked = pyqtSignal()
    busClicked = pyqtSignal()
    kioskClicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.initUI()
        self.dustClicked.connect(self.onDustClicked)
        self.weatherClicked.connect(self.onWeatherClicked)
        self.busClicked.connect(self.onBusClicked)
        self.kioskClicked.connect(self.onKioskClicked)

    def initUI(self):
        self.setObjectName("mainWindow")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.qml_view = QQuickWidget()
        main_layout.addWidget(self.qml_view, 4)

        self.buttons_view = QQuickWidget()
        self.buttons_view.rootContext().setContextProperty("homeApp", self)
        self.buttons_view.setSource(QUrl("home.qml"))
        main_layout.addWidget(self.buttons_view, 1)

        # Initialization of QMediaPlayer
        self.video_player = QMediaPlayer()

        # Creation and configuration of QVideoWidget
        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.IgnoreAspectRatio)
        self.video_player.setVideoOutput(self.video_widget)
        # Add QVideoWidget to the layout
        main_layout.addWidget(self.video_widget, 3)

        self.video_player.setMedia(QMediaContent(
            QUrl.fromLocalFile("./ressources/default_media.mp4")))
        self.video_player.mediaStatusChanged.connect(self.onMediaStatusChanged)
        self.video_player.play()

        self.web_view = QWebEngineView()

        self.loadStyleSheet()

    def loadStyleSheet(self):
        with open('style.qss', 'r') as file:
            self.setStyleSheet(file.read())

    def openWebviewOnMp4(self, url):
        self.video_player.stop()
        main_layout = self.layout()
        self.web_view.setUrl(QUrl(url))
        main_layout.replaceWidget(self.video_widget, self.web_view)
        self.video_widget.hide()
        self.web_view.show()

    def openFullScreenWebView(self, url):
        self.video_player.stop()
        self.video_widget.hide()
        self.qml_view.hide()
        self.buttons_view.hide()

        self.web_view.setUrl(QUrl(url))
        self.web_view.showMaximized()

    @pyqtSlot()
    def onMediaStatusChanged(self):
        if self.video_player.mediaStatus() == QMediaPlayer.EndOfMedia:
            self.video_player.setPosition(0)
            self.video_player.play()

    @pyqtSlot()
    def onDustClicked(self):
        print("Dust button clicked")
        self.openWebviewOnMp4("https://www.google.com")

    @pyqtSlot()
    def onWeatherClicked(self):
        print("Weather button clicked")
        self.openWebviewOnMp4("https://www.naver.com")

    @pyqtSlot()
    def onBusClicked(self):
        print("Bus button clicked")
        self.openWebviewOnMp4("https://www.naver.com")

    @pyqtSlot()
    def onKioskClicked(self):
        self.openFullScreenWebView("https://www.naver.com")


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.showFullScreen()
    ex.show()

    sys.exit(app.exec_())
