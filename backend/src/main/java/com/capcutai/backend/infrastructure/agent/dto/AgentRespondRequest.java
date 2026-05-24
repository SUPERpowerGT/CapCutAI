package com.capcutai.backend.infrastructure.agent.dto;

import java.util.List;
import java.util.Map;

public record AgentRespondRequest(
        String conversationId,
        List<AgentMessagePayload> messages,
        Map<String, Object> context
) {
}
