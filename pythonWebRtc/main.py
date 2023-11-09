import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
import socketio
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription
import requests
import os
import logging
from aiortc.contrib.media import MediaPlayer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import numpy as np
import pyaudio
from aiortc.contrib.media import MediaStreamTrack
import asyncio
from aiortc import MediaStreamTrack
from aiortc.contrib.media import MediaPlayer


class CustomAudioTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.audio.recv()
        return frame


class CustomVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        print("recv execute")
        frame = await self.track.video.recv()
        return frame


class MainWindow(QWidget):
    user_signal = pyqtSignal(dict)
    user_signal_delete = pyqtSignal(str)
    icecandidate_signal = pyqtSignal(object)
    sdp_offer_received = pyqtSignal(object)
    sdp_answer = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        logging.basicConfig(level=logging.DEBUG)
        self.init_ui()
        self.sio = socketio.Client()
        self.sio.connect('http://localhost:5000')
        self.local_audio = None

        self.local_video = None

        configuration = RTCConfiguration(iceServers=[
            RTCIceServer(urls="stun:stun.l.google.com:19302")
        ])
        self.pc = RTCPeerConnection(configuration)
        self.pc.on('track', self.handle_track)
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

    def init_media_players(self):
        if not self.local_audio:
            self.local_audio = MediaPlayer(
                'audio=마이크 배열 (Realtek(R) Audio)', format='dshow', options={'rtbufsize': '70200000'})
        if not self.local_video:
            self.local_video = MediaPlayer(
                'video=Integrated Camera',
                format='dshow',
                options={
                    'framerate': '30',
                    'video_size': '320x240',
                    'rtbufsize': '2048M'
                }
            )
        self.custom_audio_track = CustomAudioTrack(self.local_audio)
        self.custom_video_track = CustomVideoTrack(self.local_video)

    async def handle_track(self, track: MediaStreamTrack):
        print("Track received", track.kind)
        print("Track state", track.readyState)
        if track.kind == 'audio':
            print("audio track received 1")
            # Configure PyAudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=48000,
                            output=True)

            # Play audio stream
            while True:
                print("audio track received 2")
                frame = await track.recv()
                print("audio track received 3")
                data = frame.to_bytes()
                stream.write(data)
        if track.kind == 'video':
            while True:
                print("video track received 1")
                try:
                    frame = await track.recv()
                    print("video track received 2")
                except:
                    print("Videoerror")
                # convert frame to numpy format
                image = frame.to_ndarray(format="bgr24")
                print("video track received 3")

                # convert numpy  to QImage
                h, w, ch = image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(
                    image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                # can adjust size of displayed image here
                p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)

                # conver Qimage to pixmap to display
                pixmap = QPixmap.fromImage(p)
                self.video_label.setPixmap(pixmap)
                self.update_video_label(pixmap)
                print("video track received 4")

    def update_video_label(self, pixmap):
        QTimer.singleShot(0, lambda: self.video_label.setPixmap(pixmap))

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
          #  self.sio.emit('ice-candidate', candidate_dict)

        elif not candidate:
            print("All ICE candidates have been generated")

    def init_ui(self):
        self.setWindowTitle('Communicationwith signal server')
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.video_label = QLabel()
        self.layout.addWidget(self.video_label)
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
        username = os.getenv('USER_NAME', 'undefined')
        if data["userReceiveCall"] != username:
            return
        reply = QMessageBox.question(self, 'Call', data["userInitiateCall"] + " is calling you",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.handle_sdp_offer_received(data))
        else:
            print("User reject the call")

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
        # self.init_media_players()
        # if not self.pc.getSenders():
        #     self.pc.addTrack(self.custom_audio_track)
        #     self.pc.addTrack(self.custom_video_track)
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
    main_window.showFullScreen()
    main_window.show()
    sys.exit(app.exec_())
