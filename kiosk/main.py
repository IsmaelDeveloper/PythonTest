import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile


class WebEnginePage(QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.featurePermissionRequested.connect(
            self.onFeaturePermissionRequested)

    def onFeaturePermissionRequested(self, url, feature):
        # Accorder automatiquement toutes les permissions nécessaires
        if feature in (QWebEnginePage.MediaAudioCapture,
                       QWebEnginePage.MediaVideoCapture,
                       QWebEnginePage.MediaAudioVideoCapture):
            self.setFeaturePermission(
                url, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            super(WebEnginePage, self).onFeaturePermissionRequested(url, feature)


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

        # set Timer for close btn
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.updateCountdown)
        self.countdown_button = QPushButton("50", self)
        self.countdown_button.clicked.connect(self.closeWebview)

    def initUI(self):
        self.setObjectName("mainWindow")
        self.host = "http://192.168.0.3"
        self.deviceId = "DailySafe_8afa173b69d9408dbcc90c77f75128a6"
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

        self.configureWebEngineSettings()

        self.loadStyleSheet()

    def loadStyleSheet(self):
        with open('style.qss', 'r') as file:
            self.setStyleSheet(file.read())

    def configureWebEngineSettings(self):
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(
            QWebEngineSettings.PlaybackRequiresUserGesture, False)

    def clearCache(self):
        QWebEngineProfile.defaultProfile().clearHttpCache()

    def openWebviewOnMp4(self, url):
        self.video_player.stop()
        main_layout = self.layout()
        self.web_view.setUrl(QUrl(url))
        main_layout.replaceWidget(self.video_widget, self.web_view)
        self.video_widget.setParent(None)
        self.video_widget.hide()
        self.web_view.show()
        QTimer.singleShot(100, self.setupCountdown)

    def openFullScreenWebView(self, url):
        self.clearCache()
        self.video_player.stop()
        self.video_widget.hide()
        self.qml_view.hide()
        self.buttons_view.hide()

        # reinitialize self.web_view
        if self.web_view.parent() is not None:
            self.web_view.setParent(None)
        self.web_view = QWebEngineView()
        self.configureWebEngineSettings()

        self.web_view.setUrl(QUrl(url))
        self.web_view.setWindowFlags(Qt.FramelessWindowHint)
        self.web_view.showFullScreen()

    def setupCountdown(self):
        self.countdown_time = 50
        self.countdown_button.setText(str(self.countdown_time))
        self.countdown_button.resize(100, 50)
        web_view_geometry = self.web_view.geometry()
        button_x = web_view_geometry.right() - self.countdown_button.width() - 10
        button_y = web_view_geometry.top() + 10
        self.countdown_button.move(button_x, button_y)
        self.countdown_button.raise_()
        self.countdown_button.show()

        self.countdown_timer.start(1000)

    def updateCountdown(self):
        self.countdown_time -= 1
        self.countdown_button.setText(str(self.countdown_time))
        if self.countdown_time <= 0:
            self.closeWebview()

    def closeWebview(self):
        self.countdown_timer.stop()
        self.countdown_button.hide()
        self.restoreVideoView()
        self.web_view.setParent(None)
        self.web_view.hide()

    def restoreVideoView(self):
        self.video_widget.setParent(self)
        main_layout = self.layout()
        main_layout.addWidget(self.video_widget, 3)
        self.video_player.setVideoOutput(self.video_widget)
        self.video_widget.show()
        self.video_player.stop()
        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(
            "./ressources/default_media.mp4")))
        self.video_player.play()

    @pyqtSlot()
    def onMediaStatusChanged(self):
        if self.video_player.mediaStatus() == QMediaPlayer.EndOfMedia:
            self.video_player.setPosition(0)
            self.video_player.play()

    @pyqtSlot()
    def onDustClicked(self):
        print("Dust button clicked")
        self.openWebviewOnMp4(self.host +
                              "/signagemenu/dust.html?appId=" + self.deviceId)

    @pyqtSlot()
    def onWeatherClicked(self):
        print("Weather button clicked")
        self.openWebviewOnMp4(self.host +
                              "/signagemenu/weather.html?appId=" + self.deviceId)

    @pyqtSlot()
    def onBusClicked(self):
        print("Bus button clicked")
        self.openWebviewOnMp4(self.host +
                              "/signagemenu/traffic.html?appId=" + self.deviceId)

    @pyqtSlot()
    def onKioskClicked(self):
        self.openFullScreenWebView(self.host + "/kiosk/")


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.showFullScreen()
    ex.show()

    sys.exit(app.exec_())
