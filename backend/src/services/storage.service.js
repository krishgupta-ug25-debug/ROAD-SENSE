const {ImageKit} = require("@imagekit/nodejs");
const client = new ImageKit({
  privateKey: process.env.IMAGEKIT_PRIVATE_KEY});

async function uploadImageToImageKit(file, body) {
  try {
      const response = await client.files.upload({
      file: file.buffer.toString("Base64"), // Path to the image file
      fileName: `${body.busId}_${file.fileName}`, // Name of the file in ImageKit
    });
    return response; // Return the URL of the uploaded image
  } catch (error) {
    console.error("Error uploading image to ImageKit:", error);
    throw error; // Rethrow the error for further handling
  }
}

module.exports = {uploadImageToImageKit};