const mongoose=require("mongoose")

const Schema=new mongoose.Schema({
    busId:{
        type:String,
        required:true
    },
    latitude:{
        type:Number,
        required:true
    },
    longitude:{
        type:Number,
        required:true
    },
    roadName:{
        type:String,
        default:"Unknown Road"
    },
    imageUrl:{
        type:String,
        required:true
    },
    detections:{
        type:Array,
        default:["No incident detected"]
    }
},{timestamps:true}
)

const model=mongoose.model("detectModel",Schema);
module.exports=model
