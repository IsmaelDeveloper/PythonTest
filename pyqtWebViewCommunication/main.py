import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QObject, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel

class BackendHandler(QObject):
    def __init__(self, web_view):
        super().__init__()
        self.web_view = web_view

    @pyqtSlot()
    def buttonClicked(self):
        print('Button clicked, closing web view...')
        self.web_view.close()

class MyWebPage(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.channel = QWebChannel()
        self.page().setWebChannel(self.channel)
        self.backend_handler = BackendHandler(self)
        self.channel.registerObject('backend', self.backend_handler)
        self.load(QUrl("http://127.0.0.1:5500/pyqtWebViewCommunication/index.html"))

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.web_view = MyWebPage(self)
        self.layout.addWidget(self.web_view)
        self.setLayout(self.layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    widget.showFullScreen()
    sys.exit(app.exec_())