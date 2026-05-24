package com.capcutai.backend.shared.error;

import org.springframework.http.HttpStatus;

public abstract class BackendException extends RuntimeException {

    private final String errorCode;
    private final HttpStatus httpStatus;

    protected BackendException(String errorCode, HttpStatus httpStatus, String message) {
        super(message);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public HttpStatus getHttpStatus() {
        return httpStatus;
    }
}
