let saveButtonCounter = 0;
let selectedUsers = [];

let socketRef = io.connect(`${location.protocol}//${location.hostname}:8234`);
var username = new URLSearchParams(window.location.search).get("username");
var offerConnection = {};
var answerConnection = {};
var waitingAnswer = [];
var isCalling = false;
const rtcConfig = {
  iceServers: [
    {
      urls: "stun:stun.l.google.com:19302",
    },
    {
      urls: "turn:13.250.13.83:3478?transport=udp",
      username: "YzYNCouZM1mhqhmseWk6",
      credential: "YzYNCouZM1mhqhmseWk6",
    },
  ],
};
let pendingCandidates = [];

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

//

document.addEventListener("DOMContentLoaded", function () {
  // call
  document
    .getElementById("all-call-button")
    .addEventListener("click", function () {
      selectedUsers.forEach((targetUser) => {
        if (targetUser !== username) {
          createOfferMultipleCall(targetUser);
          openMultipleCallWindow();
        }
      });
    });
  // call

  function createOfferMultipleCall(targetUser, listUsers = selectedUsers) {
    if (offerConnection[targetUser]) return;
    offerConnection[targetUser] = new RTCPeerConnection(rtcConfig);
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: true })
      .then((stream) => {
        stream
          .getTracks()
          .forEach((track) =>
            offerConnection[targetUser].addTrack(track, stream)
          );
        return offerConnection[targetUser].createOffer();
      })
      .then((offer) => {
        offerConnection[targetUser].setLocalDescription(offer);
        offerConnection[targetUser].onsignalingstatechange = function (
          event
        ) {};
        offerConnection[targetUser].onicecandidate = function (event) {
          if (event.candidate) {
            socketRef.emit("sendCandidateToAnswerForMultipleCall", {
              target: targetUser,
              candidate: event.candidate,
            });
          }
        };

        socketRef.emit("roomCall", {
          offer,
          targetUser,
          from: username,
          listUsers: listUsers,
        });
        socketRef.on("receiveAnswer", function (data) {
          const { answer, to, from } = data;
          if (username === to) {
            offerConnection[from].setRemoteDescription(
              new RTCSessionDescription(answer)
            );
            offerConnection[from].ontrack = function (event) {
              addVideoStream(event);
            };
          }
        });
        socketRef.on("receiveCandidateInOfferForMultipleCall", function (data) {
          if (data.target === username) {
            var candidate = new RTCIceCandidate(data.candidate);
            if (offerConnection[data.from].remoteDescription) {
              offerConnection[data.from]
                .addIceCandidate(candidate)
                .catch(console.error);
            }
          }
        });
      });
  }

  // receive call
  socketRef.on("roomCalling", function (data) {
    const { offer, from, targetUser, listUsers } = data;

    if (username === targetUser) {
      displayGroupCallPopup(offer, from, targetUser, listUsers);
    }
  });

  // receive call

  function displayGroupCallPopup(offer, from, targetUser, listUsers) {
    if (answerConnection[from]) return;
    answerConnection[from] = new RTCPeerConnection(rtcConfig);
    socketRef.on("receiveCandidateInAnswerForMultipleCall", function (data) {
      if (data.target === targetUser) {
        var candidate = new RTCIceCandidate(data.candidate);
        if (answerConnection[from].remoteDescription) {
          answerConnection[from]
            .addIceCandidate(candidate)
            .catch(console.error);
        } else {
          pendingCandidates.push({ from: from, candidate: candidate });
        }
      }
    });

    openMultipleCallWindow();
    acceptGroupCall(offer, from, targetUser);

    const currentUserIndex = listUsers.indexOf(username);
    if (currentUserIndex !== -1 && !isCalling) {
      const usersAfterCurrent = listUsers.slice(currentUserIndex + 1);
      usersAfterCurrent.forEach((user) => {
        setTimeout(() => {
          createOfferMultipleCall(user, []);
        }, (currentUserIndex + 1) * 1000);
        isCalling = true;
      });
    }
  }
  // close call
  document.getElementById("closeGroupCall").onclick = function () {
    answerConnection = {};
    offerConnection = {};
    window.location.reload();
    document.getElementById("groupCallVideoContainer").style.display = "none"; // Cacher le conteneur sur clic du bouton Fermer
  };

  function openMultipleCallWindow() {
    let container = document.getElementById("groupCallVideoContainer");
    if (!container.style.display || container.style.display === "none") {
      container.style.display = "block";
    }
  }
  // start a call
  function acceptGroupCall(offer, from, targetUser) {
    if (username == targetUser) {
      // Vérifiez si l'offre est destinée à cet utilisateur
      answerConnection[from].ontrack = function (event) {
        addVideoStream(event);
      };
      answerConnection[from]
        .setRemoteDescription(new RTCSessionDescription(offer))
        .then(() => {
          pendingCandidates.forEach((candidate) => {
            if (candidate.from === from) {
              answerConnection[from]
                .addIceCandidate(candidate.candidate)
                .catch(console.error);
            }
          });
          return navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true,
          });
        })
        .then((stream) => {
          stream.getTracks().forEach((track) => {
            answerConnection[from].addTrack(track, stream);
          });

          return answerConnection[from].createAnswer();
        })
        .then((answer) => {
          answerConnection[from].setLocalDescription(answer);

          socketRef.emit("sendAnswerMultipleCall", {
            answer,
            to: from,
            from: username,
          });

          answerConnection[from].onicecandidate = function (event) {
            if (event.candidate) {
              socketRef.emit("sendCandidateToOfferForMultipleCall", {
                target: from,
                from: username,
                candidate: event.candidate,
              });
            }
          };
        })
        .catch(console.error);
    }
  }

  function addVideoStream(event) {
    if (event.track.kind === "video") {
      let videoElement = document.createElement("video");
      videoElement.srcObject = new MediaStream([event.track]);
      videoElement.autoplay = true;
      videoElement.playsInline = true;
      videoElement.classList.add("remote-video");
      document.getElementById("videos").appendChild(videoElement);
    } else if (event.track.kind === "audio") {
      let audioElement = document.createElement("audio");
      audioElement.srcObject = new MediaStream([event.track]);
      audioElement.autoplay = true;
      document
        .getElementById("groupCallVideoContainer")
        .appendChild(audioElement);
    }
  }
});
