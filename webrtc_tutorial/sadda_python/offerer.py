import asyncio
import requests
import os
import socketio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, VideoStreamTrack, MediaStreamTrack
from aiortc.contrib.media import MediaRelay
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


class CustomVideoTrack(VideoStreamTrack):
    """
    A video stream track that generates frames from a custom source.
    """

    def __init__(self):
        super().__init__()
        self.camera = cv2.VideoCapture(0)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        # Générer ou récupérer une frame vidéo ici
        # Exemple : créer une image noire
        ret, frame = self.camera.read()
        if not ret:
            print("Erreur de capture de la webcam.")
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convertir la frame NumPy en VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame


class Offerer(QObject):
    SIGNALING_SERVER_URL = 'http://192.168.0.136:6969'
    ID = "offerer01"
    video_frame_received = pyqtSignal(np.ndarray)

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

        @self.channel.on("close")
        def on_close():
            print("channel closed")
            self.end_call()

        @self.peer_connection.on("track")
        async def on_track(track):
            asyncio.create_task(self.handle_video_track(track))

    async def handle_video_track(self, track: MediaStreamTrack):
        relay = MediaRelay()
        relayed_track = relay.subscribe(track)

        while True:
            print("try to get video frame in offer")
            frame = await relayed_track.recv()
            video_frame = frame.to_ndarray(
                format="bgr24")  # Convertir en ndarray
            self.video_frame_received.emit(video_frame)

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
        custom_video_track = CustomVideoTrack()
        self.peer_connection.addTrack(custom_video_track)

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
