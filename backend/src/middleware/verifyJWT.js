import ErrorHandler from "../utils/errorHandler.js";
import { ResponseHandler } from "../utils/responseHandler.js";
import User from "../model/user.js";
import jwt from "jsonwebtoken";

export const verifyJWT = ResponseHandler(async (req, res, next) => {
    const incomingAccessToken = req.cookies.Token;
    // console.log(incomingAccessToken);
    if (!incomingAccessToken) {
        throw new ErrorHandler('You are not logged in to perform this action',400);
    }
    try {
       
        const decoded = jwt.verify(incomingAccessToken, process.env.AccKey);
        let user;

        
        if (decoded.googleId) {

            user = await User.findOne({ googleId: decoded.googleId });
        } else if (decoded.email) {
           
            user = await User.findOne({ email: decoded.email });
        } else {
            
            throw new ErrorHandler('Invalid token',400);
        }

        
        if (!user) {
            throw new ErrorHandler('Unauthorized access',400);
        }

        req.user = user;
        next();
    } catch (error) {
        throw new ErrorHandler(error.message,error.statusCode || 500);
    }
});
