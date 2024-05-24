
import socketio
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QThread

class SocketIOThread(QThread):
    offerReceived = pyqtSignal(dict)
    iceCandidateReceived = pyqtSignal(dict)
    multipleCallOfferReceived = pyqtSignal(str)
    socketIdReceived = pyqtSignal(str)

    def __init__(self, url, username):
        QThread.__init__(self)
        self.url = url
        self.username = username
        self.socketId = None 
        self.sio = socketio.Client(ssl_verify=False)
    def run(self):

        @self.sio.event
        def connect():
            self.socketId = self.sio.eio.sid
            self.socketIdReceived.emit(self.socketId)
            print("Connected to server")
            self.sio.emit('register', {'username': self.username})
            self.sio.emit('usernm-client', self.username)

        @self.sio.event
        def disconnect():
            print("Disconnected from server")

        @self.sio.event
        def getOffer(data):
            self.offerReceived.emit(data)

        @self.sio.event
        def receiveCandidateInAnswer(data):
            self.iceCandidateReceived.emit(data)
        
        @self.sio.on('boom-server')
        def boom_server(UUID):
            self.multipleCallOfferReceived.emit(UUID)
            print("MULTIPLE CALL ")

        self.sio.connect(self.url)
        self.sio.wait()

    def reRegisterUser(self):
        if self.sio.connected:
            self.sio.emit('register', {'username': self.username})