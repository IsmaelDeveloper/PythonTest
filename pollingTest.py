import sys
import time
from PyQt5.QtCore import QTimer  # Import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel

class PollingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Polling page")
        self.setGeometry(100, 100, 400, 200)

        self.label = QLabel("state: waiting polling", self)
        self.button_start = QPushButton("Start polling", self)
        self.button_stop = QPushButton("Stop polling", self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button_start)
        layout.addWidget(self.button_stop)
        self.setLayout(layout)

        self.button_start.clicked.connect(self.startPolling)
        self.button_stop.clicked.connect(self.stopPolling)

        self.polling_active = False
        self.timer = QTimer(self)  # Create a QTimer instance

    def startPolling(self):
        if not self.polling_active:
            self.polling_active = True
            self.label.setText("State : Polling activated")
            self.timer.timeout.connect(self.poll)  # Connect the timer to the poll function
            self.timer.start(2000)  # Start the timer with a 2-second interval

    def stopPolling(self):
        if self.polling_active:
            self.polling_active = False
            self.label.setText("State : Polling stopped")
            self.timer.stop()  # Stop the timer

    def poll(self):
        if self.polling_active:
            print("Polling in process...")
            # Insert your code to test during polling here

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PollingPage()
    window.show()
    sys.exit(app.exec_())
