import e from "express";
import { postLogin, postSignup } from "../controller/login.js";
let loginRouter = e.Router();
import passport from "passport";
import { Strategy as GoogleStrategy } from 'passport-google-oauth20';
import User from "../model/user.js";
import jwt from "jsonwebtoken";
import ErrorHandler from "../utils/errorHandler.js";
import dotenv from 'dotenv';
dotenv.config();

loginRouter.post('/signup', postSignup);
loginRouter.post('/login', postLogin);


passport.use(new GoogleStrategy(
    {
        clientID: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        callbackURL: "http://localhost:4444/auth/google/callback"  // Ensure this matches the Google console redirect URI
    }, 
    async (accessToken, refreshToken, profile, done) => {
        try {
            let user = await User.findOne({ googleId: profile.id });

            if (!user) {
                user = await User.findOne({ email: profile.emails[0].value });

                if (user) {
                    user.googleId = profile.id;
                    user.name = profile.displayName;
                    user.profilePicture = profile.photos[0].value;
                    await user.save();
                } else {
                    user = await User.create({
                        googleId: profile.id,
                        email: profile.emails[0].value,
                        name: profile.displayName,
                        profilePicture: profile.photos[0].value
                    });
                }
            }

            const token = jwt.sign({ email: user.email }, process.env.AccKey, { expiresIn: '7d' });
            done(null, { user, token });

        } catch (err) {
            done(err, null);
        }
    }
));

loginRouter.get('/auth/google', passport.authenticate('google', { scope: ['profile', 'email'] }));

loginRouter.get('/auth/google/callback', 
    (req, res, next) => {
        passport.authenticate('google', (err, user, info) => {
            if (err) {
                console.log(err);
                return next(new ErrorHandler('Server error, please try again', 500));
            }

            if (!user) {
                return next(new ErrorHandler('Google authorization failed', 400));
            }

            const { token } = user;

            res.status(200)
                .cookie("Token", token, { httpOnly: true, secure: true, sameSite: 'none' })
                .redirect('http://localhost:3000/app');  // Redirect to your React app
        })(req, res, next);
    }
);



export default loginRouter;