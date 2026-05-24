package com.capcutai.backend.application.message;

import com.capcutai.backend.application.message.dto.MessageView;
import com.capcutai.backend.domain.message.ConversationMessageEntity;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Collections;
import java.util.List;

final class MessageViewMapper {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private MessageViewMapper() {
    }

    static MessageView toView(ConversationMessageEntity entity) {
        return new MessageView(
                entity.getMessageId(),
                entity.getConversationId(),
                entity.getRole().name(),
                entity.getContent(),
                entity.getStatus().name(),
                readTrace(entity.getTraceJson()),
                entity.getCreatedAt()
        );
    }

    private static List<String> readTrace(String traceJson) {
        if (traceJson == null || traceJson.isBlank()) {
            return List.of();
        }

        try {
            return OBJECT_MAPPER.readValue(traceJson, new TypeReference<>() {
            });
        } catch (JsonProcessingException exception) {
            return Collections.emptyList();
        }
    }
}
