let saveButtonCounter = 0;
let selectedUsers = [];

// Assurez-vous d'inclure les scripts pour Peer et io au préalable
let peers = [];
let socketRef = io.connect(`${location.protocol}//${location.hostname}:6969`);
const userVideo = document.createElement("video");
const peersRef = [];

function attachSaveButtonEvent(saveButton, userName) {
  saveButton.dataset.isSelected = "false";

  saveButton.addEventListener("click", function () {
    const isSelected = this.dataset.isSelected === "true";
    this.dataset.isSelected = String(!isSelected);

    if (!isSelected) {
      this.style.backgroundColor = "red";
      selectedUsers.push(userName);
      saveButtonCounter += 1;
    } else {
      this.style.backgroundColor = "";
      const index = selectedUsers.indexOf(userName);
      if (index > -1) {
        selectedUsers.splice(index, 1);
      }
      saveButtonCounter -= 1;
    }

    const counterDisplay = document.getElementById("counter-display");
    counterDisplay.innerText = saveButtonCounter + " 개";
  });
}

document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("all-call-button")
    .addEventListener("click", function () {
      const roomId = generateRoomId(); // Générer un roomId aléatoire
      socketRef.emit("roomCall", { roomId, selectedUsers });
      console.log(
        `Calling room with ID: ${roomId} for users: ${selectedUsers.join(", ")}`
      );
    });

  function generateRoomId() {
    const now = Date.now();
    const randomPart = Math.random().toString(36).substring(2, 15);
    return `room_${now}_${randomPart}`;
  }

  socketRef.on("roomCalling", function (data) {
    const { roomId, selectedUsers } = data;
    const username = new URLSearchParams(window.location.search).get(
      "username"
    );
    if (selectedUsers.includes(username)) {
      displayGroupCallPopup(roomId, selectedUsers);
    }
  });

  function displayGroupCallPopup(roomID, selectedUsers) {
    const callPopup = document.getElementById("callPopup");
    callPopup.innerHTML = `<p>그룹 콜 초대.</p>
        <button id="acceptGroupCall">수락하다</button>
        <button id="declineGroupCall">거절하다</button>`;
    callPopup.style.display = "block";

    const callingSound = document.getElementById("callingSound");
    callingSound.play();

    document.getElementById("acceptGroupCall").onclick = function () {
      callPopup.style.display = "none";
      callingSound.pause();
      callingSound.currentTime = 0;
      navigator.mediaDevices
        .getUserMedia({ video: true, audio: true })
        .then((stream) => {
          userVideo.srcObject = stream;
          userVideo.autoplay = true;
          userVideo.muted = true;
          document.body.appendChild(userVideo);

          socketRef.emit("join room", roomID);
          socketRef.on("all users", (users) => {
            const peers = [];
            users.forEach((userID) => {
              const peer = createPeer(userID, socketRef.id, stream);
              peersRef.push({
                peerID: userID,
                peer,
              });
              peers.push(peer);
            });
            peers.forEach((peer) => {
              const video = document.createElement("video");
              peer.on("stream", (stream) => {
                video.srcObject = stream;
                video.autoplay = true;
                document.body.appendChild(video);
              });
            });
          });

          socketRef.on("user joined", (payload) => {
            const peer = addPeer(payload.signal, payload.callerID, stream);
            peersRef.push({
              peerID: payload.callerID,
              peer,
            });

            const video = document.createElement("video");
            peer.on("stream", (stream) => {
              video.srcObject = stream;
              video.autoplay = true;
              document.body.appendChild(video);
            });
          });

          socketRef.on("receiving returned signal", (payload) => {
            const item = peersRef.find((p) => p.peerID === payload.id);
            item.peer.signal(payload.signal);
          });
        });
    };

    document.getElementById("declineGroupCall").onclick = function () {
      callPopup.style.display = "none";
      callingSound.pause();
      callingSound.currentTime = 0;
    };
  }
});

function createPeer(userToSignal, callerID, stream) {
  const peer = new Peer({
    initiator: true,
    trickle: false,
    stream,
  });

  peer.on("signal", (signal) => {
    socketRef.emit("sending signal", {
      userToSignal,
      callerID,
      signal,
    });
  });

  return peer;
}

function addPeer(incomingSignal, callerID, stream) {
  const peer = new Peer({
    initiator: false,
    trickle: false,
    stream,
  });

  peer.on("signal", (signal) => {
    socketRef.emit("returning signal", {
      signal,
      callerID,
    });
  });

  peer.signal(incomingSignal);

  return peer;
}
