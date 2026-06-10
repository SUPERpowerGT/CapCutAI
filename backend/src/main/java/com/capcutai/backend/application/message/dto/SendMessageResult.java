package com.capcutai.backend.application.message.dto;

import java.util.Map;

public record SendMessageResult(
        String conversationId,
        MessageView userMessage,
        MessageView assistantMessage,
        String agentStatus,
        Map<String, Object> artifacts
) {
}
