package com.capcutai.backend.application.message;

import com.capcutai.backend.application.message.dto.MessageView;
import com.capcutai.backend.infrastructure.persistence.message.ConversationMessageRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class MessageQueryService {

    private final ConversationMessageRepository messageRepository;

    public MessageQueryService(ConversationMessageRepository messageRepository) {
        this.messageRepository = messageRepository;
    }

    @Transactional(readOnly = true)
    public List<MessageView> listMessages(String conversationId) {
        return messageRepository.findByConversationIdOrderByCreatedAtAsc(conversationId)
                .stream()
                .map(MessageViewMapper::toView)
                .toList();
    }
}
