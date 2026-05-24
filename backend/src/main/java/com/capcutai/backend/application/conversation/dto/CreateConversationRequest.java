package com.capcutai.backend.application.conversation.dto;

import jakarta.validation.constraints.Size;

public record CreateConversationRequest(
        @Size(max = 64)
        String userId,
        @Size(max = 64)
        String sessionId,
        @Size(max = 255)
        String title
) {
}
