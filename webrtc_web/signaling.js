const { v4: uuidv4, v6: uuidv6 } = require("uuid");
const express = require("express");
const https = require("http");
const socketIo = require("socket.io");
const cors = require("cors");
const fs = require("fs");

const app = express();
const certPath = "./cert/";
const privateKey = fs.readFileSync(certPath + "lo.cal.com.key", "utf8");
const certificate = fs.readFileSync(certPath + "lo.cal.com.crt", "utf8");
// const certPath = "/etc/letsencrypt/live/kiosk-chat.musicen.com/";
// const privateKey = fs.readFileSync(certPath + "privkey.pem", "utf8");
// const certificate = fs.readFileSync(certPath + "fullchain.pem", "utf8");
const credentials = { key: privateKey, cert: certificate };
const rooms = [];
// ssl_certificate /etc/letsencrypt/live/schback.musicen.com/fullchain.pem; # managed by Certbot
// ssl_certificate_key /etc/letsencrypt/live/schback.musicen.com/privkey.pem; # managed by Certbot
// include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
// ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

const httpsServer = https.createServer(credentials, app);
const notAnsweredYet = [];

app.use(express.static(__dirname));

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

const allSockets = {};

io.on("connection", (socket) => {
  console.log("User connected:", socket.id);
  socket.on("register", (data) => {
    const username = data.username;
    users[username] = socket.id;
    io.emit("update_users", Object.keys(users));
    console.log(`User registered: ${username} with socket ID: ${socket.id}`);
  });

  console.log("🚀 ~ io.on ~ socket:", socket.id);
  allSockets[socket.id] = { socket: socket, userNm: null };

  socket.join("main");
  socket.on("usernm-client", (userNm) => {
    userNm;
    console.log("🚀 ~ socket.on ~ userNm:", userNm);

    allSockets[socket.id].userNm = userNm;
    refreshUsers();
  });
  refreshUsers();

  socket.on("sendCandidateToAnswer", (data) => {
    const targetSocketId = users[data.target];
    if (targetSocketId) {
      io.emit("receiveCandidateInAnswer", data);
    }
  });

  socket.on("sendCloseWebrtcDuo", (usernameData) => {
    io.emit("closeWebrtcDuo", usernameData);
  });
  socket.on("sendEndUpTheCallDuo", (usernameData) => {
    io.emit("endUpTheCallDuo", usernameData);
  });
  // Réception des candidats ICE de l'Answer et envoi au pair Offer
  socket.on("sendCandidateToOffer", (data) => {
    const targetSocketId = users[data.target];
    if (targetSocketId) {
      io.to(targetSocketId).emit("receiveCandidateInOffer", data);
    }
  });
  socket.on("disconnect", () => {
    for (const roomUUID in rooms) {
      if (rooms.hasOwnProperty(roomUUID)) {
        const index = rooms[roomUUID].indexOf(socket.id);
        if (index !== -1) {
          rooms[roomUUID].splice(index, 1); // Remove the user from the room
          // Notify the remaining users in the room
          rooms[roomUUID].forEach((id) => {
            io.to(id).emit("user-left", { socketId: socket.id });
          });
          // If the room is empty, delete the room
          if (rooms[roomUUID].length === 0) {
            delete rooms[roomUUID];
          }
        }
      }
    }

    delete allSockets[socket.id];
    refreshUsers();

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

  socket.on("boom-client", (boomUsers) => {
    const uuid = uuidv4();
    if (!rooms[uuid]) {
      rooms[uuid] = [];
    }
    boomUsers.forEach((socketId) => {
      io.to(socketId).emit("boom-server", uuid);
    });
  });

  socket.on("addNotAnsweredPerson", (roomUUID, username) => {
    if (!notAnsweredYet[roomUUID]) {
      notAnsweredYet[roomUUID] = [];
    }
    notAnsweredYet[roomUUID].push(username);
  });
  socket.on("getNotAnsweredPerson", (roomUUID) => {
    socket.emit("notAnsweredPerson", {
      roomUUID,
      participants: notAnsweredYet[roomUUID],
    });
  });
  socket.on("removeNotAnsweredPerson", (roomUUID, username) => {
    notAnsweredYet[roomUUID] = notAnsweredYet[roomUUID].filter(
      (user) => user !== username
    );
  });
  socket.on("get-room-participants", (data) => {
    const { roomUUID } = data;
    if (rooms[roomUUID]) {
      socket.emit("room-participants", {
        roomUUID,
        participants: rooms[roomUUID],
      });
    } else {
      socket.emit("room-participants", { roomUUID, participants: [] });
    }
  });

  socket.on("endAllCalls", function (data) {
    io.to(data.roomUUID).emit("endCallForEveryone");
  });

  socket.on("join-room", (data) => {
    const { roomUUID } = data;
    if (rooms[roomUUID]) {
      rooms[roomUUID].push(socket.id);
      socket.join(roomUUID);
      console.log(`User ${socket.id} joined room ${roomUUID}`);
    } else {
      console.log(`Room ${roomUUID} does not exist`);
    }
  });

  socket.on("webrtc-data-client", (message) => {
    const { sender, receiver, msgType, rtcData } = message;
    console.log("🚀 ~ socket.on ~ sender:", sender, receiver, msgType);
    io.to(receiver).emit("webrtc-data-server", {
      sender,
      receiver,
      msgType,
      rtcData,
    });
  });

  function refreshUsers() {
    // const users = allSockets.map(socket => ({...socket, socket:null}));

    const users = {};
    Object.entries(allSockets).forEach(([key, value]) => {
      // allSockets[key].socket = null
      users[key] = { ...value, socket: null };
    });
    io.emit("users-server", users);
  }
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

app.get("/test", (req, res) => {
  res.status(200).send("Server work correctly");
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

app.get("/msg", (req, res) => {
  const msg = req.query.msg;
  io.emit("msg-server", msg);
});
app.get("/rooms", (req, res) => {
  const msg = req.params.msg;
  console.log(io.sockets.adapter.rooms);
  // res.json(io.sockets.adapter.rooms);
  res.json(Object.fromEntries(io.sockets.adapter.rooms));
});

const PORT = 8234;
httpsServer.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
