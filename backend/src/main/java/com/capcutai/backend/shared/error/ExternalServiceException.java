package com.capcutai.backend.shared.error;

import org.springframework.http.HttpStatus;

public class ExternalServiceException extends BackendException {

    public ExternalServiceException(String serviceName, String message) {
        super(
                "EXTERNAL_SERVICE_ERROR",
                HttpStatus.BAD_GATEWAY,
                serviceName + ": " + message
        );
    }
}
