const express = require("express");
const app = express();
const cors = require("cors");

app.use(cors());
app.use(express.json());

app.use((req, res, next) => {
    console.log("REQUEST RECEIVED:", req.method, req.originalUrl);
    next();
});

const detectionrouter = require("./routers/detectionroute");

app.use("/yolo/api", detectionrouter);

module.exports = app;