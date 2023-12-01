import socketio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration
import asyncio
import os
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from aiortc.contrib.media import MediaPlayer, MediaRecorder, MediaRelay, MediaStreamTrack
import pyaudio
import numpy as np
from rtc_utils import end_rtc_call


class AudioAnswerer(QObject):
    video_frame_received = pyqtSignal(np.ndarray)
    SIGNALING_SERVER_URL = 'http://127.0.0.1:6969'
    ID = "Audioanswerer01"
    LOCAL_USERNAME = os.getenv("USERNAME", "default_user")
    audio_offer_received = pyqtSignal()

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
            print('connection established in answer audio')

        @self.sio.event
        async def disconnect():
            print('disconnected from server')

        @self.sio.event
        async def getAudioOffer(data):
            print("Received audio offer")
            if data["type"] == "offer" and data.get("target") == self.LOCAL_USERNAME:
                print("Offer is for me")
                self.offer = data  # Stockez les données de l'offre pour une utilisation ultérieure
                self.audio_offer_received.emit()

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

    async def handle_offer(self):
        print("Handling audio offer")
        if hasattr(self, 'offer'):
            rd = RTCSessionDescription(
                sdp=self.offer["sdp"], type=self.offer["type"])
            await self.peer_connection.setRemoteDescription(rd)
            await self.peer_connection.setLocalDescription(await self.peer_connection.createAnswer())

            answer = {"id": self.ID, "sdp": self.peer_connection.localDescription.sdp,
                      "type": self.peer_connection.localDescription.type}
            r = requests.post(self.SIGNALING_SERVER_URL +
                              '/audioAnswer', data=answer)
            print("Answer sent : ", r)


# Exemple d'utilisation
if __name__ == "__main__":
    answerer = AudioAnswerer()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(answerer.start())
