import asyncio
import requests
import os
import socketio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer
from PyQt5.QtCore import QObject, pyqtSignal
import logging
ROOT = os.path.dirname(__file__)


class Offerer(QObject):
    SIGNALING_SERVER_URL = 'http://localhost:6969'
    ID = "offerer01"

    def __init__(self):
        super().__init__()
        logging.basicConfig(level=logging.DEBUG)
        self.sio = socketio.AsyncClient()
        self.peer_connection = RTCPeerConnection()
        self.channel = None
        self.setup_sio_events()
        self.setup_peer_connection()

    def setup_sio_events(self):
        @self.sio.event
        async def getAnswer(data):
            if data["type"] == "answer":
                rd = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
                await self.peer_connection.setRemoteDescription(rd)
                print("Answer received and set as Remote Description")

    def setup_peer_connection(self):
        self.channel = self.peer_connection.createDataChannel("chat")

        @self.channel.on("open")
        def on_open():
            print("channel openned")
            self.channel.send("Hello from Offerer via Datachannel")
            asyncio.ensure_future(self.send_pings(self.channel))

        @self.channel.on("message")
        def on_message(message):
            print("Received via RTC Datachannel", message)

    async def send_pings(self, channel):
        num = 0
        while True:
            msg = "From Offerer: {}".format(num)
            print("Sending via RTC Datachannel: ", msg)
            channel.send(msg)
            num += 1
            await asyncio.sleep(1)

    async def initialize_media(self):
        self.player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
        if self.player.audio:
            self.peer_connection.addTrack(self.player.audio)

    async def start(self):
        await self.initialize_media()
        await self.peer_connection.setLocalDescription(await self.peer_connection.createOffer())
        message = {"id": self.ID, "sdp": self.peer_connection.localDescription.sdp,
                   "type": self.peer_connection.localDescription.type, "target": os.getenv("TARGET_USERNAME", "default_target")}
        r = requests.post(self.SIGNALING_SERVER_URL + '/offer', data=message)

        await self.sio.connect(self.SIGNALING_SERVER_URL)
        await self.sio.wait()


# Exemple d'utilisation
if __name__ == "__main__":
    offerer = Offerer()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(offerer.start())
