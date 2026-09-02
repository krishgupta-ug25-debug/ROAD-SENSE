const express=require("express")

const multer=require("multer")
const storage=multer.memoryStorage()
const upload = multer({storage: storage,})

const detectController=require("../controllers/detectioncontoller")
const detectionrouter=express.Router()


router.post(
    "/createdetection",
    upload.single("Image"),
    (req, res, next) => {
        console.log("MULTER FILE:", req.file);
        console.log("MULTER BODY:", req.body);
        next();
    },
    detectController.createdetection
);
detectionrouter.get("/getalldetection",detectController.getalldetection)
detectionrouter.get("/getdetection/:id",detectController.getdetectionById)
detectionrouter.get("/getalldetection",detectController.getalldetection)

module.exports={detectionrouter}