import express from "express";
import mongoose from "mongoose";
import bodyParser from "body-parser";
import cookieParser from "cookie-parser";
import cors from "cors";
import loginRouter from "./routes/loginRouter.js";
import dotenv from 'dotenv';
dotenv.config();
import { verifyJWT } from "./middleware/verifyJWT.js";


const app = express();
const PORT = 4444;
app.use(cors({
    credentials: true,
    origin:'http://localhost:3000'
}))
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));
app.use(cookieParser());

app.use('/', loginRouter);
app.get('/test', verifyJWT, async(req,res,next) => {
    res.status(200).json({
        message:"succesful verification"
    })
})
// console.log(process.env.mongoConnect);
mongoose.connect(process.env.mongoConnect)
    .then(() => {
        app.listen(PORT, () => {
            console.log(`http://localhost:${PORT}`);
        })
    })
    .catch((err) => {
        console.log(err);
    })
