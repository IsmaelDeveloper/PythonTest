from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtCore import pyqtSignal
class WebEnginePage(QWebEnginePage):
    closeViewRequested = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.featurePermissionRequested.connect(
            self.onFeaturePermissionRequested)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        print(url)
        if url.scheme() == "closewebview":
            print("URL personnalisée détectée :", url.toString())
            self.closeViewRequested.emit()
            return False
        return super(WebEnginePage, self).acceptNavigationRequest(url, nav_type, is_main_frame)

    def onFeaturePermissionRequested(self, url, feature):
        if feature in (QWebEnginePage.MediaAudioCapture,
                       QWebEnginePage.MediaVideoCapture,
                       QWebEnginePage.MediaAudioVideoCapture):
            self.setFeaturePermission(
                url, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            super(WebEnginePage, self).onFeaturePermissionRequested(url, feature)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            print(
                f"JS Error: {message} (line: {lineNumber}, source: {sourceID})")
        else:
            print(f"JS: {message} (line: {lineNumber}, source: {sourceID})")