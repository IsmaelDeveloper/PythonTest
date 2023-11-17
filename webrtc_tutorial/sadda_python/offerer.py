from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
import json
import asyncio
import requests
import os
import socketio

SIGNALING_SERVER_URL = 'http://localhost:6969'
ID = "offerer01"
sio = socketio.AsyncClient()


async def main():
    print("Starting")
    peer_connection = RTCPeerConnection()
    channel = peer_connection.createDataChannel("chat")

    async def send_pings(channel):
        num = 0
        while True:
            msg = "From Offerer: {}".format(num)
            print("Sending via RTC Datachannel: ", msg)
            channel.send(msg)
            num += 1
            await asyncio.sleep(1)

    @channel.on("open")
    def on_open():
        print("channel openned")
        channel.send("Hello from Offerer via Datachannel")
        asyncio.ensure_future(send_pings(channel))

    @channel.on("message")
    def on_message(message):
        print("Received via RTC Datachannel", message)

    @sio.event
    async def getAnswer(data):
        if data["type"] == "answer":
            rd = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
            await peer_connection.setRemoteDescription(rd)
            print("Answer received and set as Remote Description")

    # send offer
    await peer_connection.setLocalDescription(await peer_connection.createOffer())
    message = {"id": ID, "sdp": peer_connection.localDescription.sdp,
               "type": peer_connection.localDescription.type, "target": os.getenv("TARGET_USERNAME", "default_target")}
    r = requests.post(SIGNALING_SERVER_URL + '/offer', data=message)

    await sio.connect(SIGNALING_SERVER_URL)
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())
