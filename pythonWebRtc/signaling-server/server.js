const http = require("http");
const socketIo = require("socket.io");
const express = require("express");

const app = express();
const server = http.createServer();
const io = socketIo(server, {
  cors: {
    origin: "*",
  },
});
let users = [];
let userNames = {};
app.get("/get-user", (req, res) => {
  console.log("Get users");
  res.json(users);
});
app.listen(3000, () => {
  console.log("Server is running on port 3000");
});
io.on("connection", (socket) => {
  console.log("Client connected:", socket.id);
  socket.on("set-username", (data) => {
    userNames[socket.id] = data.username;
  });
  socket.on("disconnect", () => {
    const username = userNames[socket.id];
    if (username) {
      console.log("Client disconnected:", username);
      users = users.filter((user) => user.user !== username);
      io.emit("users-delete", username);
      delete userNames[socket.id];
    } else {
      console.log("Client disconnected with no username:", socket.id);
    }
  });

  // Handle SDP Offer
  socket.on("sdp-offer", (data) => {
    console.log("SDP Offer received:", data.offer);
    console.log("SDP Offer for:", data.userReceiveCall);
    io.emit("sdp-offer-received", data); // Forward the SDP Offer to other clients
  });

  // Handle SDP Answer
  socket.on("sdp-answer", (data) => {
    data.senderId = socket.id;
    console.log("SDP Answer received:", data);
    io.emit("sdp-answer", data); // Forward the SDP Answer to other clients
  });

  // Handle user
  socket.on("user", (data) => {
    console.log("users received:", data);
    users.push(data);
    io.emit("users", data);
  });

  socket.on("message", (data) => {
    console.log("Message received:", data);
    socket.broadcast.emit("message", data);
  });
});
server.listen(5000, () => {
  console.log("Signaling server listening on port 5000");
});
