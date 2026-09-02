const express=require("express")

const multer=require("multer")
const storage=multer.memoryStorage()
const upload = multer({storage: storage,})

const detectController=require("../controllers/detectioncontoller")
const detectionrouter=express.Router()


detectionrouter.post("/createdetection",upload.single("Image"),detectController.createdetection)
detectionrouter.get("/getalldetection",detectController.getalldetection)
detectionrouter.get("/getdetection/:id",detectController.getdetectionById)
detectionrouter.get("/getalldetection",detectController.getalldetection)

module.exports={detectionrouter}