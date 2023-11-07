import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QDialog, QLineEdit
from PySide6.QtCore import Slot


def _sayHello(input):
    print("Button clicked, Hello! "+ input.text())

app = QApplication(sys.argv)
input = QLineEdit("write here")
button = QPushButton("Click me")
button.clicked.connect(lambda: _sayHello(input))
dialog = QDialog()
dialog.setWindowTitle("Hello")
layout = QVBoxLayout()
layout.addWidget(input)
layout.addWidget(button)
dialog.setLayout(layout)
dialog.show()
sys.exit(app.exec())
