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

        # Ajouter deux faux onglets pour les icônes
        self.addTab("")
        self.addTab("")

    def paintEvent(self, event):
        super(CustomTabBar, self).paintEvent(event)
        painter = QPainter(self)

        # Dessiner la première icône
        firstIconTabRect = self.tabRect(self.count() - 2)
        firstIconRect = QRect(firstIconTabRect.x(),
                              firstIconTabRect.y(), 30, 30)
        self.firstIcon.paint(painter, firstIconRect)

        # Dessiner la seconde icône
        secondIconTabRect = self.tabRect(self.count() - 1)
        secondIconRect = QRect(secondIconTabRect.x(),
                               secondIconTabRect.y(), 30, 30)
        self.secondIcon.paint(painter, secondIconRect)

    def mousePressEvent(self, event):
        # Détecter les clics sur la première icône
        if self.tabRect(self.count() - 2).contains(event.pos()):
            self.firstIconClicked.emit()
            event.accept()  # Accepter l'événement pour empêcher le changement d'onglet
            return  # Ne pas appeler super.mousePressEvent

        # Détecter les clics sur la seconde icône
        if self.tabRect(self.count() - 1).contains(event.pos()):
            self.secondIconClicked.emit()
            event.accept()  # Accepter l'événement pour empêcher le changement d'onglet
            return  # Ne pas appeler super.mousePressEvent

        # Comportement par défaut pour les autres zones
        super(CustomTabBar, self).mousePressEvent(event)
