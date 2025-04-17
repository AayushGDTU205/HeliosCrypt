import mongoose from 'mongoose';
const { Schema } = mongoose;

const userSchema = new Schema({
    password: {
        type: String,
        required: function () {
            !this.googleId;
        }
    },
    email: {
        type: String,
        unique: true,
        required: true
    },
    googleId: {
        type: String,
        required: false
    },
    googleAccessToken: {
        type: String,
        required: false
    },
    name: {
        type: String,
        required: true
    },
    profilePicture: {
        type: String
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

const User = mongoose.model('User', userSchema);
export default User;