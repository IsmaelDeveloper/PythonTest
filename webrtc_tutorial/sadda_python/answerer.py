import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer
import asyncio
import os
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from aiortc.contrib.media import MediaPlayer, MediaRecorder, MediaRelay
import pyaudio


class Answerer(QObject):
    SIGNALING_SERVER_URL = 'http://127.0.0.1:6969'
    ID = "answerer01"
    LOCAL_USERNAME = os.getenv("USERNAME", "default_user")
    offer_received = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sio = socketio.AsyncClient()
        self.peer_connection = RTCPeerConnection()
        self.setup_sio_events()
        self.setup_peer_connection_events()

    def setup_sio_events(self):
        @self.sio.event
        async def connect():
            print('connection established in answer')

        @self.sio.event
        async def disconnect():
            print('disconnected from server')

        @self.sio.event
        async def getOffer(data):
            if data["type"] == "offer" and data.get("target") == self.LOCAL_USERNAME:
                self.offer = data  # Stockez les données de l'offre pour une utilisation ultérieure
                self.offer_received.emit()

    def setup_peer_connection_events(self):
        @self.peer_connection.on("datachannel")
        def on_datachannel(channel):
            print(channel, "-", "created by remote party")
            channel.send("Hello From Answerer via RTC Datachannel")

            @channel.on("message")
            async def on_message(message):
                print("Received via RTC Datachannel: ", message)

            asyncio.ensure_future(self.send_pings(channel))

        @self.peer_connection.on("track")
        async def on_track(track):
            if track.kind == "audio":
                relay = MediaRelay()
                relayed_track = relay.subscribe(track)

                # Créez et configurez un flux PyAudio pour la lecture
                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paInt16,
                                channels=2,
                                rate=48000,
                                output=True)

                while True:
                    # Lire les données du track et les écrire dans le flux PyAudio
                    print('we are here')
                    frame = await relayed_track.recv()
                    print("frame :", frame)
                    data = frame.to_ndarray().tobytes()
                    stream.write(data)

    async def send_pings(self, channel):
        num = 0
        while True:
            msg = "From Answerer: {}".format(num)
            print("Sending via RTC Datachannel: ", msg)
            channel.send(msg)
            num += 1
            await asyncio.sleep(1)

    async def start(self):
        await self.sio.connect(self.SIGNALING_SERVER_URL)
        await self.sio.wait()

    async def handle_offer(self):
        if hasattr(self, 'offer'):
            rd = RTCSessionDescription(
                sdp=self.offer["sdp"], type=self.offer["type"])
            await self.peer_connection.setRemoteDescription(rd)
            await self.peer_connection.setLocalDescription(await self.peer_connection.createAnswer())

            answer = {"id": self.ID, "sdp": self.peer_connection.localDescription.sdp,
                      "type": self.peer_connection.localDescription.type}
            r = requests.post(self.SIGNALING_SERVER_URL +
                              '/answer', data=answer)


# Exemple d'utilisation
if __name__ == "__main__":
    answerer = Answerer()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(answerer.start())
