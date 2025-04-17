import { ResponseHandler } from "../utils/responseHandler.js";
import ErrorHandler from "../utils/errorHandler.js";
import User from "../model/user.js";
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
        console.log(image1Buffer);
        console.log(image2Buffer);
        return res.status(200).json({
            message: "received data successfully"
        })
    } catch (error) {
        throw new ErrorHandler(error.message, 500 || error.statusCode);
    }
})