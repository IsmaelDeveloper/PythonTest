let saveButtonCounter = 0;
let selectedUsers = [];

let socketRef = io.connect(`${location.protocol}//${location.hostname}:6969`);
var username = new URLSearchParams(window.location.search).get("username");
const offerConnection = {};
const answerConnection = {};
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
          offerConnection[targetUser] = new RTCPeerConnection(rtcConfig);
          navigator.mediaDevices
            .getUserMedia({ video: true, audio: true })
            .then((stream) => {
              console.log("Tracks to be added:", stream.getTracks());
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
              ) {
                console.log(
                  "Signaling state change:",
                  offerConnection[targetUser].signalingState
                );
              };
              offerConnection[targetUser].onicecandidate = function (event) {
                if (event.candidate) {
                  // console.log("New ICE candidate (Offer):", event.candidate);
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
              });
              socketRef.on("receiveAnswer", function (data) {
                const { answer, to, from } = data;
                if (username === to) {
                  console.log("username : ", username);
                  console.log("from : ", from);
                  console.log(answer);
                  // console.log("receiveAnswer", answer);
                  offerConnection[targetUser].setRemoteDescription(
                    new RTCSessionDescription(answer)
                  );
                  offerConnection[targetUser].ontrack = function (event) {
                    addVideoStream(event);
                  };
                }
              });
              socketRef.on(
                "receiveCandidateInOfferForMultipleCall",
                function (data) {
                  console.log(data);
                  if (data.target === username) {
                    var candidate = new RTCIceCandidate(data.candidate);
                    if (offerConnection[targetUser].remoteDescription) {
                      offerConnection[targetUser]
                        .addIceCandidate(candidate)
                        .catch(console.error);
                    } else {
                      pendingCandidates.push(candidate);
                    }
                  }
                }
              );
            });
        }
      });
    });
  // call

  // receive call
  socketRef.on("roomCalling", function (data) {
    const { offer, from, targetUser } = data;
    if (username === targetUser) {
      displayGroupCallPopup(offer, from, targetUser);
    }
  });
  // receive call

  function displayGroupCallPopup(offer, from, targetUser) {
    const callPopup = document.getElementById("callPopup");
    callPopup.innerHTML = `<p>그룹 콜 초대.</p>
        <button id="acceptGroupCall">수락하다</button>
        <button id="declineGroupCall">거절하다</button>`;
    callPopup.style.display = "block";

    const callingSound = document.getElementById("callingSound");
    callingSound.play();

    // accept call
    document.getElementById("acceptGroupCall").onclick = function () {
      callPopup.style.display = "none";
      callingSound.pause();
      callingSound.currentTime = 0;
      document.getElementById("groupCallVideoContainer").style.display =
        "block";
      acceptGroupCall(offer, from, targetUser);
    };

    //denied call
    document.getElementById("declineGroupCall").onclick = function () {
      callPopup.style.display = "none";
      callingSound.pause();
      callingSound.currentTime = 0;
    };

    // close call
    document.getElementById("closeGroupCall").onclick = function () {
      document.getElementById("groupCallVideoContainer").style.display = "none"; // Cacher le conteneur sur clic du bouton Fermer
    };
  }

  // start a call
  function acceptGroupCall(offer, from, targetUser) {
    if (username == targetUser) {
      // Vérifiez si l'offre est destinée à cet utilisateur
      answerConnection[from] = new RTCPeerConnection(rtcConfig);
      answerConnection[from].ontrack = function (event) {
        // alert("targetUser : " + targetUser + " from : " + from);
        addVideoStream(event);
      };
      answerConnection[from]
        .setRemoteDescription(new RTCSessionDescription(offer))
        .then(() => {
          pendingCandidates.forEach((candidate) => {
            answerConnection[from]
              .addIceCandidate(candidate)
              .catch(console.error);
          });
          pendingCandidates = [];
          return navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true,
          });
        })
        .then((stream) => {
          console.log("Tracks to be added: in answer", stream.getTracks());
          stream.getTracks().forEach((track) => {
            answerConnection[from].addTrack(track, stream);
          });

          return answerConnection[from].createAnswer();
        })
        .then((answer) => {
          answerConnection[from].setLocalDescription(answer);

          // Envoyer la réponse au serveur pour qu'elle soit transmise à l'émetteur
          socketRef.emit("sendAnswerMultipleCall", {
            answer,
            to: from,
            from: username,
          });

          socketRef.on(
            "receiveCandidateInAnswerForMultipleCall",
            function (data) {
              if (data.target === username) {
                var candidate = new RTCIceCandidate(data.candidate);
                if (answerConnection[from].remoteDescription) {
                  answerConnection[from]
                    .addIceCandidate(candidate)
                    .catch(console.error);
                }
              }
            }
          );

          answerConnection[from].onicecandidate = function (event) {
            if (event.candidate) {
              // console.log("New ICE candidate (Answer):", event.candidate);
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
    let container = document.getElementById("groupCallVideoContainer");
    if (!container.style.display || container.style.display === "none") {
      container.style.display = "block";
    }

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
