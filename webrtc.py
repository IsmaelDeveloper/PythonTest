import os
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

class WebEnginePage(QWebEnginePage):
    def __init__(self, *args, **kwargs):
        QWebEnginePage.__init__(self, *args, **kwargs)
        self.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

    def onFeaturePermissionRequested(self, url, feature):
        if feature in (QWebEnginePage.MediaAudioCapture, 
            QWebEnginePage.MediaVideoCapture, 
            QWebEnginePage.MediaAudioVideoCapture):
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionDeniedByUser)

class WindowWebRTC(QMainWindow):
    def __init__(self):
        super(WindowWebRTC, self).__init__()
        # Central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Main layout
        self.main_layout = QVBoxLayout(central_widget)

        # WebRTC View
        self.webRTCView = QWebEngineView()
        page = WebEnginePage(self.webRTCView)
        self.webRTCView.setPage(page)
        self.webRTCView.load(QUrl("http://127.0.0.1:8000/"))

        self.main_layout.addWidget(self.webRTCView, alignment=Qt.AlignTop)

        # Main window settings
        self.setWindowTitle("WebRTC Sample")
        self.setGeometry(100, 100, 1024, 576)

if __name__ == "__main__":
    app = QApplication([])
    win = WindowWebRTC()
    win.show()
    app.exec()
