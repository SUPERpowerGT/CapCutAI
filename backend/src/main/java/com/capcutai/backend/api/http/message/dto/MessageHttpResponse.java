package com.capcutai.backend.api.http.message.dto;

import java.time.OffsetDateTime;
import java.util.List;

public record MessageHttpResponse(
        String messageId,
        String conversationId,
        String role,
        String content,
        String status,
        List<String> trace,
        OffsetDateTime createdAt
) {
}
