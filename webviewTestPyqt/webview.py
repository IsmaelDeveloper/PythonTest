from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QApplication

app = QApplication([])

view = QWebEngineView()
page = view.page()

# Autorise sound lecture automaticly
page.settings().setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
page.profile().clearHttpCache()
# charge a web page which contain sound 
view.setUrl(QUrl("http://192.168.56.1:8080/noodle_01.html"))

view.show()
app.exec_()
