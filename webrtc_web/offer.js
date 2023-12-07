import { serverUrl, rtcConfig } from "./config.js";
document.addEventListener("DOMContentLoaded", function () {
  var socket = io.connect(serverUrl);
  var usersDiv = document.getElementById("users");
  var username = new URLSearchParams(window.location.search).get("username");
  var target = "";
  var localConnection = new RTCPeerConnection(rtcConfig);

  // Enregistrement des événements d'état ICE
  localConnection.oniceconnectionstatechange = function (event) {
    console.log(
      "ICE connection state change:",
      localConnection.iceConnectionState
    );
  };

  // Enregistrement des changements d'état de la négociation
  localConnection.onsignalingstatechange = function (event) {
    console.log("Signaling state change:", localConnection.signalingState);
  };

  // Enregistrement des candidats ICE
  localConnection.onicecandidate = function (event) {
    if (event.candidate) {
      console.log("New ICE candidate (Offer):", event.candidate);
      socket.emit("sendCandidateToAnswer", {
        target: target,
        candidate: event.candidate,
      });
    }
  };

  socket.on("receiveCandidateInOffer", function (data) {
    if (data.target === username) {
      console.log("ice candidate to add", data);
      var candidate = new RTCIceCandidate(data.candidate);
      localConnection.addIceCandidate(candidate).catch(console.error);
    }
  });

  socket.on("connect", function () {
    socket.emit("register", { username: username });
  });

  socket.on("update_users", function (users) {
    usersDiv.innerHTML = "";
    users.forEach(function (user) {
      if (user == username) {
        return;
      }
      var btn = document.createElement("button");
      btn.innerText = user;
      btn.onclick = function () {
        createAndSendOffer(user);
      };
      usersDiv.appendChild(btn);
    });
  });

  function createAndSendOffer(targetUser) {
    target = targetUser;
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: true })
      .then((stream) => {
        stream
          .getTracks()
          .forEach((track) => localConnection.addTrack(track, stream));

        return localConnection.createOffer();
      })
      .then((offer) => {
        return localConnection.setLocalDescription(offer);
      })
      .then(() => {
        var offerData = {
          type: "offer",
          sdp: localConnection.localDescription.sdp,
          target: targetUser,
          id: username,
        };
        sendOfferToServer(offerData);
      })
      .catch(console.error);
  }

  function sendOfferToServer(offerData) {
    fetch("http://" + serverUrl + "/offer", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `type=${offerData.type}&sdp=${encodeURIComponent(
        offerData.sdp
      )}&target=${offerData.target}&id=${offerData.id}&from=${username}`,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
      })
      .catch(console.error);
  }

  socket.on("getAnswer", function (data) {
    if (data.id === username) {
      var remoteDesc = new RTCSessionDescription({
        type: data.type,
        sdp: data.sdp,
      });

      localConnection
        .setRemoteDescription(remoteDesc)
        .then(() => {
          console.log("Remote description set successfully");
        })
        .catch(console.error);
    }
  });
});
