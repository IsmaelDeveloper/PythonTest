document.addEventListener("DOMContentLoaded", function () {
  var socket = io.connect("http://" + "127.0.0.1" + ":" + "6969");
  var username = new URLSearchParams(window.location.search).get("username");
  var iceServers = [
    {
      urls: "stun:stun.l.google.com:19302",
    },
    {
      urls: "turn:13.250.13.83:3478?transport=udp",
      username: "YzYNCouZM1mhqhmseWk6",
      credential: "YzYNCouZM1mhqhmseWk6",
    },
  ];

  var rtcConfig = {
    iceServers: iceServers,
  };

  var localConnection = new RTCPeerConnection(rtcConfig);
  var target = "";
  socket.on("connect", function () {
    console.log("Connected to the server. Socket ID:", socket.id);
  });
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
      console.log("ice candidate to add", data);
      var candidate = new RTCIceCandidate(data.candidate);
      localConnection.addIceCandidate(candidate).catch(console.error);
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
      target = data.id;
      // Définir la description distante (l'offre)
      var remoteDesc = new RTCSessionDescription({
        type: data.type,
        sdp: data.sdp,
      });
      localConnection
        .setRemoteDescription(remoteDesc)
        .then(() => {
          console.log("Remote description set successfully");

          // Créer une réponse
          return localConnection.createAnswer();
        })
        .then((answer) => {
          // Définir la description locale (la réponse)
          return localConnection.setLocalDescription(answer);
        })
        .then(() => {
          // Envoyer la réponse au serveur
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
    fetch("http://127.0.0.1:6969/answer", {
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
});
