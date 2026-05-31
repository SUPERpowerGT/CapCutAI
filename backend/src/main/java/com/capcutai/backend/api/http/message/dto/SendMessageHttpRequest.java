package com.capcutai.backend.api.http.message.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.Map;

public record SendMessageHttpRequest(
        @NotBlank
        @Size(max = 8000)
        String content,
        Map<String, Object> context
) {
}
