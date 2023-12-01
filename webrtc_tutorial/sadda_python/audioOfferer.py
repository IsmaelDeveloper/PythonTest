import asyncio
import requests
import os
import socketio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, VideoStreamTrack, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer
from PyQt5.QtCore import QObject, pyqtSignal
import logging
from av import VideoFrame
from av.audio.frame import AudioFrame
import av
import numpy as np
import cv2
import sounddevice as sd
import pyaudio
from rtc_utils import end_rtc_call
from fractions import Fraction

ROOT = os.path.dirname(__file__)


class CustomAudioTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, rate=48000, channels=2):
        super().__init__()
        self.rate = rate
        self.channels = channels
        self._timestamp = 0

        # Initialiser PyAudio
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt16,
                                   channels=2,
                                   rate=48000,
                                   input=True,
                                   frames_per_buffer=960)

    async def recv(self):
        frames_per_buffer = 960

        # Lire les données du stream PyAudio
        data = np.frombuffer(self.stream.read(
            frames_per_buffer), dtype=np.int16)
        data = data.reshape(-1, 1)

        self._timestamp += frames_per_buffer
        pts = self._timestamp
        time_base = Fraction(1, self.rate)
        # Préparation des données pour PyAV
        audio_frame = av.AudioFrame.from_ndarray(
            data.T, format='s16', layout='stereo')
        audio_frame.sample_rate = self.rate
        audio_frame.pts = pts
        audio_frame.time_base = time_base

        return audio_frame

    def __del__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()


class AudioOfferer(QObject):
    SIGNALING_SERVER_URL = 'http://localhost:6969'
    ID = "Audioofferer01"

    def __init__(self):
        super().__init__()
        logging.basicConfig(level=logging.DEBUG)
        self.sio = socketio.AsyncClient()
        self.peer_connection = RTCPeerConnection(
            RTCConfiguration(iceServers=[RTCIceServer(
                urls=["stun:stun.l.google.com:19302"])])
        )
        self.channel = None
        self.setup_sio_events()
        self.setup_peer_connection()

    def setup_sio_events(self):
        @self.sio.event
        async def getAudioAnswer(data):
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

        @self.channel.on("close")
        def on_close():
            print("channel closed")
            self.end_call()

    def end_call(self):
        asyncio.run_coroutine_threadsafe(
            end_rtc_call(self.peer_connection), asyncio.get_event_loop())

    async def send_pings(self, channel):
        num = 0
        while True:
            msg = "From Offerer: {}".format(num)
            print("Sending via RTC Datachannel: ", msg)
            channel.send(msg)
            num += 1
            await asyncio.sleep(1)

    async def initialize_media(self):
        custom_audio_track = CustomAudioTrack()
        self.peer_connection.addTrack(custom_audio_track)

    async def start(self):
        await self.initialize_media()
        await self.peer_connection.setLocalDescription(await self.peer_connection.createOffer())
        message = {"id": self.ID, "sdp": self.peer_connection.localDescription.sdp,
                   "type": self.peer_connection.localDescription.type, "target": os.getenv("TARGET_USERNAME", "default_target")}
        r = requests.post(self.SIGNALING_SERVER_URL +
                          '/audioOffer', data=message)
        await self.sio.connect(self.SIGNALING_SERVER_URL)
        await self.sio.wait()


# Exemple d'utilisation
if __name__ == "__main__":
    offerer = AudioOfferer()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(offerer.start())
