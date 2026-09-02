const dns=require("dns")
dns.setServers(['8.8.8.8','1.1.1.1']);
require("dotenv").config()
const connectDB=require("./src/db/db")
connectDB()
const app=require("./src/app")
app.listen(3000,()=>{
    console.log("Server running on port 3000")
})