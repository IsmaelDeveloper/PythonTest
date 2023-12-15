from PyQt5.QtWidgets import QSlider, QSpacerItem, QSizePolicy, QTextBrowser, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui
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


class ProxyStyle(QtWidgets.QProxyStyle):
    def drawControl(self, element, opt, painter, widget):
        if element == QtWidgets.QStyle.CE_TabBarTabLabel:
            ic = self.pixelMetric(QtWidgets.QStyle.PM_TabBarIconSize)
            r = QtCore.QRect(opt.rect)
            w = 0 if opt.icon.isNull() else opt.rect.width() + \
                self.pixelMetric(QtWidgets.QStyle.PM_TabBarIconSize)
            r.setHeight(opt.fontMetrics.width(opt.text) + w)
            r.moveBottom(opt.rect.bottom())
            opt.rect = r
        QtWidgets.QProxyStyle.drawControl(self, element, opt, painter, widget)


class ToolWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.loadStyleSheet()

    def initUI(self):
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
        print("Save clicked")

    def onCancelClicked(self):
        print("Cancel clicked")
        self.close()

    def createCameraTabContent(self):
        camera_widget = QWidget()
        camera_layout = QVBoxLayout(camera_widget)
        camera_layout.addWidget(QLabel("Camera settings..."))
        return camera_widget

    def createScreenTabContent(self):
        screen_container = QWidget()
        screen_layout = QVBoxLayout(screen_container)
        screen_layout.setAlignment(Qt.AlignTop)
        screen_layout.setContentsMargins(10, 10, 10, 10)

        panel_widget = QWidget()
        panel_widget.setFixedSize(700, 200)
        panel_widget.setObjectName("ScreenPanel")
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(2, 10, 10, 10)

        screen_title = QLabel("검출 내용 표시")
        screen_title.setObjectName("ScreenTitle")
        panel_layout.addWidget(
            screen_title, alignment=Qt.AlignLeft | Qt.AlignTop)

        # layoun for 날짜
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(0)
        toggle_label = QLabel("날짜")
        toggle_label.setObjectName("ToggleLabel")
        toggle_layout.addWidget(toggle_label, alignment=Qt.AlignLeft)
        toggle_switch = ToggleSwitch(is_on=False)
        toggle_layout.addWidget(toggle_switch, alignment=Qt.AlignLeft)
        panel_layout.addLayout(toggle_layout)

        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        panel_layout.addSpacerItem(spacer)

        # layout for 이름
        toggle_layout2 = QHBoxLayout()
        toggle_layout2.setSpacing(0)
        toggle_label2 = QLabel("이름")
        toggle_label2.setObjectName("ToggleLabel")
        toggle_layout2.addWidget(toggle_label2, alignment=Qt.AlignLeft)
        toggle_switch2 = ToggleSwitch(is_on=False)
        toggle_layout2.addWidget(toggle_switch2, alignment=Qt.AlignLeft)
        panel_layout.addLayout(toggle_layout2)

        spacer2 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        panel_layout.addSpacerItem(spacer2)

        # layout for 온도
        toggle_layout3 = QHBoxLayout()
        toggle_layout3.setSpacing(0)
        toggle_label3 = QLabel("온도")
        toggle_label3.setObjectName("ToggleLabel")
        toggle_layout3.addWidget(toggle_label3, alignment=Qt.AlignLeft)
        toggle_switch3 = ToggleSwitch(is_on=False)
        toggle_layout3.addWidget(toggle_switch3, alignment=Qt.AlignLeft)
        panel_layout.addLayout(toggle_layout3)

        screen_layout.addWidget(panel_widget, alignment=Qt.AlignHCenter)

        return screen_container

    def createAlarmTabContent(self):
        alarm_widget = QWidget()
        alarm_layout = QVBoxLayout(alarm_widget)
        alarm_layout.addWidget(QLabel("Alarm settings..."))
        return alarm_widget

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
