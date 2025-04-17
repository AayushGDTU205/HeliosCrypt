import { ResponseHandler } from "../utils/responseHandler.js";
import ErrorHandler from "../utils/errorHandler.js";
import User from "../model/user.js";
import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";

export const postSignup = ResponseHandler(async (req, res, next)=> {
    const {email,password,name} = req.body;
    const reqFields = ["email","password", "name"];
    const bodyFields = Object.keys(req.body);
    const missing = reqFields.filter((field) => {
        if (!bodyFields.includes(field)) return true;
        else return false;
    })
    if (missing.length > 0) {
        throw new ErrorHandler(400, 'Certain fields missing');
    }
    try {
        let user = await User.findOne({ email })
        // console.log(User);
        if (user) {
            if (!user.password) {
                user.password = await bcrypt.hash(password, 10);
                await user.save();
            }
            else {
                throw new ErrorHandler("User with given mail exists", 402);
            }
        }
        else {
            user = await User.create({
                email,
                name,
                password: await bcrypt.hash(password, 10)
            });
        }
        // console.log(response.url);
        
        return res.status(200).json({
            message: 'user created succesfully',
            data: user
        })
    } catch (error) {
        throw new ErrorHandler(error.message, 500||error.statusCode);
    }
})

export const postLogin = ResponseHandler(async (req, res, next) => {
    const { email, password } = req.body;
    try {
        const user = await User.findOne({ email: email });
        if (user) {
            if (!user.password) {
                throw new ErrorHandler("kindly login via google", 400);
            }
            else {
                const isMatch = bcrypt.compare(password, user.password);
                if (!isMatch) {
                    throw new ErrorHandler("incorrect password", 400);
                }
            }
        }
        else {
            throw new ErrorHandler("User does not exist");
        }
        const Token = jwt.sign(
            { email: user.email },
            process.env.AccKey,
            {expiresIn:'7d'}
        )
        const options = {
            httpOnly: true
            // expires: new Date(new Date().getTime() + 31557600),
            // secure:true,
            // sameSite:'none'
            }
        return res.status(200)
            .cookie("Token",Token, options)
            .json({
                message: 'logged in successfully',
                data: user,
                authToken:Token
            })
    } catch (error) {
        // console.log(error.message);
        throw new ErrorHandler(error.message,error.statusCode || 500);
    }
})