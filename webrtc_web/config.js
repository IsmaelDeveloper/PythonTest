// config.js
//export const serverUrl = "192.168.0.136:6969";
export const serverUrl = `${location.protocol}//${location.hostname}:8234`;

export const rtcConfig = {
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
