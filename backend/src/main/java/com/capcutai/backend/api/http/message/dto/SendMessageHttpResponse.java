package com.capcutai.backend.api.http.message.dto;

import java.util.Map;

public record SendMessageHttpResponse(
        String conversationId,
        MessageHttpResponse userMessage,
        MessageHttpResponse assistantMessage,
        String agentStatus,
        Map<String, Object> artifacts
) {
}
