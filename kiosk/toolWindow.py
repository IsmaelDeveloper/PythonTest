from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui


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
        screen_widget = QWidget()
        screen_layout = QVBoxLayout(screen_widget)
        screen_layout.addWidget(QLabel("Screen settings..."))
        return screen_widget

    def createAlarmTabContent(self):
        alarm_widget = QWidget()
        alarm_layout = QVBoxLayout(alarm_widget)
        alarm_layout.addWidget(QLabel("Alarm settings..."))
        return alarm_widget

    def createManagementTabContent(self):
        management_widget = QWidget()
        management_layout = QVBoxLayout(management_widget)
        management_layout.addWidget(
            QLabel("Management and system settings..."))
        return management_widget

    def createLicenseTabContent(self):
        license_widget = QWidget()
        license_layout = QVBoxLayout(license_widget)
        license_layout.addWidget(QLabel("Open source licenses..."))
        return license_widget

    def loadStyleSheet(self):
        with open('tool.qss', 'r') as file:
            self.setStyleSheet(file.read())
