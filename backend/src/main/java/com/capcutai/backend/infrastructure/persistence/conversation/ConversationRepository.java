package com.capcutai.backend.infrastructure.persistence.conversation;

import com.capcutai.backend.domain.conversation.ConversationEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ConversationRepository extends JpaRepository<ConversationEntity, String> {
    List<ConversationEntity> findAllByOrderByUpdatedAtDesc();
    List<ConversationEntity> findAllByWorkspaceIdOrderByUpdatedAtDesc(String workspaceId);
}
