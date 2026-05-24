package com.capcutai.backend.application.message.dto;

import java.time.OffsetDateTime;
import java.util.List;

public record MessageView(
        String messageId,
        String conversationId,
        String role,
        String content,
        String status,
        List<String> trace,
        OffsetDateTime createdAt
) {
}
