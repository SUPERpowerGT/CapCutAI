package com.capcutai.backend.api.http.conversation.dto;

public record CreateConversationHttpRequest(
        String userId,
        String sessionId,
        String workspaceId,
        String title
) {
}
