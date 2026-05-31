package com.capcutai.backend.application.agent;

import com.capcutai.backend.application.message.dto.MessageView;
import com.capcutai.backend.infrastructure.agent.AiServiceClient;
import com.capcutai.backend.infrastructure.agent.dto.AgentMessagePayload;
import com.capcutai.backend.infrastructure.agent.dto.AgentRespondRequest;
import com.capcutai.backend.infrastructure.agent.dto.AgentRespondResponse;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class AgentOrchestrationService {

    private final AiServiceClient aiServiceClient;

    public AgentOrchestrationService(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    public AgentRespondResponse respond(
            String conversationId,
            List<MessageView> messages,
            Map<String, Object> context
    ) {
        List<AgentMessagePayload> payloadMessages = messages.stream()
                .map(message -> new AgentMessagePayload(
                        message.role().toLowerCase(),
                        message.content()
                ))
                .toList();

        Map<String, Object> payloadContext = new LinkedHashMap<>();
        payloadContext.put("source", "backend");
        if (context != null && !context.isEmpty()) {
            payloadContext.putAll(context);
        }

        return aiServiceClient.respond(new AgentRespondRequest(
                conversationId,
                payloadMessages,
                payloadContext
        ));
    }
}
