package com.capcutai.backend.application.message;

import com.capcutai.backend.application.message.dto.MessageView;
import com.capcutai.backend.domain.message.ConversationMessageEntity;
import com.capcutai.backend.domain.message.MessageRole;
import com.capcutai.backend.domain.message.MessageStatus;
import com.capcutai.backend.infrastructure.persistence.message.ConversationMessageRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class MessageCommandService {

    private final ConversationMessageRepository messageRepository;
    private final ObjectMapper objectMapper;

    public MessageCommandService(
            ConversationMessageRepository messageRepository,
            ObjectMapper objectMapper
    ) {
        this.messageRepository = messageRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public MessageView createUserMessage(String conversationId, String content) {
        return save(conversationId, MessageRole.USER, content, MessageStatus.SUBMITTED, List.of());
    }

    @Transactional
    public MessageView createAssistantMessage(
            String conversationId,
            String content,
            MessageStatus status,
            List<String> trace
    ) {
        return save(conversationId, MessageRole.ASSISTANT, content, status, trace);
    }

    private MessageView save(
            String conversationId,
            MessageRole role,
            String content,
            MessageStatus status,
            List<String> trace
    ) {
        ConversationMessageEntity entity = new ConversationMessageEntity();
        entity.setMessageId("msg_" + UUID.randomUUID());
        entity.setConversationId(conversationId);
        entity.setRole(role);
        entity.setContent(content);
        entity.setStatus(status);
        entity.setTraceJson(writeTrace(trace));
        return MessageViewMapper.toView(messageRepository.save(entity));
    }

    private String writeTrace(List<String> trace) {
        try {
            return objectMapper.writeValueAsString(trace);
        } catch (JsonProcessingException exception) {
            return "[]";
        }
    }
}
