package com.capcutai.backend.api.http.message.dto;

public record SendMessageHttpResponse(
        String conversationId,
        MessageHttpResponse userMessage,
        MessageHttpResponse assistantMessage,
        String agentStatus
) {
}
