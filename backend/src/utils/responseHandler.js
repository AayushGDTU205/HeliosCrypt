export const ResponseHandler = (func) => {
    return async (req, res, next) => {
        try {
            await func(req, res, next);
        }
        catch(error) {
            res.status(error.statusCode || 500).json({
                success: false,
                message:error.message
            })
        }
    }
}