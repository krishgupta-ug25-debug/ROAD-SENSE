const detectModel=require("../model/model");
const fs=require("fs");
const {spawn}=require("child_process") // Means to run python script from nodejs we need to use child_process module
const path=require("path")
const {uploadImageToImageKit}=require("../services/storage.service")
function runYOLO(imagePath) {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python', [path.join(__dirname, '../../../', 'yolo', 'main.py'), imagePath])
        let output = ""
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString()
        })
        pythonProcess.stderr.on('data', (data) => {
            console.error(data.toString())
        })
        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                return reject(new Error(`Python script exited with code ${code}`))
            }

            // main.py's stdout can have warning/log noise mixed in (e.g. a
            // one-time ultralytics settings warning) before or after the
            // actual JSON result. Instead of trusting the whole output,
            // scan line by line from the end and take the last line that
            // is genuinely valid JSON — that's the real detection result.
            const lines = output.split('\n').map(l => l.trim()).filter(Boolean)

            for (let i = lines.length - 1; i >= 0; i--) {
                try {
                    JSON.parse(lines[i]) // validate it parses
                    return resolve(lines[i])
                } catch (e) {
                    // not JSON, keep looking further up
                }
            }

            reject(new Error(`No valid JSON found in Python output: ${output}`))
        })
    })
}
// Use of this function is to run the YOLO model on a given image and return the output as a promise. It spawns a child process to execute the Python script and captures the output from stdout. If the script exits successfully, it resolves the promise with the output; otherwise, it rejects the promise with an error.

async function createdetection(req,res){
    const{busId,latitude,longitude}=req.body
    try{
        const file=req.file
        if(!file){
            return res.status(400).json({
                message:"No image file received"
            })
        }
        const uploadPath=path.join(__dirname,"../../../uploads",file.originalname)
        fs.writeFileSync(uploadPath,file.buffer)

        const result=await uploadImageToImageKit(file,req.body)
        
        const yoloResult=JSON.parse(await runYOLO(uploadPath))
        if (!yoloResult || yoloResult.length === 0) {
            return res.status(400).json({
                message: "No detections found"
            });
        }
        
        console.log("YOLO Result:",yoloResult)
        await detectModel.create({
            busId,latitude,longitude,imageUrl:result.url,detections:yoloResult
        })
        return res.status(201).json({
            message:"Saved to DB",
            yoloResult
        })
    }
    catch(err){
        console.log(err)
        return res.status(400).json({
            message:"Couldn't save to DB"
        })
    }
}
async function getalldetection(req,res){
    const allevents=await detectModel.find()
    res.status(200).json({
        message:"Retrieved successfully",
        allevents
    })
}
async function getdetectionById(req,res){
    const id=req.params.id
    const event=await detectModel.findOne({_id:id})
    res.status(200).json({
        message:"Retrieved successfully",
        event
    })
}



module.exports={createdetection,getalldetection,getdetectionById};