import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget, QHBoxLayout

class Widget(QWidget):
    
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.textLabel = ["test1", "test2", "test3", "test4", "test5", "test6", "test7", "test8", "test9", "test10"]
        self.textWidget = "test test"
        self.text_widget = QLabel(self.textWidget)  # Définir comme attribut de classe

        menu_widget = QListWidget()
        for i in range(10):
            item = QListWidgetItem(f"Item {i}")
            item.setTextAlignment(Qt.AlignCenter)
            if i % 2 == 0:
                item.setBackground(Qt.blue)
            else:
                item.setBackground(Qt.red)
            menu_widget.addItem(item)

        menu_widget.currentItemChanged.connect(lambda item: self.update_text(menu_widget.currentRow()))

        button = QPushButton("Something")

        content_layout = QVBoxLayout()
        content_layout.addWidget(self.text_widget)
        content_layout.addWidget(button)
        main_widget = QWidget()
        main_widget.setLayout(content_layout)

        layout = QHBoxLayout()
        layout.addWidget(menu_widget, 1)
        layout.addWidget(main_widget, 4)
        self.setLayout(layout)
        
    def update_text(self, index):
        self.textWidget = self.textLabel[index]
        self.text_widget.setText(self.textWidget)

if __name__ == "__main__":
    app = QApplication([])

    w = Widget()
    w.showFullScreen()
    w.show()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    sys.exit(app.exec())
