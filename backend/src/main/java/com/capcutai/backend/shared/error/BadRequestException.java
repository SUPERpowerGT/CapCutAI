package com.capcutai.backend.shared.error;

import org.springframework.http.HttpStatus;

public class BadRequestException extends BackendException {

    public BadRequestException(String message) {
        super("BAD_REQUEST", HttpStatus.BAD_REQUEST, message);
    }
}
