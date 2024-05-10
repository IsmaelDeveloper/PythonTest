import { socket, rtcConfig } from "./config.js";

let saveButtonCounter = 0;
let isCalling = false;
let selectedUsers = [];
let mySocketId = null;
let localStream;
let webRtcPeers = {};
let socketIdListUsernm = [];
let webrtc_data_server_list = [];
window.multipleCallFromPython = multipleCallFromPython;
window.webrtcDataServerOn = webrtc_data_server_on;
export function attachSaveButtonEvent(saveButton, userName) {
  saveButton.dataset.isSelected = "false";

  saveButton.addEventListener("click", function () {
    socketIdListUsernm.forEach((item) => {
      if (item[1].userNm === userName) {
        addSelectedUser(item[0]);
      }
    });
    const isSelected = this.dataset.isSelected === "true";
    if (!isSelected && saveButtonCounter >= 4) {
      return;
    }

    this.dataset.isSelected = String(!isSelected);

    if (!isSelected) {
      this.style.backgroundColor = "red";
      saveButtonCounter += 1;
    } else {
      this.style.backgroundColor = "";
      saveButtonCounter -= 1;
    }

    const counterDisplay = document.getElementById("counter-display");
    counterDisplay.innerText = saveButtonCounter + " 개";
    console.log(selectedUsers);
  });
}

$(function () {
  myVwefew();
});

const myVwefew = async () => {
  localStream = await window.navigator.mediaDevices.getUserMedia({
    audio: true,
    video: true,
  });
};

const mySocket = socket;
//

mySocket.on("connect", () => {
  mySocketId = mySocket.id;
  console.log(mySocketId, "  :  mySocketId");

  const userNm =
    new URLSearchParams(window.location.search).get("username") ||
    uuid.v4().slice(0, 5);
  mySocket.emit("usernm-client", userNm);

  mySocket.on("msg-server", (msg) => {
    console.log("🚀 ~ mySocket.on ~ msg:", msg);
  });

  mySocket.on("users-server", (users) => {
    let str = "";
    console.log(users);
    socketIdListUsernm = [];
    Object.entries(users).forEach(([key, value]) => {
      socketIdListUsernm.push([key, value]);
      str += `
                  <li class="${key === mySocketId ? "my" : ""}">
                      <span>${key} : ${JSON.stringify(value)}</span>    
                      <button data-socketId="${key}" onclick="addSelectedUser('${key}')">눌러주세요</button>
                      >
                  </li>
              `;
    });
    // $("#users").html(str);
  });

  mySocket.on("webrtc-data-server", async (message) => {
    webrtc_data_server_on(message);
  });

  mySocket.on("boom-server", (roomUUID) => {
    if (isCalling == true) {
      boom_server(roomUUID);
    } else {
      displayGroupCallPopup(roomUUID);
    }
  });
});

async function webrtc_data_server_on(message) {
  if (isCalling) {
    await webrtc_data_server(message);
  } else {
    webrtc_data_server_list.push(message);
  }
}
async function displayGroupCallPopup(roomUUID) {
  const callPopup = document.getElementById("callPopup");
  callPopup.innerHTML = `<div class="callPopupContent"><p>그룹 콜 초대.</p>
      <button id="acceptGroupCall">수락하다</button>
      <button id="declineGroupCall">거절하다</button></div>`;
  callPopup.style.display = "block";

  const callingSound = document.getElementById("callingSound");
  callingSound.play();

  // accept call
  document.getElementById("acceptGroupCall").onclick = async function () {
    callPopup.style.display = "none";
    callingSound.pause();
    callingSound.currentTime = 0;
    isCalling = true;
    webrtc_data_server_list.forEach(async (message) => {
      await webrtc_data_server(message);
    });
    webrtc_data_server_list = [];
    boom_server(roomUUID);
  };

  //denied call
  document.getElementById("declineGroupCall").onclick = function () {
    callPopup.style.display = "none";
    callingSound.pause();
    callingSound.currentTime = 0;
    window.location.reload();
  };
}
async function webrtc_data_server(message) {
  const { rtcData, sender, receiver, msgType } = message;

  if (msgType === "offerSdp") {
    // const nowPeer = new RTCPeerConnection(rtcConfig);
    webRtcPeers[sender] = {
      peer: new RTCPeerConnection(rtcConfig),
      stream: null,
    };
    const nowPeer = webRtcPeers[sender].peer;

    nowPeer.addEventListener("icecandidate", (ev) => {
      const iceCandidate = ev.candidate;
      if (!iceCandidate) return;

      mySocket.emit("webrtc-data-client", {
        sender: mySocketId,
        receiver: sender,
        msgType: "iceCandidate",
        rtcData: iceCandidate,
      });
    });

    nowPeer.addEventListener("track", (event) => {
      const [remoteStream] = event.streams;
      webRtcPeers[sender].stream = remoteStream;

      addVideoStreamFromPeers();
    });

    const remoteSdp = new RTCSessionDescription(rtcData);
    nowPeer.setRemoteDescription(remoteSdp);

    localStream.getTracks().forEach((track) => {
      nowPeer.addTrack(track, localStream);
    });

    const answerSdp = await nowPeer.createAnswer();
    nowPeer.setLocalDescription(answerSdp);

    mySocket.emit("webrtc-data-client", {
      sender: mySocketId,
      receiver: sender,
      msgType: "answerSdp",
      rtcData: answerSdp,
    });
  } else if (msgType === "answerSdp") {
    //
    const sdp = new RTCSessionDescription(rtcData);
    console.log("sender : ", sender);
    console.log("webRtcPeers : ", webRtcPeers);
    webRtcPeers[sender].peer.setRemoteDescription(sdp);
  } else if (msgType === "iceCandidate") {
    //

    console.log("sender 2 : ", sender);
    console.log("webRtcPeers 2 : ", webRtcPeers);
    const newCandi = new RTCIceCandidate(rtcData);
    webRtcPeers[sender].peer.addIceCandidate(newCandi);
  }
}
async function multipleCallFromPython(roomUUID) {
  displayGroupCallPopup(roomUUID);
}
async function boom_server(roomUUID) {
  mySocket.emit("get-room-participants", { roomUUID });
  mySocket.on("room-participants", async (data) => {
    const { participants } = data;

    const targetUsers = participants.filter(
      (socketId) => socketId !== mySocketId
    );
    mySocket.emit("join-room", { roomUUID });

    console.log("🚀 ~ mySocket.on ~ targetUsers:", targetUsers);

    targetUsers.forEach(async (targetUserSocketId) => {
      // const peerConnection = new RTCPeerConnection(rtcConfig);
      webRtcPeers[targetUserSocketId] = {
        peer: new RTCPeerConnection(rtcConfig),
        stream: null,
      };

      const currentPeer = webRtcPeers[targetUserSocketId].peer;
      currentPeer.addEventListener("icecandidate", (ev) => {
        if (!ev.candidate) return;

        mySocket.emit("webrtc-data-client", {
          sender: mySocketId,
          receiver: targetUserSocketId,
          msgType: "iceCandidate",
          rtcData: event.candidate,
        });
      });
      currentPeer.addEventListener("track", (event) => {
        webRtcPeers[targetUserSocketId].stream = event.streams[0];

        addVideoStreamFromPeers();
      });

      localStream.getTracks().forEach((track) => {
        currentPeer.addTrack(track, localStream);
      });

      // debugger
      const offerSdp = await currentPeer.createOffer();
      currentPeer.setLocalDescription(offerSdp);

      mySocket.emit("webrtc-data-client", {
        sender: mySocketId,
        receiver: targetUserSocketId,
        msgType: "offerSdp",
        rtcData: offerSdp,
      });
    });
  });
}
function getUserNameBySocketId(socketId) {
  const user = socketIdListUsernm.find((item) => item[0] === socketId);
  return user ? user[1].userNm : "Unknown User"; // Retourne 'Unknown User' si non trouvé
}

function openMultipleCallWindow() {
  let container = document.getElementById("groupCallVideoContainer");
  if (!container.style.display || container.style.display === "none") {
    container.style.display = "block";
  }
}

function addVideoStreamFromPeers() {
  openMultipleCallWindow();
  const videoContainer = document.getElementById("videos");
  const audioContainer = document.getElementById("groupCallVideoContainer");

  let str = "";
  document.getElementById("videos").innerHTML = "";
  const audioElements = document
    .getElementById("groupCallVideoContainer")
    .getElementsByTagName("audio");
  while (audioElements[0]) {
    audioElements[0].parentNode.removeChild(audioElements[0]);
  }

  console.log(webRtcPeers, "  :   webRtcPeers");
  Object.entries(webRtcPeers).forEach(([socketId, peer]) => {
    const username = getUserNameBySocketId(socketId);
    if (peer.stream) {
      peer.stream.getTracks().forEach((track) => {
        if (track.kind === "video") {
          const videoWrap = document.createElement("div");
          videoWrap.classList.add("video-wrap");

          console.log("video of : ", username);
          let videoElement = document.createElement("video");
          videoElement.srcObject = new MediaStream([track]);
          videoElement.autoplay = true;
          videoElement.playsInline = true;
          videoElement.classList.add("remote-video");

          const userNameLabel = document.createElement("div");
          userNameLabel.classList.add("user-label");
          userNameLabel.textContent = username;
          videoContainer.appendChild(videoElement);
          videoWrap.appendChild(videoElement);
          videoWrap.appendChild(userNameLabel);
          videoContainer.appendChild(videoWrap);
        } else if (track.kind === "audio") {
          let audioElement = document.createElement("audio");
          audioElement.srcObject = new MediaStream([track]);
          audioElement.autoplay = true;
          audioContainer.appendChild(audioElement);
        }
      });
    }
  });
}

function allBoom() {
  mySocket.emit("boom-client", [...selectedUsers, mySocketId]);
}

function addSelectedUser(socketId) {
  if (socketId === mySocketId) {
    return;
  }

  if (selectedUsers.includes(socketId)) {
    selectedUsers = selectedUsers.filter((id) => id !== socketId);
  } else {
    selectedUsers.push(socketId);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("all-call-button")
    .addEventListener("click", function () {
      isCalling = true;
      allBoom();
    });
  document.getElementById("closeGroupCall").onclick = function () {
    window.location.reload();
  };
});
