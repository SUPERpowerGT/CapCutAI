package com.capcutai.backend.application.message.dto;

public record SendMessageResult(
        String conversationId,
        MessageView userMessage,
        MessageView assistantMessage,
        String agentStatus
) {
}
