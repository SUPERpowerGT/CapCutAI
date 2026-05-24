package com.capcutai.backend.infrastructure.agent.dto;

public record AgentReplyPayload(
        String role,
        String content
) {
}
