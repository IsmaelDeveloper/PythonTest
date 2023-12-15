from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt


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

        self.setWindowTitle("Tool Window")
        self.setGeometry(300, 300, 400, 300)

    def loadStyleSheet(self):
        with open('style.qss', 'r') as file:
            self.setStyleSheet(file.read())
