from PyQt5.QtCore import QUrl, QTimer, QJsonDocument
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
class PollingManager:
    def __init__(self, payload, url, interval, callback):
        self.payload = payload
        self.url = url
        self.interval = interval
        self.callback = callback
        self.timer = QTimer()
        self.timer.timeout.connect(self.sendRequest)
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handleResponse)

    def start(self):
        self.sendRequest()
        self.timer.start(self.interval)

    def sendRequest(self):
        request = QNetworkRequest(QUrl(self.url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        payload_bytes = QJsonDocument(self.payload).toJson()
        self.network_manager.post(request, payload_bytes)

    def handleResponse(self, reply):
        if reply.error():
            print(f"HTTP REQUEST ERROR :  {reply.errorString()}")
            response_data = None
        else:
            response_data = str(reply.readAll(), 'utf-8')
        
        if self.callback:  
            self.callback(response_data)