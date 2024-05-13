import sys
import cv2
import os
import socketio
import ssl
import json
import urllib3
from PyQt5.QtWidgets import QMessageBox, QLabel, QSpacerItem, QSizePolicy, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QTabWidget
from PyQt5.QtCore import QThread, Qt, QUrl, pyqtSignal, pyqtSlot, QTimer, QPropertyAnimation, QRect, QJsonDocument
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtGui import QImage, QPixmap
from utils.customTabBar import CustomTabBar
from utils.toolWindow import ToolWindow
from utils.LocalParameterStorage import LocalParameterStorage
from utils.LocalDbParameterStorage import LocalDbParameterStorage
from urllib.parse import quote
from utils.faceRecognition import WebcamWidget
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from datetime import datetime

class SingleRequestManager:
    def __init__(self, payload, url, callback):
        self.payload = payload
        self.url = url
        self.callback = callback
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handleResponse)

    def sendRequest(self):
        request = QNetworkRequest(QUrl(self.url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        payload_bytes = QJsonDocument(self.payload).toJson()
        self.network_manager.post(request, payload_bytes)

    def handleResponse(self, reply):
        if reply.error():
            print(f"HTTP REQUEST ERROR: {reply.errorString()}")
            response_data = None
        else:
            response_data = str(reply.readAll(), 'utf-8')

        if self.callback:  
            self.callback(response_data)


class PollingManager:
    def __init__(self, payload, url, interval, callback):
        self.payload = payload
        self.url = url
        self.interval = interval
        self.callback = callback
        self.timer = QTimer()
        self.timer.timeout.connect(self.sendRequest)
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handleResponse)

    def start(self):
        self.sendRequest()
        self.timer.start(self.interval)

    def sendRequest(self):
        request = QNetworkRequest(QUrl(self.url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        payload_bytes = QJsonDocument(self.payload).toJson()
        self.network_manager.post(request, payload_bytes)

    def handleResponse(self, reply):
        if reply.error():
            print(f"HTTP REQUEST ERROR :  {reply.errorString()}")
            response_data = None
        else:
            response_data = str(reply.readAll(), 'utf-8')
        
        if self.callback:  
            self.callback(response_data)
            
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


class SocketIOThread(QThread):
    offerReceived = pyqtSignal(dict)
    iceCandidateReceived = pyqtSignal(dict)
    multipleCallOfferReceived = pyqtSignal(str)
    webrtcDataServerList = pyqtSignal(dict)
    socketIdReceived = pyqtSignal(str)

    def __init__(self, url, username):
        QThread.__init__(self)
        self.url = url
        self.username = username
        self.socketId = None 
        self.sio = socketio.Client(ssl_verify=False)
    def run(self):

        @self.sio.event
        def connect():
            self.socketId = self.sio.eio.sid
            self.socketIdReceived.emit(self.socketId)
            print("Connected to server")
            self.sio.emit('register', {'username': self.username})
            self.sio.emit('usernm-client', self.username)

        @self.sio.event
        def disconnect():
            print("Disconnected from server")

        @self.sio.event
        def getOffer(data):
            self.offerReceived.emit(data)

        @self.sio.event
        def receiveCandidateInAnswer(data):
            self.iceCandidateReceived.emit(data)
        
        @self.sio.on('boom-server')
        def boom_server(UUID):
            self.multipleCallOfferReceived.emit(UUID)
            print("MULTIPLE CALL ")
        
        @self.sio.on('webrtc-data-server')
        def webrtc_data_server(message):
            print("webrtc message ")
            self.webrtcDataServerList.emit(message)

        self.sio.connect(self.url)
        self.sio.wait()

    def reRegisterUser(self):
        if self.sio.connected:
            self.sio.emit('register', {'username': self.username})


class MainApp(QWidget):
    dustClicked = pyqtSignal()
    weatherClicked = pyqtSignal()
    busClicked = pyqtSignal()
    kioskClicked = pyqtSignal()
    callClicked = pyqtSignal()
    openWebViewSignal = pyqtSignal(dict)
    openWebViewSignalForMultipleCall = pyqtSignal(str)
    webrtcDataServerListObject = []

    def __init__(self):
        super().__init__()
        self.initUI()
        self.isFullScreenWebViewOpen = False
        self.dustClicked.connect(self.onDustClicked)
        self.weatherClicked.connect(self.onWeatherClicked)
        self.busClicked.connect(self.onBusClicked)
        self.kioskClicked.connect(self.onKioskClicked)
        self.callClicked.connect(self.onCallClicked)
        self.isWebviewCloseByUser = False

        self.iceCandidatesQueue = []

        # set Timer for close btn
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.updateCountdown)
        self.countdown_button = QPushButton("닫기 (50)", self)

        self.countdown_button.setObjectName("webviewCloseButton")
        self.countdown_button.hide()
        self.countdown_button.clicked.connect(self.closeWebview)
        self.isWebviewOnMp4Open = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.startSocket()
        self.LocalDbParameterStorage = LocalDbParameterStorage()
        self.offerSent = False
        self.multipleCallJsSent = False
        self.openWebViewSignal.connect(self.openFullScreenWebViewSlot)
        self.openWebViewSignalForMultipleCall.connect(self.openFullScreenWebViewForMultipleCallSlot)
        current_timestamp = int(datetime.now().timestamp() * 1000)
        payload = {
            "appID": self.deviceId,
            "date": current_timestamp,
            "edgeBoxName": "A01",
            "serviceName": "A01"
        }
        url = "http://192.168.0.3/v1/appapi/device/regist"
        self.singleRequestManager = SingleRequestManager(payload, url, self.requestCallback)
        self.singleRequestManager.sendRequest()

        
        payload = {
            "appID": self.deviceId,
            "cameraStatus": 0,
            "edgeboxStatus": 0,
            "featureType": "KT",
            "modifiedAt": current_timestamp
        }
        url = "http://192.168.0.3/v1/appapi/polling"
        interval = 60000  
        self.pollingManager = PollingManager(payload, url, interval, self.pollingCallback)
        self.pollingManager.start()
    
    def startSocket(self):
        self.socket_thread = SocketIOThread(
            'https://kiosk-chat.musicen.com:8234', self.username)
        self.socket_thread.socketIdReceived.connect(self.handleSocketId)
        self.socket_thread.start()
        self.socket_thread.offerReceived.connect(self.handleOffer)
        self.socket_thread.multipleCallOfferReceived.connect(self.handleMultipleCallOffer)
        self.socket_thread.webrtcDataServerList.connect(self.handleWebrtctDataServer)
        
        self.socket_thread.iceCandidateReceived.connect(
            lambda data: self.iceCandidatesQueue.append(data)
        )

    def userCloseWebview(self):
        self.isWebviewCloseByUser = True
        self.closeFullScreenWebView()
    def handleSocketId(self, socketId):
        self.socketId = socketId 

    def requestCallback(self, response):
        print("Single request answer:", response)    

    def pollingCallback(self, response):
        print("Polling request answer : ", response)

    def initUI(self):
        try:
            with open('/etc/machine-id', 'r') as file:
                machine_id = file.read().strip()
        except FileNotFoundError:
            print("file /etc/machine-id not found.")
            machine_id = "51b51c691e4d4f379ce9a8c98585bff5"
        self.widget_states = None
        self.parameter = LocalParameterStorage()
        self.setObjectName("mainWindow")
        self.deviceId = f"DailySafe_{machine_id}"
        self.username = "a"
        self.host = "http://211.46.245.40:81"
        self.callingWebviewUrl = "https://kiosk-chat.musicen.com:8234/userInterface.html?username=" + self.username

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.webcam_widget = WebcamWidget(self)
        self.webcam_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.webcam_widget, 4)

        spacer_top = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer_top)

        self.buttons_view = QQuickWidget()
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(
            os.path.abspath(__file__)))
        qml_path = os.path.join(
            self.base_path, 'ressources', 'qml', 'home.qml')

        self.buttons_view.rootContext().setContextProperty("homeApp", self)
        self.buttons_view.setSource(QUrl.fromLocalFile(qml_path))
        main_layout.addWidget(self.buttons_view, 1)

        # Initialization of QMediaPlayer
        self.video_player = QMediaPlayer()

        # Creation and configuration of QVideoWidget
        self.video_widget = QVideoWidget()

        self.video_widget.setAspectRatioMode(Qt.IgnoreAspectRatio)
        self.video_player.setVideoOutput(self.video_widget)
        # Add QVideoWidget to the layout
        main_layout.addWidget(self.video_widget, 3)

        mp4_path = os.path.join(
            self.base_path, 'ressources', 'default_media.mp4')
        self.video_player.setMedia(QMediaContent(
            QUrl.fromLocalFile(mp4_path)))
        self.video_player.mediaStatusChanged.connect(self.onMediaStatusChanged)
        self.video_player.play()

        self.web_view = QWebEngineView()

        self.configureWebEngineSettings()

        self.loadStyleSheet()
        self.addSlideMenu()

    def handleOffer(self, offerData):
        if self.offerSent == False and self.isFullScreenWebViewOpen == False:
            if offerData.get("target") == self.username:
                reply = QMessageBox.question(
                    self, '전화', "누군가 자네를 부르고 있네", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QTimer.singleShot(
                        2000, lambda: self.openWebViewSignal.emit(offerData))

    def handleWebrtctDataServer(self, message):
        print(message)
        if self.isFullScreenWebViewOpen == False:
            self.webrtcDataServerListObject.append(message)
        else:
            jsCode = f"window.webrtcDataServerOn({json.dumps(message)})"
    def handleMultipleCallOffer(self, UUID):
        print(self.isFullScreenWebViewOpen)
        if self.isFullScreenWebViewOpen == False:
            reply = QMessageBox.question(
                self, '전화', "누군가 자네를 부르고 있네", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                print("he said yes")
                print(UUID)
                QTimer.singleShot(
                    2000, lambda: self.openWebViewSignalForMultipleCall.emit(UUID))


    @pyqtSlot(dict)
    def openFullScreenWebViewSlot(self, offerData):
        self.webcam_widget.releaseCamera()
        url = self.callingWebviewUrl
        self.openFullScreenWebView(url, offerData)

    @pyqtSlot(str)
    def openFullScreenWebViewForMultipleCallSlot(self, UUID):
        self.webcam_widget.releaseCamera()
        url = self.callingWebviewUrl
        self.openFullScreenWebView(url, UUID, True)

    def sendIceCandidateToWebView(self, candidateData):
        jsCode = f"window.receiveCandidateInAnswer({json.dumps(candidateData)})"
        self.web_view.page().runJavaScript(jsCode)

    def addSlideMenu(self):
        menu_width = 250
        self.slideMenu = QFrame(self)
        self.slideMenu.setGeometry(-menu_width, 0, menu_width, self.height())

        # create layout for slide menu
        slideMenuLayout = QHBoxLayout(self.slideMenu)
        slideMenuLayout.setContentsMargins(0, 0, 0, 0)
        slideMenuLayout.setSpacing(0)

        # create tab widget
        self.tabWidget = QTabWidget(self.slideMenu)
        customTabBar = CustomTabBar()
        customTabBar.firstIconClicked.connect(self.onToolImageClicked)
        customTabBar.secondIconClicked.connect(self.onRefreshImageClicked)

        self.tabWidget.setTabBar(customTabBar)
        self.tabWidget.setStyleSheet("background-color: white;")
        tab1 = QWidget()
        tab2 = QWidget()

        self.tabWidget.addTab(tab1, "Onglet 1")
        self.tabWidget.addTab(tab2, "Onglet 2")
        self.tabWidget.setCurrentIndex(0)

        # add content on tab1
        # tab1_layout = QVBoxLayout()
        # tab1.setLayout(tab1_layout)
        # tab1_layout.addWidget(QLabel("Contenu de l'Onglet 1"))
        # tab1_layout.addWidget(QPushButton("Bouton dans Onglet 1"))

        # add widget to slide menu
        slideMenuLayout.addWidget(self.tabWidget)

        # Animation for slide menu
        self.menuAnimation = QPropertyAnimation(self.slideMenu, b"geometry")
        self.menuAnimation.setDuration(500)

    def onToolImageClicked(self):
        print("Tool clicked")
        self.toolWindow = ToolWindow()
        self.toolWindow.show()

    def onRefreshImageClicked(self):
        print("Refresh clicked")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F3:
            self.toggleMenu()

    def toggleMenu(self):
        print("ok")
        menu_width = self.slideMenu.width()
        is_hidden = self.slideMenu.x() == -menu_width  # check if the menu is hidden

        if is_hidden:
            new_x = 0
        else:
            new_x = -menu_width
        #  Animation
        self.menuAnimation.setStartValue(self.slideMenu.geometry())
        end_geometry = QRect(new_x, 0, menu_width, self.height() // 2)
        self.menuAnimation.setEndValue(end_geometry)
        self.menuAnimation.start()

    def loadStyleSheet(self):
        qss_path = os.path.join(
            self.base_path, 'ressources', 'qss', 'style.qss')
        with open(qss_path, 'r') as file:
            self.setStyleSheet(file.read())

    def configureWebEngineSettings(self):
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.AllowGeolocationOnInsecureOrigins, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, False)


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
        self.isWebviewOnMp4Open = True
        QTimer.singleShot(100, self.setupCountdown)

    def openFullScreenWebView(self, url, offerData=None, isMultipleCall = False):
        if self.isWebviewOnMp4Open:
            self.closeWebview()
        self.storeWidgetStates()
        # self.clearCache()
        self.video_player.stop()
        self.video_widget.setParent(None)
        self.video_widget.hide()
        self.buttons_view.hide()
        self.webcam_widget.hide()

        # reinitialize self.web_view
        if self.web_view.parent() is not None:
            self.web_view.setParent(None)
        self.web_view = QWebEngineView()
        if offerData is not None and isMultipleCall == False:
            self.web_view.loadFinished.connect(
                lambda ok:  self.sendOfferToWebView(ok, offerData))
        
        if offerData is not None and isMultipleCall == True:
            self.web_view.loadFinished.connect(
                  lambda ok: self.sendMultipleCallToWebView(ok, offerData))

        self.configureWebEngineSettings()
        custom_page = WebEnginePage(self.web_view)
        custom_page.closeViewRequested.connect(self.userCloseWebview)
        self.web_view.setPage(custom_page)

        self.web_view.setUrl(QUrl(url))
        self.web_view.setWindowFlags(Qt.FramelessWindowHint)
        self.web_view.showFullScreen()

        self.offerSent = False
        self.isFullScreenWebViewOpen = True

    def sendMultipleCallToWebView(self, ok, offerData):
        if ok:
            self.isWebviewCloseByUser = False
            print(" Load finish")
            print(offerData)
            print(self.webrtcDataServerListObject)
            if self.multipleCallJsSent == False:
                jsCode = f"window.multipleCallFromPython({json.dumps(offerData)})"
                self.web_view.page().runJavaScript(jsCode)
                self.multipleCallJsSent = True
        else:
            if self.isWebviewCloseByUser == False:
                self.closeFullScreenWebView()
                self.checkInternetPopup()
            # self.webcam_widget.releaseCamera()
            # self.openFullScreenWebView(
            # self.callingWebviewUrl, offerData, True)
            # print("loading error")

    def sendOfferToWebView(self, ok, offerData):
        if ok:
            self.isWebviewCloseByUser = False
            if not self.offerSent:
                for candidate in self.iceCandidatesQueue:
                    print("Sending candidate to webview")
                    self.sendIceCandidateToWebView(candidate)
                self.iceCandidatesQueue.clear()
                jsCode = f"window.getOffer({offerData})"
                self.web_view.page().runJavaScript(jsCode)
                self.offerSent = True
        else:
            if self.isWebviewCloseByUser == False:
                self.closeFullScreenWebView()
                self.checkInternetPopup()
            # self.webcam_widget.releaseCamera()
            # self.openFullScreenWebView(
            #     self.callingWebviewUrl, offerData)

    def storeWidgetStates(self):
        self.widget_states = {
            'video_widget': self.video_widget.isVisible(),
            'buttons_view': self.buttons_view.isVisible(),
            'web_view': self.web_view.isVisible()
        }

    def checkInternetPopup(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle('오류')
        msgBox.setText("통화에 연결할 수 없습니다. 인터넷 연결을 확인하세요.")
        msgBox.setStandardButtons(QMessageBox.Yes)
        buttonY = msgBox.button(QMessageBox.Yes)
        buttonY.setText("확인")  # Personnalisez le label du bouton ici
        msgBox.exec_()



    def sendCloseSignalToWebView(self):
            if self.web_view:
                jsCode = "if (typeof closeCamera === 'function') closeCamera();"
                self.web_view.page().runJavaScript(jsCode)

    def closeFullScreenWebView(self):
        self.sendCloseSignalToWebView()
        self.multipleCallJsSent = False
        self.web_view.setUrl(QUrl("about:blank"))
        self.web_view.setParent(None)
        self.web_view.hide() 
        # self.web_view = QWebEngineView()

        self.video_widget.setParent(self)
        main_layout = self.layout()

        if self.widget_states['video_widget']:
            main_layout.addWidget(self.video_widget, 3)
            self.video_widget.show()
            self.restoreVideoView()
        self.webcam_widget.reactivateCamera()
        self.webcam_widget.show()
        self.buttons_view.setVisible(self.widget_states['buttons_view'])
        self.web_view.setVisible(self.widget_states['web_view'])
        self.isFullScreenWebViewOpen = False
        self.socket_thread.reRegisterUser() 
        
        # self.startSocket()
        # self.isWebviewCloseByUser = False



    def setupCountdown(self):
        self.countdown_time = 50
        self.countdown_button.setText("닫기 (" + str(self.countdown_time) + ")")
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
        self.countdown_button.setText("닫기 (" + str(self.countdown_time) + ")")
        if self.countdown_time <= 0:
            self.closeWebview()

    def closeWebview(self):
        self.countdown_timer.stop()
        self.countdown_button.hide()
        self.restoreVideoView()
        self.web_view.setParent(None)
        self.web_view.hide()
        self.isWebviewOnMp4Open = False

    def restoreVideoView(self):
        mp4_path = os.path.join(
            self.base_path, 'ressources', 'default_media.mp4')

        self.video_widget.setParent(self)
        main_layout = self.layout()
        main_layout.addWidget(self.video_widget, 3)
        self.video_player.setVideoOutput(self.video_widget)
        self.video_widget.show()
        self.video_player.stop()
        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(
            mp4_path)))
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

    @pyqtSlot()
    def onCallClicked(self):
        self.webcam_widget.releaseCamera()
        self.openFullScreenWebView(
            self.callingWebviewUrl)


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.showFullScreen()
    ex.show()

    sys.exit(app.exec_())
