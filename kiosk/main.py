import sys
import os
import json
import urllib3
import requests
import sqlite3
import base64
import zipfile
import shutil
from io import BytesIO
from PyQt5.QtWidgets import QMessageBox, QDialog, QLineEdit, QLabel, QSpacerItem, QSizePolicy, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QTabWidget, QInputDialog
from PyQt5.QtCore import Qt, QProcess, QUrl, pyqtSignal, pyqtSlot, QTimer, QPropertyAnimation, QRect, QProcess
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile
from utils.customTabBar import CustomTabBar
from utils.toolWindow import ToolWindow
from utils.LocalParameterStorage import LocalParameterStorage
from utils.LocalDbParameterStorage import LocalDbParameterStorage
from utils.PollingManager import PollingManager
from utils.faceRecognition import WebcamWidget
from utils.WebEngine import WebEnginePage
from utils.SocketIoThread import SocketIOThread

class MainApp(QWidget):
    dustClicked = pyqtSignal()
    weatherClicked = pyqtSignal()
    busClicked = pyqtSignal()
    kioskClicked = pyqtSignal()
    callClicked = pyqtSignal()
    openWebViewSignal = pyqtSignal(dict)
    openWebViewSignalForMultipleCall = pyqtSignal(str)

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
        
        
        # payload = {
        #     "appID": self.deviceId,
        #     "cameraStatus": 0,
        #     "edgeboxStatus": 0,
        #     "featureType": "KT",
        #     "modifiedAt": current_timestamp
        # }
        payload = { 
            "kioskSeq": self.kioskSeq,
            "cameraSttusAt" : "Y"
        }
        url = "http://newk.musicen.com/kiosk/polling.api"
        interval = 60000  
        self.pollingManager = PollingManager(payload, url, interval, self.pollingCallback)
        self.pollingManager.start()

    
    def check_existing_user(self):
        connection = sqlite3.connect('kioskdb.db')
        cursor = connection.cursor()
        cursor.execute('SELECT instt_code, kiosk_seq FROM user LIMIT 1')
        result = cursor.fetchone()
        connection.close()
        
        if result:
            self.insttCode = result[0]
            self.kioskSeq = result[1]
            print(f"Existing instt_code found: {self.insttCode}, kiosk_seq found: {self.kioskSeq}")
        else:
            self.showKioskInputPopup()



    def showKioskInputPopup(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('키오스크 번호 입력')
        dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)  # Remove the close button
        layout = QVBoxLayout()

        label = QLabel('키오스크 번호를 입력해 주세요:')
        layout.addWidget(label)

        input_field = QLineEdit()
        layout.addWidget(input_field)

        button = QPushButton('확인')
        button.clicked.connect(lambda: self.onKioskIdEntered(dialog, input_field))
        layout.addWidget(button)

        dialog.setLayout(layout)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.adjustSize()  # Adjust the size of the dialog
        rect = dialog.geometry()
        center = QApplication.primaryScreen().availableGeometry().center()
        rect.moveCenter(center)
        dialog.setGeometry(rect)

        dialog.exec_()


    def onKioskIdEntered(self, dialog, input_field):
        id = input_field.text()
        dialog.close()
        self.registId(id)

    def registId(self, id): 
        payload = { 
            "insttCode": id,
        }
        url = "http://newk.musicen.com/kiosk/registKiosk.api"
        headers = {"Content-Type" : "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        jsonResponse = response.json()
        print(jsonResponse.get('data'))
        if(response.status_code == 200):
            self.insttCode = id
            self.kioskSeq = jsonResponse.get('data').get('kioskSeq')
            print(self.kioskSeq)
            self.insert_user(id, self.kioskSeq) 
        else:
            self.showCenteredMessageBox('오류', '잘못된 코드입니다. 다시 시도해 주세요.')
            self.showKioskInputPopup()

        
    def insert_user(self, instt_code, kiosk_seq):
        connection = sqlite3.connect('kioskdb.db')
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO user (instt_code, kiosk_seq)
            VALUES (?, ?)
        ''', (instt_code, kiosk_seq))
        connection.commit()
        connection.close()


    
    def showCenteredMessageBox(self, title, message):
        msgBox = QMessageBox(QMessageBox.Warning, title, message, QMessageBox.Ok, self)
        msgBox.setWindowModality(Qt.ApplicationModal)
        msgBox.adjustSize()
        rect = msgBox.geometry()
        center = QApplication.primaryScreen().availableGeometry().center()
        rect.moveCenter(center)
        msgBox.setGeometry(rect)
        msgBox.exec_()

    def startSocket(self):
        self.socket_thread = SocketIOThread(
            'https://kiosk-chat.musicen.com:8234', self.username)
        self.socket_thread.socketIdReceived.connect(self.handleSocketId)
        self.socket_thread.start()
        self.socket_thread.offerReceived.connect(self.handleOffer)
        self.socket_thread.multipleCallOfferReceived.connect(self.handleMultipleCallOffer)
        
        self.socket_thread.iceCandidateReceived.connect(
            lambda data: self.iceCandidatesQueue.append(data)
        )

    def userCloseWebview(self):
        self.isWebviewCloseByUser = True
        self.closeFullScreenWebView()
    def handleSocketId(self, socketId):
        self.socketId = socketId    

    def pollingCallback(self, response):
        try:
            response_dict = json.loads(response)
            data = response_dict.get('data', None)
            if data:
                print("Polling request data:", data)
                new_marquee_msg = data.get('marqueeMsg', '')
                self.webcam_widget.checkAndUpdateMarqueeText(new_marquee_msg)

                update_user_list = data.get('updateUserList', [])
                self.processUpdateUserList(update_user_list)

                delete_user_list_str = data.get('deleteUserListStr', [])
                self.processDeleteUserList(delete_user_list_str)

                delete_all_user_at = data.get('deleteAllUserAt', 'N')
                if delete_all_user_at == 'Y':
                    self.deleteAllUsers()

                media_file_download = data.get('mediaFileDownload', '')
                self.processMediaFileDownload(media_file_download)

                kiosk_status = data.get('kioskCtrlAt', 'N')
                if kiosk_status == 'K':
                    print("Kiosk status is 'K'. Exiting application.")
                    QApplication.quit()
                elif kiosk_status == 'R':
                    self.webcam_widget.releaseCamera()
                    print("Kiosk status is 'R'. Restarting application.")
                    QProcess.startDetached(sys.executable, sys.argv)
                    QApplication.quit()
            else:
                print("No data found in response")
        except json.JSONDecodeError:
            print("Failed to decode JSON response")

    def processMediaFileDownload(self, media_file_path):
        if media_file_path:
            url = f"http://newk.musicen.com{media_file_path}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                # Extract the filename from the Content-Disposition header
                if 'Content-Disposition' in response.headers:
                    content_disposition = response.headers['Content-Disposition']
                    file_name = content_disposition.split('filename=')[-1].strip('"')
                    print(f"Extracting file: {file_name}")  # Print the name of the zip file
                else:
                    print("Filename not found in the headers")
                    file_name = "default.zip"  # Fallback if the filename is not provided

                media_dir = os.path.join(self.base_path, 'ressources', 'media')
                if not os.path.exists(media_dir):
                    os.makedirs(media_dir)

                # Extract the zip file from the response content
                with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                    zip_ref.extractall(media_dir)

                print(f"Successfully extracted media file to {media_dir}")
            except requests.RequestException as e:
                print(f"Failed to download media file from {url}. Reason: {e}")
            except zipfile.BadZipFile as e:
                print(f"Failed to extract zip file from response content. Reason: {e}")

    def deleteAllUsers(self):
        base_path = os.path.join(os.getcwd(), 'utils', 'datasets', 'webcam_test', 'member')

        # Delete all folders in the member directory
        if os.path.exists(base_path):
            for user_dir in os.listdir(base_path):
                full_path = os.path.join(base_path, user_dir)
                try:
                    shutil.rmtree(full_path)
                    print(f'Successfully deleted directory: {full_path}')
                except Exception as e:
                    print(f'Failed to delete directory {full_path}. Reason: {e}')

        # Delete all users in the SQLite database
        connection = sqlite3.connect('kioskdb.db')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM users')
        connection.commit()
        connection.close()
        print('Successfully deleted all users from the database')


    def processUpdateUserList(self, update_user_list):
        base_path = os.path.join(os.getcwd(), 'utils', 'datasets', 'webcam_test', 'member')
        
        for user in update_user_list:
            user_seq = user.get('userSeq')
            user_nm = user.get('userNm')

            user_npz = user.get('userNpz')

            if user_seq and user_npz:
                user_dir = os.path.join(base_path, user_seq)
                
                if not os.path.exists(user_dir):
                    os.makedirs(user_dir)
                    connection = sqlite3.connect('kioskdb.db')
                    cursor = connection.cursor()
                    cursor.execute('INSERT INTO users (user_seq, user_nm) VALUES (?, ?)', (user_seq, user_nm))
                    connection.commit()
                    connection.close()

                else:
                    for filename in os.listdir(user_dir):
                        file_path = os.path.join(user_dir, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception as e:
                            print(f'Failed to delete {file_path}. Reason: {e}')
                try:
                    decoded_data = base64.b64decode(user_npz)
                    with zipfile.ZipFile(BytesIO(decoded_data), 'r') as zip_ref:
                        zip_ref.extractall(user_dir)
                        
                    extracted_items = os.listdir(user_dir)
                    if len(extracted_items) == 1 and os.path.isdir(os.path.join(user_dir, extracted_items[0])):
                        single_folder_path = os.path.join(user_dir, extracted_items[0])
                        for item in os.listdir(single_folder_path):
                            shutil.move(os.path.join(single_folder_path, item), user_dir)
                        shutil.rmtree(single_folder_path)

                except Exception as e:
                    print(f'Failed to extract data for user {user_seq}. Reason: {e}')

    def processDeleteUserList(self, delete_user_list_str):
        base_path = os.path.join(os.getcwd(), 'utils', 'datasets', 'webcam_test', 'member')
        
        for user_seq in delete_user_list_str:
            user_dir = os.path.join(base_path, user_seq)
            
            if os.path.exists(user_dir):
                try:
                    shutil.rmtree(user_dir)
                    connection = sqlite3.connect('kioskdb.db')
                    cursor = connection.cursor()
                    cursor.execute('DELETE FROM users WHERE user_seq = ?', (user_seq,))
                    connection.commit()
                    connection.close()
                    print(f'Successfully deleted directory for user: {user_seq}')
                except Exception as e:
                    print(f'Failed to delete directory for user {user_seq}. Reason: {e}')


    # def start_and_monitor_process(self, process_name):
    #         self.process = QProcess(self)
    #         self.process.finished.connect(self.on_process_finished)
    #         self.process.start(process_name)

    # def on_process_finished(self):
    #     print("WE CLOOOOOOOOOOOOOOOOOOOOOOSE")
        
    def initUI(self):
        self.check_existing_user()
        # self.start_and_monitor_process("gedit")
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
        self.username = os.getenv('USERNAME', 'default_username')
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
            self.base_path, 'ressources/media', 'default_media.mp4')
        self.video_player.setMedia(QMediaContent(
            QUrl.fromLocalFile(mp4_path)))
        self.video_player.mediaStatusChanged.connect(self.onMediaStatusChanged)
        self.video_player.play()

        self.web_view = QWebEngineView()

        self.configureWebEngineSettings()

        self.loadStyleSheet()
        self.addSlideMenu()

    def handleOffer(self, offerData):
        if self.isFullScreenWebViewOpen == False:
            if offerData.get("target") == self.username:
                reply = QMessageBox.question(
                    self, '전화', "누군가 자네를 부르고 있네", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QTimer.singleShot(
                        2000, lambda: self.openWebViewSignal.emit(offerData))

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
        self.multipleCallJsSent = False
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
            if not self.multipleCallJsSent:
                self.multipleCallJsSent = True
                jsCode = f"window.multipleCallFromPython({json.dumps(offerData)})"
                self.web_view.page().runJavaScript(jsCode)
        else:
            if self.isWebviewCloseByUser == False:
                self.closeFullScreenWebView()
                self.checkInternetPopup()

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
        self.web_view.setUrl(QUrl("about:blank"))
        self.web_view.setParent(None)
        self.web_view.hide() 
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
