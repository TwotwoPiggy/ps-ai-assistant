import { io } from "socket.io-client";

// Connect to the Python backend server
// Note: In production, you might want to configure this based on environment
const SOCKET_URL = "http://127.0.0.1:18919";

export const socket = io(SOCKET_URL, {
    transports: ["websocket", "polling"],
});

socket.on("connect", () => {
    console.log("Connected to PS AI Assistant server");
});

socket.on("disconnect", () => {
    console.log("Disconnected from server");
});
