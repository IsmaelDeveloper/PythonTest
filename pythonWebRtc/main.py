import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal
import socketio
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription
import requests
import os
import logging


class MainWindow(QWidget):
    user_signal = pyqtSignal(dict)
    user_signal_delete = pyqtSignal(str)
    icecandidate_signal = pyqtSignal(object)
    sdp_offer_received = pyqtSignal(object)
    sdp_answer = pyqtSignal(object)


# {
# "urls": [
# "turn:13.250.13.83:3478?transport=udp"
# ],
# "username": "YzYNCouZM1mhqhmseWk6",
# "credential": "YzYNCouZM1mhqhmseWk6"
# }


    def __init__(self):
        super().__init__()
        logging.basicConfig(level=logging.DEBUG)
        self.init_ui()
        self.sio = socketio.Client()
        self.sio.connect('http://localhost:5000')
        configuration = RTCConfiguration(iceServers=[
            RTCIceServer(urls="stun:stun.l.google.com:19302"),
            # RTCIceServer(urls="turn:13.250.13.83:3478?transport=udp",
            #            username="YzYNCouZM1mhqhmseWk6",
            #           credential="YzYNCouZM1mhqhmseWk6")
            #    RTCIceServer("turn:numb.viagenie.ca", "webrtc@live.com", "muazkh"),
            #     RTCIceServer("stun:stun.l.google.com:19302")
            #    RTCIceServer("stun:freestun.net:3478")

        ])
        self.pc = RTCPeerConnection(configuration)
        self.pc.on('icecandidate', self.emit_icecandidate_signal)
        self.pc.on('connectionstatechange', self.on_connection_state_change)
        self.data_channel = self.pc.createDataChannel("dataChannel")
        self.generated_candidate = None
        self.candidate_buttons = {}
        self.load_existing_users()
        self.sio.on('users', self.emit_user_signal)
        self.sio.on('users-delete', self.emit_user_signal_delete)
        self.sio.on('sdp-offer-received', self.emit_sdp_offer_received)
        self.sio.on('sdp-answer', self.emit_sdp_answer)
        # $env:USER_NAME="ismael2"; python ./main.py for set env variable in windows
        self.sio.emit('user', {
            "user": os.getenv('USER_NAME', 'undefined')
        })
        self.sio.emit('set-username',
                      {'username': os.getenv('USER_NAME', 'undefined')})

    def start_offer_generation(self):
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.create_offer())

    def on_connection_state_change(self):
        print(f'Connection state changed: {self.pc.connectionState}')

    def on_ice_candidate(self, candidate):
        print("on Ice candidate here")
        if candidate and not self.generated_candidate:
            self.generated_candidate = candidate
            candidate_dict = {
                'candidate': candidate.candidate,
                'sdpMid': candidate.sdpMid,
                'sdpMLineIndex': candidate.sdpMLineIndex
            }
            print(candidate_dict)
            # send Ice candidate to server
            self.sio.emit('ice-candidate', candidate_dict)

        elif not candidate:
            print("All ICE candidates have been generated")

    def init_ui(self):
        self.setWindowTitle('Communicationwith signal server')
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.setLayout(self.layout)
        self.user_signal.connect(self.handle_user)
        self.user_signal_delete.connect(self.handle_user_delete)
        self.icecandidate_signal.connect(self.on_ice_candidate)
        self.sdp_offer_received.connect(self.start_sdp_offer_received)
        self.sdp_answer.connect(self.start_sdp_answer)

    def start_sdp_answer(self, data):
        import asyncio
        username = os.getenv('USER_NAME', 'undefined')
        if data["userInitiateCall"] != username:
            return
        print("SDP answer received", data)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.handle_sdp_answer(data))

    async def handle_sdp_answer(self, data):
        username = os.getenv('USER_NAME', 'undefined')
        if data["userInitiateCall"] != username:
            return
        answer = RTCSessionDescription(
            sdp=data['answer']['sdp'], type=data['answer']['type'])
        await self.pc.setRemoteDescription(answer)
        print("Remote description set with answer")

    def start_sdp_offer_received(self, data):
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.handle_sdp_offer_received(data))

    async def handle_sdp_offer_received(self, data):
        username = os.getenv('USER_NAME', 'undefined')
        if data["userReceiveCall"] != username:
            return
        print("SDP offer received", data['offer'])
        offer = RTCSessionDescription(
            sdp=data['offer']['sdp'], type=data['offer']['type'])

        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        print(answer, "Answer created")
        answer_dict = {"sdp": answer.sdp, "type": answer.type}
        self.sio.emit(
            'sdp-answer', {"answer": answer_dict, "userReceiveCall": data["userReceiveCall"], "userInitiateCall": data["userInitiateCall"]})

    def emit_user_signal(self, data):
        self.user_signal.emit(data)

    def emit_user_signal_delete(self, data):
        self.user_signal_delete.emit(data)

    def emit_sdp_offer_received(self, data):
        self.sdp_offer_received.emit(data)

    def emit_sdp_answer(self, data):
        self.sdp_answer.emit(data)

    def emit_icecandidate_signal(self, data):
        self.icecandidate_signal.emit(data)

    def load_existing_users(self):
        response = requests.get('http://localhost:3000/get-user')
        if response.status_code == 200:
            existing_candidates = response.json()
            print(existing_candidates)
            for candidate_data in existing_candidates:
                self.handle_user(candidate_data)
        else:
            print(
                f'Failed to load existing ICE candidates: {response.status_code}')

    def handle_user(self, data):
        username = os.getenv('USER_NAME', 'undefined')
        if data["user"] == username:
            return
        candidate_button = QPushButton(f'{data["user"]}')
        candidate_button.clicked.connect(lambda: self.start_create_offer(data))
        list_item = QListWidgetItem()
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, candidate_button)
        self.candidate_buttons[candidate_button] = data

    def handle_user_delete(self, data):
        button_to_remove = None
        list_item_to_remove = None

        # find btn to delete
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            button = self.list_widget.itemWidget(list_item)
            if button.text() == data:
                button_to_remove = button
                list_item_to_remove = list_item
                break

        # delete item btn from list
        if button_to_remove and list_item_to_remove:
            # take off btn from list
            row = self.list_widget.row(list_item_to_remove)
            self.list_widget.takeItem(row)
            # take off entry btn
            del self.candidate_buttons[button_to_remove]

    async def create_offer(self, data):
        print("Creating offer...", data)
        username = os.getenv('USER_NAME', 'undefined')

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        print(offer)
        self.sio.emit(
            'sdp-offer', {"offer": {'sdp': offer.sdp, 'type': offer.type}, "userInitiateCall": username, "userReceiveCall": data["user"]},)
        print("Offer created")

    def start_create_offer(self, data):
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.create_offer(data))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
