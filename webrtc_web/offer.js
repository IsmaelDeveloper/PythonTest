import { serverUrl, rtcConfig, socket } from "./config.js";
import {
  attachSaveButtonEvent,
  deleteSelectedUsers,
} from "./multipleCallOffer.js";
document.addEventListener("DOMContentLoaded", function () {
  console.log("io url >> " + serverUrl);
  var usersDiv = document.getElementById("users");
  var username = new URLSearchParams(window.location.search).get("username");
  var target = "";
  var currentCallTarget = "";
  var localConnection = new RTCPeerConnection(rtcConfig);

  // Enregistrement des événements d'état ICE
  localConnection.oniceconnectionstatechange = function (event) {
    console.log(
      "ICE connection state change:",
      localConnection.iceConnectionState
    );
    if (localConnection.iceConnectionState === "disconnected") {
      showNetworkIssuePopup();
      setTimeout(() => {
        document.getElementById("networkIssuePopup").style.display = "none";
      }, 10000);
    }
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

  localConnection.ontrack = function (event) {
    if (event.track.kind === "video") {
      console.log("event", event);
      document.getElementById("remoteVideo").srcObject = event.streams[0];
    } else if (event.track.kind === "audio") {
      console.log("event audio ", event);
      document.getElementById("remoteAudio").srcObject = event.streams[0];
    }
  };

  document.getElementById("closeVideo").onclick = function () {
    document.getElementById("videoPopup").style.display = "none";
    socket.emit("sendCloseWebrtcDuo", { username: currentCallTarget });
    window.location.reload();
  };

  socket.on("receiveCandidateInOffer", function (data) {
    if (data.target === username) {
      console.log("ice candidate to add", data);
      var candidate = new RTCIceCandidate(data.candidate);
      localConnection.addIceCandidate(candidate).catch(console.error);
    }
  });

  socket.on("closeWebrtcDuo", (usernameData) => {
    if (usernameData.username === username) {
      console.log("Reloading due to username match");
      window.location.reload();
    }
  });

  socket.on("connect", function () {
    socket.emit("register", { username: username });
  });

  socket.on("endUpTheCallDuo", function (data) {
    if (data.username === username) {
      cleanUpCall();
    }
  });

  function displayEndUpPopup() {
    document.getElementById("endUpPopup").innerHTML = `<p>통화가 종료되었습니다.
    </p>
      <button id="endup">닫기</button>`;
    document.getElementById("endUpPopup").style.display = "block";
  }

  function showNetworkIssuePopup() {
    document.getElementById("networkIssuePopup").style.display = "block";
  }

  function cleanUpCall() {
    document.getElementById("videoPopup").style.display = "none";
    localConnection.close();
    localConnection = new RTCPeerConnection(rtcConfig);
    displayEndUpPopup();
    document.getElementById("endup").onclick = function () {
      window.location.reload();
    };
  }
  socket.on("update_users", function (users) {
    deleteSelectedUsers();
    usersDiv.innerHTML = ""; // Effacer les utilisateurs existants
    users.forEach(function (user) {
      if (user == username) {
        return; // Ne pas afficher l'utilisateur actuel
      }
      var userContainer = document.createElement("div");
      userContainer.className = "user-container";

      var userName = document.createElement("div");
      userName.className = "user-name";
      userName.innerText = user;

      var buttonContainer = document.createElement("div");
      buttonContainer.className = "button-container";

      var callButton = document.createElement("button");
      callButton.className = "call-button";
      callButton.innerText = "전화걸기";
      callButton.onclick = function () {
        createAndSendOffer(user);
      };

      var saveButton = document.createElement("button");
      saveButton.className = "button save-button";
      saveButton.innerText = "담기";
      attachSaveButtonEvent(saveButton, user);

      buttonContainer.appendChild(saveButton);
      buttonContainer.appendChild(callButton);

      userContainer.appendChild(userName);
      userContainer.appendChild(buttonContainer);

      usersDiv.appendChild(userContainer);
    });
    if (window.initializePagination) {
      window.initializePagination();
    }
  });

  function createAndSendOffer(targetUser) {
    currentCallTarget = targetUser;
    target = targetUser;
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: true })
      .then((stream) => {
        document.getElementById("videoPopup").style.display = "block";
        document.getElementById("localVideo").srcObject = stream;
        document.getElementById("localVideo").classList.add("local-overlay");
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
        setTimeout(() => {
          if (!localConnection.currentRemoteDescription) {
            closeCall();
          }
        }, 20000);
      })
      .catch(console.error);
  }

  function closeCall() {
    document.getElementById("videoPopup").style.display = "none";
    localConnection.close();
    localConnection = new RTCPeerConnection(rtcConfig);
    window.location.reload();
  }

  function sendOfferToServer(offerData) {
    fetch(serverUrl + "/offer", {
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
