import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration, VideoStreamTrack
import asyncio
import os
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from aiortc.contrib.media import MediaPlayer, MediaRecorder, MediaRelay, MediaStreamTrack
import pyaudio
import numpy as np
import cv2
from av import VideoFrame
from rtc_utils import end_rtc_call


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

class Answerer(QObject):
    video_frame_received = pyqtSignal(np.ndarray)
    SIGNALING_SERVER_URL = 'http://192.168.0.136:6969'
    ID = "answerer01"
    LOCAL_USERNAME = os.getenv("USERNAME", "default_user")
    offer_received = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sio = socketio.AsyncClient()
        self.peer_connection = RTCPeerConnection(
            RTCConfiguration(iceServers=[RTCIceServer(
                urls=["stun:stun.l.google.com:19302"])])
        )
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

            @channel.on("close")
            def on_close():
                print("channel closed")
                self.end_call()

        @self.peer_connection.on("track")
        async def on_track(track):
            if track.kind == "video":
                asyncio.create_task(self.handle_video_track(track))
            elif track.kind == "audio":
                asyncio.create_task(self.handle_audio_track(track))

    async def handle_audio_track(self, track):
        relay = MediaRelay()
        relayed_track = relay.subscribe(track)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=2,
                        rate=48000, output=True, frames_per_buffer=960)

        while True:
            print("try to get audio frame")
            frame = await relayed_track.recv()
            print("Audio frame:", frame)
            data = frame.to_ndarray().tobytes()
            print("Length of data:", len(data))
            stream.write(data)

    async def handle_video_track(self, track: MediaStreamTrack):
        relay = MediaRelay()
        relayed_track = relay.subscribe(track)

        while True:
            print("try to get video frame")
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
            msg = "From Answerer: {}".format(num)
            print("Sending via RTC Datachannel: ", msg)
            channel.send(msg)
            num += 1
            await asyncio.sleep(1)

    async def start(self):
        await self.sio.connect(self.SIGNALING_SERVER_URL)
        await self.sio.wait()


    async def initialize_media(self):
        custom_video_track = CustomVideoTrack()
        self.peer_connection.addTrack(custom_video_track)

    async def handle_offer(self):
        if hasattr(self, 'offer'):
            rd = RTCSessionDescription(
                sdp=self.offer["sdp"], type=self.offer["type"])
            await self.peer_connection.setRemoteDescription(rd)
            await self.initialize_media()
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
