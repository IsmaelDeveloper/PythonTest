from PyQt5.QtWidgets import QSlider, QMessageBox, QSpacerItem, QSizePolicy, QTextBrowser, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui
from LocalParameterStorage import LocalParameterStorage
import markdown


class ToggleSwitch(QSlider):
    def __init__(self, parent=None, is_on=True):
        super().__init__(Qt.Horizontal, parent)
        self.setMinimum(0)
        self.setMaximum(1)
        self.setFixedSize(140, 30)
        if is_on:
            self.setValue(1)
        else:
            self.setValue(0)
        self.valueChanged.connect(self.updateStyle)
        self.updateStyle(self.value())

    def updateStyle(self, value):
        if value == 1:
            self.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 15px;
                    width: 80px;
                    margin: 0px;
                    border-radius: 5px;
                    background: #40FF2B;
                }
                QSlider::handle:horizontal {
                    background: white;
                    width: 25px;
                    border: 1px solid lightGray;
                    margin: -5px 0;
                    border-radius: 10px;
                    position: absolute;
                }
                QSlider::handle:horizontal:hover {
                    background: white;
                }
            """)
        else:
            self.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 15px;
                    width: 80px;
                    margin: 0px;
                    border-radius: 5px;
                    background: lightGray;
                }
                QSlider::handle:horizontal {
                    background: white; 
                    width: 25px;
                    margin: -5px 0;
                    border: 1px solid lightGray;
                    border-radius: 10px;
                    position: absolute;
                }
                QSlider::handle:horizontal:hover {
                    background: white;
                }
            """)

    def isOn(self):
        return self.value() == 1

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.value() == 0:
            self.setValue(1)
        else:
            self.setValue(0)


class TabBar(QtWidgets.QTabBar):
    def tabSizeHint(self, index):
        size = QtWidgets.QTabBar.tabSizeHint(self, index)
        size.transpose()
        size.setHeight(80)
        return size

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(TabBar(self))
        self.setTabPosition(QtWidgets.QTabWidget.West)


class ToolWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.loadStyleSheet()

    def initUI(self):
        self.parameter = LocalParameterStorage()
        self.parameterStorage = self.parameter.get_parameters()
        self.setObjectName("toolWindow")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 10, 0, 0)

        # Window Title
        self.windowTitle = QLabel("사용자 설정")
        self.windowTitle.setObjectName("ToolWindowTitle")
        main_layout.addWidget(
            self.windowTitle, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Tab Widget
        self.tabWidget = TabWidget()
        camera_tab_content = self.createCameraTabContent()
        screen_tab_content = self.createScreenTabContent()
        alarm_tab_content = self.createAlarmTabContent()
        management_tab_content = self.createManagementTabContent()
        license_tab_content = self.createLicenseTabContent()
        self.screen_tab_content = screen_tab_content
        self.tabWidget.addTab(camera_tab_content, QtGui.QIcon(
            "./ressources/images/camera.png"), "가메라")
        self.tabWidget.addTab(screen_tab_content, QtGui.QIcon(
            "./ressources/images/screen_30px.png"), "화면")
        self.tabWidget.addTab(alarm_tab_content, QtGui.QIcon(
            "./ressources/images/alarm.png"), "알림")
        self.tabWidget.addTab(management_tab_content, QtGui.QIcon(
            "./ressources/images/regi.png"), "관리 및 시스템")
        self.tabWidget.addTab(license_tab_content, QtGui.QIcon(
            "./ressources/images/open_source.png"), "오픈소스 라이센스")
        main_layout.addWidget(self.tabWidget)

        # Bottom Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 20, 20)
        buttons_layout.addStretch()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        save_button.setObjectName("saveButton")
        cancel_button.setObjectName("cancelButton")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        save_button.clicked.connect(self.onSaveClicked)
        cancel_button.clicked.connect(self.onCancelClicked)

        self.layout().addLayout(buttons_layout)

        # window
        self.setWindowTitle("Tool Window")
        self.setGeometry(300, 300, 800, 800)

    def onSaveClicked(self):
        # Créer le message d'alerte
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("저장 ?")
        msgBox.setText("저장 하시겠습니까 ?")
        msgBox.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        response = msgBox.exec_()

        # Vérifier la réponse de l'utilisateur
        if response == QMessageBox.Ok:
            # Récupérer les états des ToggleSwitch
            isDate = self.screen_tab_content.findChild(
                ToggleSwitch, "DateToggle").isOn()
            isName = self.screen_tab_content.findChild(
                ToggleSwitch, "NameToggle").isOn()
            isTemperature = self.screen_tab_content.findChild(
                ToggleSwitch, "TemperatureToggle").isOn()
            isHighTemperatureAlarm = self.tabWidget.findChild(
                ToggleSwitch, "HighTemperatureAlarmToggle").isOn()
            isMaskAlarm = self.tabWidget.findChild(
                ToggleSwitch, "MaskAlarmToggle").isOn()

            # Mettre à jour les paramètres
            new_params = {
                'isDate': isDate,
                'isName': isName,
                'isTemperature': isTemperature,
                'highTemperatureAlarm': isHighTemperatureAlarm,
                'isMaskAlarm': isMaskAlarm,
                'temperature': self.parameterStorage['temperature'],
                'movement': self.parameterStorage['movement'],
                'movementVertical': self.parameterStorage['movementVertical'],
                'width': self.parameterStorage['width'],
                'height': self.parameterStorage['height']
            }

            # Enregistrer les paramètres dans le localStorage
            self.parameter.save_parameters(new_params)

            mssgBoxDone = QMessageBox(self)
            mssgBoxDone.setWindowTitle("저장 완료")
            mssgBoxDone.setText("저장 하였습니다.")
            mssgBoxDone.setStandardButtons(QMessageBox.Ok)
            mssgBoxDone.setDefaultButton(QMessageBox.Ok)
            mssgBoxDone.exec_()

        else:
            print("Canceled")

    def onCancelClicked(self):
        print("Cancel clicked")
        self.close()

    def createCameraTabContent(self):
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        self.configureLayout(camera_layout, 10, 10, 10, 10)
        self.addControlPanel(camera_layout, "movement",
                             "좌우 이동 설정: ", "왼쪽", "오른쪽", -1, 1)
        self.addControlPanel(camera_layout, "movementVertical",
                             "상하 이동 설정: ", "위", "아래", -1, 1)
        self.addControlPanel(camera_layout, "width",
                             "너 설정: ", "늘이기", "줄이기", -1, 1)
        self.addControlPanel(camera_layout, "height",
                             "상하 높이 설정: ", "늘이기", "줄이기", -1, 1)

        return camera_container

    def addControlPanel(self, layout, param_key, label_text, btn_left_text, btn_right_text, decrement, increment):
        panel_widget = self.createPanelWidget("CameraPanel", 700, 60)
        panel_layout = QVBoxLayout(panel_widget)
        self.configureLayout(panel_layout, 10, 10, 10, 10)

        controlDiv = QHBoxLayout()
        controlLabel = QLabel(
            label_text + str(self.parameterStorage[param_key]))
        controlLabel.setObjectName(param_key + "Label")
        controlBtnLeft = QPushButton(btn_left_text)
        controlBtnLeft.clicked.connect(
            lambda: self.adjustParameter(param_key, decrement, label_text))
        controlBtnRight = QPushButton(btn_right_text)
        controlBtnRight.clicked.connect(
            lambda: self.adjustParameter(param_key, increment, label_text))
        controlDiv.addWidget(controlLabel)
        controlDiv.addWidget(controlBtnLeft)
        controlDiv.addWidget(controlBtnRight)
        panel_layout.addLayout(controlDiv)

        layout.addWidget(panel_widget, alignment=Qt.AlignHCenter)

    def adjustParameter(self, key, delta, label_text):
        self.parameterStorage[key] += delta
        self.updateLabel(key, label_text)

    def updateLabel(self, key, label_text):
        label = self.tabWidget.findChild(QLabel, key + "Label")
        label.setText(label_text + str(self.parameterStorage[key]))

    def createScreenTabContent(self):
        screen_container = QWidget()
        screen_layout = QVBoxLayout(screen_container)
        self.configureLayout(screen_layout, 10, 10, 10, 10)

        panel_widget = self.createPanelWidget("ScreenPanel", 700, 200)
        panel_layout = QVBoxLayout(panel_widget)
        self.configureLayout(panel_layout, 2, 10, 10, 10)

        screen_title = self.createLabel("검출 내용 표시", "ScreenTitle")
        panel_layout.addWidget(
            screen_title, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.addToggleSwitch(panel_layout, "날짜", "isDate", "DateToggle")
        self.addSpacer(panel_layout, 20, 10)
        self.addToggleSwitch(panel_layout, "이름", "isName", "NameToggle")
        self.addSpacer(panel_layout, 20, 10)
        self.addToggleSwitch(panel_layout, "온도",
                             "isTemperature", "TemperatureToggle")

        screen_layout.addWidget(panel_widget, alignment=Qt.AlignHCenter)
        return screen_container

    def addSpacer(self, layout, width, height):
        spacer = QSpacerItem(
            width, height, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addSpacerItem(spacer)

    def createAlarmTabContent(self):
        alarm_container = QWidget()
        alarm_layout = QVBoxLayout(alarm_container)
        self.configureLayout(alarm_layout, 10, 10, 10, 10)

        panel_widget = self.createPanelWidget("AlarmPanel", 700, 130)
        panel_layout = QVBoxLayout(panel_widget)
        self.configureLayout(panel_layout, 10, 10, 10, 10)

        panel_label = self.createLabel("메시지 수신 설정", "alarmTitle")
        panel_layout.addWidget(
            panel_label, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.addToggleSwitch(
            panel_layout, "고온자 수신", "highTemperatureAlarm", "HighTemperatureAlarmToggle")
        self.addToggleSwitch(panel_layout, "마스크 미착용자 수신",
                             "isMaskAlarm", "MaskAlarmToggle")

        alarm_layout.addWidget(panel_widget, alignment=Qt.AlignHCenter)

        panel_widget2 = self.createPanelWidget("AlarmPanel2", 700, 130)
        panel_layout2 = QVBoxLayout(panel_widget2)
        self.configureLayout(panel_layout2, 10, 10, 10, 10)

        temp_label_text = f"알림 온도 설정 {self.parameterStorage['temperature']} (최소 30 ~ 최대 50)"
        panel_label2 = self.createLabel(temp_label_text, "alarmTitle2")
        panel_layout2.addWidget(
            panel_label2, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.addTemperatureControlButtons(panel_layout2)

        alarm_layout.addWidget(panel_widget2, alignment=Qt.AlignHCenter)
        return alarm_container

    def configureLayout(self, layout, top, left, bottom, right):
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(left, top, right, bottom)

    def createPanelWidget(self, object_name, width, height):
        panel_widget = QWidget()
        panel_widget.setFixedSize(width, height)
        panel_widget.setObjectName(object_name)
        return panel_widget

    def createLabel(self, text, object_name):
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def addToggleSwitch(self, layout, label_text, parameter_key, object_name):
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(0)
        toggle_label = QLabel(label_text)
        toggle_label.setObjectName("ToggleLabel")
        toggle_layout.addWidget(toggle_label, alignment=Qt.AlignLeft)
        toggle_switch = ToggleSwitch(
            is_on=self.parameterStorage[parameter_key])
        toggle_switch.setObjectName(object_name)
        toggle_layout.addWidget(toggle_switch, alignment=Qt.AlignLeft)
        layout.addLayout(toggle_layout)

    def addTemperatureControlButtons(self, layout):
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(0)
        plus_button = QPushButton("+")
        minus_button = QPushButton("-")
        plus_button.setFixedWidth(70)
        minus_button.setFixedWidth(70)
        buttons_layout.addWidget(
            plus_button, alignment=Qt.AlignTop | Qt.AlignLeft)
        buttons_layout.addWidget(
            minus_button, alignment=Qt.AlignTop | Qt.AlignLeft)
        spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons_layout.addSpacerItem(spacer)
        plus_button.clicked.connect(self.increaseTemperature)
        minus_button.clicked.connect(self.decreaseTemperature)
        layout.addLayout(buttons_layout)

    def increaseTemperature(self):
        if self.parameterStorage['temperature'] < 50:
            self.parameterStorage['temperature'] += 0.5
            self.updateTemperatureLabel()

    def decreaseTemperature(self):
        if self.parameterStorage['temperature'] > 30:
            self.parameterStorage['temperature'] -= 0.5
            self.updateTemperatureLabel()

    def updateTemperatureLabel(self):
        label = self.tabWidget.findChild(QLabel, "alarmTitle2")
        label.setText(
            "알림 온도 설정 " + str(self.parameterStorage['temperature']) + " (최소 30 ~ 최대 50)")

    def createManagementTabContent(self):
        management_container = QWidget()
        management_layout = QVBoxLayout(management_container)
        management_layout.setAlignment(Qt.AlignTop)
        management_layout.setContentsMargins(
            10, 10, 10, 10)
        panel_widget = QWidget()
        panel_widget.setFixedSize(400, 100)
        panel_widget.setObjectName("ManagementPanel")

        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        settings_button = QPushButton("시스템 초기화")
        settings_button.setObjectName("InitializeButton")
        settings_button.clicked.connect(self.onInitializeClicked)
        panel_layout.addWidget(settings_button, alignment=Qt.AlignCenter)

        management_layout.addWidget(panel_widget, alignment=Qt.AlignHCenter)

        return management_container

    def onInitializeClicked(self):
        print("Initialize clicked")

    def createLicenseTabContent(self):
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)

        text_browser = QTextBrowser()
        markdown_content = self.loadMarkdownContent("./license_markdown.md")
        html_content = markdown.markdown(markdown_content)
        text_browser.setHtml(html_content)

        license_layout.addWidget(text_browser)
        return license_widget

    def loadMarkdownContent(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            return "The markdown file doesn't exist or couldn't be load"

    def loadStyleSheet(self):
        with open('tool.qss', 'r') as file:
            self.setStyleSheet(file.read())
