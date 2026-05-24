package com.capcutai.backend.application.conversation.dto;

import java.time.OffsetDateTime;

public record ConversationView(
        String conversationId,
        String userId,
        String sessionId,
        String title,
        String status,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
) {
}
