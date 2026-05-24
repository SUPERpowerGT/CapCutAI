package com.capcutai.backend.infrastructure.persistence.message;

import com.capcutai.backend.domain.message.ConversationMessageEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ConversationMessageRepository extends JpaRepository<ConversationMessageEntity, String> {
    List<ConversationMessageEntity> findByConversationIdOrderByCreatedAtAsc(String conversationId);
    void deleteByConversationId(String conversationId);
}
