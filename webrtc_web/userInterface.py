import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile

import os


class WebEnginePage(QWebEnginePage):
    def __init__(self, *args, **kwargs):
        QWebEnginePage.__init__(self, *args, **kwargs)
        self.featurePermissionRequested.connect(
            self.onFeaturePermissionRequested)

    def onFeaturePermissionRequested(self, url, feature):
        if feature in (QWebEnginePage.MediaAudioCapture,
                       QWebEnginePage.MediaVideoCapture,
                       QWebEnginePage.MediaAudioVideoCapture):
            self.setFeaturePermission(
                url, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(
                url, feature, QWebEnginePage.PermissionDeniedByUser)


class WebView(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(WebView, self).__init__(*args, **kwargs)
        self.browser = QWebEngineView()
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(
            QWebEngineSettings.PlaybackRequiresUserGesture, False)

        self.page = WebEnginePage(self.browser)
        self.browser.setPage(self.page)
        self.setCentralWidget(self.browser)
        self.showMaximized()
        username = os.getenv("USERNAME", "defaultUser")
        # L'URL de votre interface utilisateur
        url = f"http://127.0.0.1:5501/webrtc_web/userInterface.html?username={username}"
        self.browser.load(
            QUrl(url))

    def clear_cache(self):
        # Accéder au profil par défaut
        profile = QWebEngineProfile.defaultProfile()

        # Vider le cache
        profile.clearHttpCache()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WebView()
    window.clear_cache()  # Pour vider le cache
    window.toggle_fullscreen()  # Pour mettre en plein écran
    sys.exit(app.exec_())
