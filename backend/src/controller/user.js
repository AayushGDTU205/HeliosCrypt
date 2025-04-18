import { ResponseHandler } from "../utils/responseHandler.js";
import ErrorHandler from "../utils/errorHandler.js";
import User from "../model/user.js";
import axios from "axios";
import sharp from "sharp";

export const postBeforeAfter = ResponseHandler(async (req, res, next) => {
    const { lat1, lat2, long1, long2 } = req.body;
    const { image1, image2 } = req.files;
    console.log(lat1, lat2, long1, long2);
    const reqFields = ["lat1","lat2", "long1","long2"];
    const bodyFields = Object.keys(req.body);
    const missing = reqFields.filter((field) => {
        if (!bodyFields.includes(field)) return true;
        else return false;
    })
    if (missing.length > 0) {
        throw new ErrorHandler('Certain fields missing',400);
    }
    if (!image1 || !image2) {
        throw new ErrorHandler('atleast 2 images requierd',400);
    }
    try {
        const image1Buffer = await sharp(image1[0].buffer).jpeg().toBuffer();
        const image2Buffer = await sharp(image2[0].buffer).jpeg().toBuffer();
        
        if (!image1Buffer || !image2Buffer) {
            throw new ErrorHandler('image processing error try reuploading images', 400);
        }
        const base64_1 = image1Buffer.toString('base64');
        const image1B64 = `data:image/jpeg;base64,${base64_1}`;
        const base64_2 = image2Buffer.toString('base64');
        const image2B64=`data:image/jpeg;base64,${base64_2}`;
        const data = {
            images: {
                before: image1B64,
                after: image2B64
            },
            coordinates: {
                before: [+lat1, +long1],
                after: [+lat2, +long2]
            }
        }; 
        const dataForPy = JSON.stringify(data);
        //making API call to python
        let PyResponse = await axios.post('http://127.0.0.1:5000/api/verify', dataForPy, {
            headers: {
              'Content-Type': 'application/json'
            }
          });
        console.log(PyResponse.data);
        return res.status(200).json({
            message: "received data successfully"
        })
    } catch (error) {
        throw new ErrorHandler(error.message, 500 || error.statusCode);
    }
})