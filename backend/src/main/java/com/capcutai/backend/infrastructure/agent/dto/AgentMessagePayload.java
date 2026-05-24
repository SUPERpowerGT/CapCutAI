package com.capcutai.backend.infrastructure.agent.dto;

public record AgentMessagePayload(
        String role,
        String content
) {
}
