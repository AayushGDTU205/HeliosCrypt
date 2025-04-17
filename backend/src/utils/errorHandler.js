class ErrorHandler extends Error{
    constructor(message="server issue", statusCode) {
        super(message);
        this.message = message;
        this.statusCode = statusCode;
        this.status = false;
    }
}

export default ErrorHandler;