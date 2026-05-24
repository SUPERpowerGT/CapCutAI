package com.capcutai.backend.shared.error;

import org.springframework.http.HttpStatus;

public class ResourceNotFoundException extends BackendException {

    public ResourceNotFoundException(String resourceType, String resourceId) {
        super(
                "RESOURCE_NOT_FOUND",
                HttpStatus.NOT_FOUND,
                resourceType + " not found: " + resourceId
        );
    }
}
