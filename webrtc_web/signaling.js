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

const usersForRoom = {};
const socketToRoom = {};

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
    const roomID = socketToRoom[socket.id];
    let room = usersForRoom[roomID];
    if (room) {
      room = room.filter((id) => id !== socket.id);
      usersForRoom[roomID] = room;
    }
  });

  // start room functions

  socket.on("roomCall", (data) => {
    const { roomId, selectedUsers } = data;
    io.emit("roomCalling", { roomId, selectedUsers });
    console.log(
      `Room call initiated for room ${roomId} with users: ${selectedUsers.join(
        ", "
      )}`
    );
  });

  socket.on("join room", (roomID) => {
    if (usersForRoom[roomID]) {
      const length = usersForRoom[roomID].length;
      if (length === 4) {
        socket.emit("room full");
        return;
      }
      usersForRoom[roomID].push(socket.id);
    } else {
      usersForRoom[roomID] = [socket.id];
    }
    socketToRoom[socket.id] = roomID;
    const usersInThisRoom = usersForRoom[roomID].filter(
      (id) => id !== socket.id
    );

    socket.emit("all users", usersInThisRoom);
  });

  socket.on("sending signal", (payload) => {
    io.to(payload.userToSignal).emit("user joined", {
      signal: payload.signal,
      callerID: payload.callerID,
    });
  });

  socket.on("returning signal", (payload) => {
    io.to(payload.callerID).emit("receiving returned signal", {
      signal: payload.signal,
      id: socket.id,
    });
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
