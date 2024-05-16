import { socket, rtcConfig } from "./config.js";

let saveButtonCounter = 0;
let isCalling = false;
let selectedUsers = [];
let mySocketId = null;
let localStream;
let webRtcPeers = {};
let socketIdListUsernm = [];
let webrtc_data_server_list = [];
let currentRoomUUID = null;
window.multipleCallFromPython = multipleCallFromPython;
window.webrtcDataServerOn = webrtc_data_server_on;
const mySocket = socket;

export function attachSaveButtonEvent(saveButton, userName) {
  saveButton.dataset.isSelected = "false";

  saveButton.addEventListener("click", function () {
    const isSelected = this.dataset.isSelected === "true";
    if (!isSelected && saveButtonCounter >= 4) {
      return;
    }
    socketIdListUsernm.forEach((item) => {
      if (item[1].userNm === userName) {
        addSelectedUser(item[0]);
      }
    });
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
export function deleteSelectedUsers() {
  console.log("deleteSelectedUsers");
  selectedUsers = [];
}

$(document).ready(function () {
  $(".webview_close_btn").on("click", function () {
    location.href = "closewebview://?";
  });
});
$(function () {
  myVwefew();
});

const myVwefew = async () => {
  localStream = await window.navigator.mediaDevices.getUserMedia({
    audio: true,
    video: true,
  });
};

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
  mySocket.on("user-left", (data) => {
    console.log("data in user-left", data);
    const { socketId } = data;
    const userName = getUserNameBySocketId(socketId);
    if (webRtcPeers[socketId]) {
      webRtcPeers[socketId].peer.close();
      delete webRtcPeers[socketId];
    }
    removeVideoStream(socketId, userName);
    checkAndRefreshPage();
  });
});

function checkAndRefreshPage() {
  const videoContainer = document.getElementById("videos");
  if (videoContainer.children.length === 1) {
    window.location.reload();
  }
}

function removeVideoStream(socketId, userName) {
  // Remove video element
  const videoContainer = document.getElementById("videos");
  const videoWraps = videoContainer.getElementsByClassName("video-wrap");
  for (let videoWrap of videoWraps) {
    const userLabel = videoWrap.getElementsByClassName("user-label")[0];
    if (userLabel && userLabel.textContent === userName) {
      videoContainer.removeChild(videoWrap);
      break;
    }
  }

  // Remove audio element
  const audioContainer = document.getElementById("groupCallVideoContainer");
  const audioElements = audioContainer.getElementsByTagName("audio");
  for (let audioElement of audioElements) {
    if (audioElement.srcObject && audioElement.srcObject.id === socketId) {
      audioContainer.removeChild(audioElement);
      break;
    }
  }

  console.log(`Removed video and audio streams for user: ${userName}`);
}

async function webrtc_data_server_on(message) {
  if (isCalling) {
    await webrtc_data_server(message);
  } else {
    webrtc_data_server_list.push(message);
  }
}
window.closeCamera = function () {
  if (localStream) {
    localStream.getTracks().forEach((track) => {
      track.stop();
    });
    localStream = null;
    console.log("Camera is off");
  }
};
async function displayGroupCallPopup(roomUUID) {
  const callPopup = document.getElementById("callPopup");
  callPopup.innerHTML = `<div class="callPopupContent"><p>단체 전화가 왔습니다.</p>
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
  isCalling = true;
  setTimeout(() => {
    boom_server(roomUUID);
  }, 1000);
}
async function boom_server(roomUUID) {
  currentRoomUUID = roomUUID;
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
  displayLocalVideo();

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
  openMultipleCallWindow();
  displayLocalVideo();
  mySocket.emit("boom-client", [...selectedUsers, mySocketId]);
}

function displayLocalVideo() {
  const videoContainer = document.getElementById("videos");
  const localVideoWrap = document.createElement("div");
  localVideoWrap.classList.add("video-wrap", "focus"); // Appliquer la classe 'focus'

  let localVideoElement = document.createElement("video");
  localVideoElement.srcObject = localStream;
  localVideoElement.autoplay = true;
  localVideoElement.playsInline = true;
  localVideoElement.muted = true; // Mute pour éviter l'écho
  localVideoElement.classList.add("remote-video");

  const localUserNameLabel = document.createElement("div");
  localUserNameLabel.classList.add("user-label");
  localUserNameLabel.textContent = new URLSearchParams(
    window.location.search
  ).get("username");

  localVideoWrap.appendChild(localVideoElement);
  localVideoWrap.appendChild(localUserNameLabel);
  videoContainer.insertBefore(localVideoWrap, videoContainer.firstChild); // Ajoute au début
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

function showSelectedUsersPopup() {
  const usersList = document.getElementById("usersList");
  usersList.innerHTML = ""; // Clear previous user list entries

  selectedUsers.forEach((socketId, index) => {
    const userDiv = document.createElement("div");
    userDiv.className = "user-div";
    userDiv.textContent = getUserNameBySocketId(socketId);

    const removeButton = document.createElement("button");
    removeButton.textContent = "선택취소";
    removeButton.className = "remove-button";
    removeButton.onclick = function () {
      selectedUsers.splice(index, 1);
      const counterDisplay = document.getElementById("counter-display");
      counterDisplay.innerText = selectedUsers.length + " 개";
      showSelectedUsersPopup();
    };

    userDiv.insertBefore(removeButton, userDiv.firstChild);
    usersList.appendChild(userDiv);
  });

  const popup = document.getElementById("selectedUsersPopup");
  popup.style.display = "flex";

  const callButton = document.getElementById("callAllButton");
  callButton.onclick = function () {
    isCalling = true;
    allBoom();
    popup.style.display = "none";
  };
}

function setupCloseButton() {
  const closeButton = document.querySelector(".close-popup-button");
  if (closeButton) {
    closeButton.addEventListener("click", function () {
      const popup = document.getElementById("selectedUsersPopup");
      if (popup) {
        popup.style.display = "none";
      }
      selectedUsers = [];
      resetButtonStyles();
      updateUIAfterClose();
    });
  }
}

function resetButtonStyles() {
  const buttons = document.querySelectorAll(".save-button");
  buttons.forEach((button) => {
    button.style.backgroundColor = "";
    button.dataset.isSelected = "false";
  });
}

function updateUIAfterClose() {
  const counterDisplay = document.getElementById("counter-display");
  if (counterDisplay) {
    counterDisplay.innerText = "0 개";
  }
  saveButtonCounter = 0;
}

document.addEventListener("DOMContentLoaded", function () {
  setupCloseButton();
  document
    .getElementById("all-call-button")
    .addEventListener("click", showSelectedUsersPopup);

  document.getElementById("closeGroupCall").onclick = function () {
    window.location.reload();
  };
});
