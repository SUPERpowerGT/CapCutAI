package com.capcutai.backend.infrastructure.agent.dto;

import java.util.List;
import java.util.Map;

public record AgentRespondResponse(
        AgentReplyPayload reply,
        String status,
        List<String> trace,
        Map<String, Object> artifacts
) {
}
