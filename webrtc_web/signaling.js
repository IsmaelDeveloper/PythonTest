const express = require("express");
const https = require("http");
const socketIo = require("socket.io");
const cors = require("cors");
const fs = require("fs");

const app = express();
const certPath = "./cert/";
const privateKey = fs.readFileSync(certPath + "lo.cal.com.key", "utf8");
const certificate = fs.readFileSync(certPath + "lo.cal.com.crt", "utf8");
const credentials = { key: privateKey, cert: certificate };
const httpsServer = https.createServer(credentials, app);
const { PeerServer } = require("peer");
const peerServer = PeerServer({ port: 9000, path: "/myapp" });

app.use(
  cors({
    origin: "*",
    methods: ["GET", "POST"],
  })
);
app.use(express.urlencoded({ extended: true }));
const io = socketIo(httpsServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"],
  },
});

const users = {};
const offers = {};
const answers = {};
const groupCalls = {};

io.on("connection", (socket) => {
  console.log("User connected:", socket.id);

  socket.on("register", (data) => {
    const username = data.username;
    users[username] = socket.id;
    io.emit("update_users", Object.keys(users));
    console.log(`User registered: ${username} with socket ID: ${socket.id}`);
  });

  socket.on("sendCandidateToAnswer", (data) => {
    const targetSocketId = users[data.target];
    if (targetSocketId) {
      io.emit("receiveCandidateInAnswer", data);
    }
  });

  // Réception des candidats ICE de l'Answer et envoi au pair Offer
  socket.on("sendCandidateToOffer", (data) => {
    const targetSocketId = users[data.target];
    if (targetSocketId) {
      io.to(targetSocketId).emit("receiveCandidateInOffer", data);
    }
  });
  socket.on("disconnect", () => {
    let userToRemove;
    for (const [username, socketId] of Object.entries(users)) {
      if (socketId === socket.id) {
        userToRemove = username;
        break;
      }
    }
    if (userToRemove) {
      delete users[userToRemove];
      io.emit("update_users", Object.keys(users));
    }
    console.log("User disconnected:", socket.id);

    // disconnect from room
  });

  // start room functions

  socket.on("sendCandidateToAnswerForMultipleCall", (data) => {
    const targetSocketId = users[data.target];
    if (targetSocketId) {
      io.emit("receiveCandidateInAnswerForMultipleCall", data);
    }
  });

  socket.on("sendCandidateToOfferForMultipleCall", (data) => {
    const targetSocketId = users[data.target];
    if (targetSocketId) {
      io.emit("receiveCandidateInOfferForMultipleCall", data);
    }
  });
  socket.on("roomCall", ({ offer, targetUser, from }) => {
    io.emit("roomCalling", { offer, from, targetUser });
  });

  socket.on("sendAnswerMultipleCall", ({ answer, to, from }) => {
    io.emit("receiveAnswer", { answer, to, from: from });
  });

  // end room functions
});

app.post("/offer", (req, res) => {
  if (req.body.type === "offer") {
    const offerData = {
      id: req.body.id,
      type: req.body.type,
      sdp: req.body.sdp,
      target: req.body.target,
      from: req.body.from,
    };
    offers[offerData.id] = offerData;
    broadcastOffer(offerData);
    res.status(200).send();
  } else {
    res.status(400).send();
  }
});
function broadcastOffer(offerData) {
  io.emit("getOffer", offerData);
}

app.post("/answer", (req, res) => {
  if (req.body.type === "answer") {
    const answerData = {
      id: req.body.id,
      type: req.body.type,
      sdp: req.body.sdp,
    };
    answers[answerData.id] = answerData;
    broadcastAnswer(answerData);
    res.status(200).send();
  } else {
    res.status(400).send();
  }
});

function broadcastAnswer(answerData) {
  console.log("Answer data", answerData);
  io.emit("getAnswer", answerData);
}

const PORT = 6969;
httpsServer.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
