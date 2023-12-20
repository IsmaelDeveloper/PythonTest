import sys
from PyQt5.QtWidgets import QTabBar
from PyQt5.QtCore import pyqtSignal, QRect

from PyQt5.QtGui import QIcon, QPainter


class CustomTabBar(QTabBar):
    firstIconClicked = pyqtSignal()
    secondIconClicked = pyqtSignal()

    def __init__(self, parent=None):
        super(CustomTabBar, self).__init__(parent)
        self.firstIcon = QIcon("./ressources/images/configure-dark.png")
        self.secondIcon = QIcon("./ressources/images/refresh.png")

        # Add fake tabs to reserve space for the icons
        self.addTab("")
        self.addTab("")

    def paintEvent(self, event):
        super(CustomTabBar, self).paintEvent(event)
        painter = QPainter(self)

        # draw first icon
        firstIconTabRect = self.tabRect(self.count() - 2)
        firstIconRect = QRect(firstIconTabRect.x(),
                              firstIconTabRect.y(), 30, 30)
        self.firstIcon.paint(painter, firstIconRect)

        # Draw second icons
        secondIconTabRect = self.tabRect(self.count() - 1)
        secondIconRect = QRect(secondIconTabRect.x(),
                               secondIconTabRect.y(), 30, 30)
        self.secondIcon.paint(painter, secondIconRect)

    def mousePressEvent(self, event):
        # detect click on the first icon
        if self.tabRect(self.count() - 2).contains(event.pos()):
            self.firstIconClicked.emit()
            event.accept()  # accept event for not switching tab
            return  # dont call super.mousePressEvent

        # detect click on the second icon
        if self.tabRect(self.count() - 1).contains(event.pos()):
            self.secondIconClicked.emit()
            event.accept()  # accept event for not switching tab
            return  # dont call super.mousePressEvent

        # default comportement for other tabs
        super(CustomTabBar, self).mousePressEvent(event)
