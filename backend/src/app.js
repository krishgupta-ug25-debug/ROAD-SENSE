const express=require("express")
const app=express()
const cors = require("cors")
app.use(cors())
app.use(express.json())
const detectionrouter=require("./routers/detectionroute")

app.use("/yolo/api",detectionrouter.detectionrouter)

module.exports=app
