import { serverUrl, rtcConfig } from "./config.js";
document.addEventListener("DOMContentLoaded", function () {
  var socket = io.connect(serverUrl);
  var username = new URLSearchParams(window.location.search).get("username");
  var localConnection = new RTCPeerConnection(rtcConfig);
  var target = "";
  socket.on("connect", function () {
    console.log("Connected to the server. Socket ID:", socket.id);
  });
  let iceCandidateQueue = [];

  localConnection.ontrack = function (event) {
    if (event.track.kind === "video") {
      console.log("event", event);
      document.getElementById("remoteVideo").srcObject = event.streams[0];
    } else if (event.track.kind === "audio") {
      console.log("event audio ", event);
      document.getElementById("remoteAudio").srcObject = event.streams[0];
    }
  };

  socket.on("receiveCandidateInAnswer", function (data) {
    if (data.target === username) {
      var candidate = new RTCIceCandidate(data.candidate);
      if (localConnection.remoteDescription) {
        localConnection.addIceCandidate(candidate).catch(console.error);
      } else {
        iceCandidateQueue.push(candidate);
      }
    }
  });

  // Enregistrement des événements d'état ICE
  localConnection.oniceconnectionstatechange = function (event) {
    console.log(
      "ICE connection state change:",
      localConnection.iceConnectionState
    );
    console.log(" status : " + localConnection.getStats());
  };

  // Enregistrement des changements d'état de la négociation
  localConnection.onsignalingstatechange = function (event) {
    console.log("Signaling state change:", localConnection.signalingState);
  };

  // Enregistrement des candidats ICE
  localConnection.onicecandidate = function (event) {
    if (event.candidate) {
      console.log("New ICE candidate (Answer):", event.candidate);
      socket.emit("sendCandidateToOffer", {
        target: target,
        candidate: event.candidate,
      });
    }
  };

  socket.on("getOffer", function (data) {
    if (data.target === username) {
      // Afficher la popup
      document.getElementById("callPopup").style.display = "block";
      var callingSound = document.getElementById("callingSound");
      callingSound.play();
      // Lorsque l'utilisateur accepte l'appel
      document.getElementById("acceptCall").onclick = function () {
        acceptCall(data);
        document.getElementById("callPopup").style.display = "none";
        document.getElementById("videoPopup").style.display = "block"; // Afficher la popup vidéo
        callingSound.pause();
        callingSound.currentTime = 0;
      };

      document.getElementById("closeVideo").onclick = function () {
        document.getElementById("videoPopup").style.display = "none";
        window.location.reload();
      };

      // Lorsque l'utilisateur décline l'appel
      document.getElementById("declineCall").onclick = function () {
        console.log("Call declined");
        document.getElementById("callPopup").style.display = "none";
        callingSound.pause();
        callingSound.currentTime = 0;
        // Vous pouvez ajouter ici une logique pour informer l'autre utilisateur que l'appel a été décliné
      };
    }
  });

  function acceptCall(data) {
    target = data.id;
    var remoteDesc = new RTCSessionDescription({
      type: data.type,
      sdp: data.sdp,
    });

    localConnection
      .setRemoteDescription(remoteDesc)
      .then(() => {
        console.log("Remote description set successfully");
        return navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });
      })
      .then((stream) => {
        stream
          .getTracks()
          .forEach((track) => localConnection.addTrack(track, stream));
        while (iceCandidateQueue.length) {
          let candidate = iceCandidateQueue.shift();
          localConnection.addIceCandidate(candidate).catch(console.error);
        }

        return localConnection.createAnswer();
      })
      .then((answer) => {
        return localConnection.setLocalDescription(answer);
      })
      .then(() => {
        sendAnswerToServer({
          type: "answer",
          sdp: localConnection.localDescription.sdp,
          id: data.from,
        });
      })
      .catch(console.error);
  }
});

function sendAnswerToServer(answerData) {
  fetch("http://" + serverUrl + "/answer", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `type=${answerData.type}&sdp=${encodeURIComponent(
      answerData.sdp
    )}&id=${answerData.id}`,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
    })
    .catch(console.error);
}
