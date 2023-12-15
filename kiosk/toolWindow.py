from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui


class TabBar(QtWidgets.QTabBar):
    def tabSizeHint(self, index):
        s = QtWidgets.QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

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
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 20, 0, 0)

        self.windowTitle = QLabel("사용자 설정")
        self.windowTitle.setObjectName("ToolWindowTitle")

        main_layout.addWidget(
            self.windowTitle, alignment=Qt.AlignTop | Qt.AlignHCenter)

        self.tabWidget = TabWidget()
        self.tabWidget.addTab(QtWidgets.QWidget(), QtGui.QIcon(
            "./ressources/images/camera.png"), "가메라")
        self.tabWidget.addTab(QtWidgets.QWidget(), QtGui.QIcon(
            "./ressources/images/screen_30px.png"), "화면")
        self.tabWidget.addTab(QtWidgets.QWidget(), QtGui.QIcon(
            "./ressources/images/alarm.png"), "알림")
        self.tabWidget.addTab(QtWidgets.QWidget(), QtGui.QIcon(
            "./ressources/images/regi.png"), "관리 및 시스템")
        self.tabWidget.addTab(QtWidgets.QWidget(), QtGui.QIcon(
            "./ressources/images/open_source.png"), "오픈소스 라이센스")

        main_layout.addWidget(self.tabWidget)

        self.setWindowTitle("Tool Window")
        self.setGeometry(300, 300, 800, 800)

    def loadStyleSheet(self):
        with open('style.qss', 'r') as file:
            self.setStyleSheet(file.read())
