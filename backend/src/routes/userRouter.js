import e from "express";
let userRouter = e.Router();
import { verifyJWT } from "../middleware/verifyJWT.js";
import multer from "multer";
import { postBeforeAfter } from "../controller/user.js";

const upload = multer({ storage: multer.memoryStorage() });

userRouter.post('/BeforeAfter', verifyJWT, upload.fields([
    { name: 'image1', maxCount: 1 },
    { name: 'image2', maxCount: 1 }
]), postBeforeAfter);

export default userRouter;