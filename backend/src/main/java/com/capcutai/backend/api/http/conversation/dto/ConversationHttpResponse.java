package com.capcutai.backend.api.http.conversation.dto;

import java.time.OffsetDateTime;

public record ConversationHttpResponse(
        String conversationId,
        String userId,
        String sessionId,
        String title,
        String status,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
) {
}
