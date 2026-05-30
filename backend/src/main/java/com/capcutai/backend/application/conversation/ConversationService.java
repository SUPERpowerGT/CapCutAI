package com.capcutai.backend.application.conversation;

import com.capcutai.backend.application.conversation.dto.ConversationView;
import com.capcutai.backend.application.conversation.dto.CreateConversationRequest;
import com.capcutai.backend.domain.conversation.ConversationEntity;
import com.capcutai.backend.domain.conversation.ConversationStatus;
import com.capcutai.backend.infrastructure.persistence.conversation.ConversationRepository;
import com.capcutai.backend.infrastructure.persistence.message.ConversationMessageRepository;
import com.capcutai.backend.shared.error.ResourceNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Service
public class ConversationService {

    private final ConversationRepository conversationRepository;
    private final ConversationMessageRepository conversationMessageRepository;

    public ConversationService(
            ConversationRepository conversationRepository,
            ConversationMessageRepository conversationMessageRepository
    ) {
        this.conversationRepository = conversationRepository;
        this.conversationMessageRepository = conversationMessageRepository;
    }

    @Transactional
    public ConversationView createConversation(CreateConversationRequest request) {
        ConversationEntity entity = new ConversationEntity();
        entity.setConversationId("conv_" + UUID.randomUUID());
        entity.setUserId(resolveUserId(request.userId()));
        entity.setSessionId(resolveSessionId(request.sessionId()));
        entity.setWorkspaceId(resolveWorkspaceId(request.workspaceId()));
        entity.setTitle(request.title() == null || request.title().isBlank() ? "New Conversation" : request.title());
        entity.setStatus(ConversationStatus.ACTIVE);
        return toView(conversationRepository.save(entity));
    }

    @Transactional(readOnly = true)
    public List<ConversationView> listConversations(String workspaceId) {
        List<ConversationEntity> entities = workspaceId == null || workspaceId.isBlank()
                ? conversationRepository.findAllByOrderByUpdatedAtDesc()
                : conversationRepository.findAllByWorkspaceIdOrderByUpdatedAtDesc(workspaceId);

        return entities
                .stream()
                .map(this::toView)
                .toList();
    }

    @Transactional(readOnly = true)
    public ConversationEntity requireConversation(String conversationId) {
        return conversationRepository.findById(conversationId)
                .orElseThrow(() -> new ResourceNotFoundException("Conversation", conversationId));
    }

    @Transactional
    public void touchConversation(String conversationId) {
        ConversationEntity entity = requireConversation(conversationId);
        entity.setUpdatedAt(OffsetDateTime.now());
        conversationRepository.save(entity);
    }

    @Transactional
    public void deleteConversation(String conversationId) {
        ConversationEntity entity = requireConversation(conversationId);
        conversationMessageRepository.deleteByConversationId(conversationId);
        conversationRepository.delete(entity);
    }

    private ConversationView toView(ConversationEntity entity) {
        return new ConversationView(
                entity.getConversationId(),
                entity.getUserId(),
                entity.getSessionId(),
                entity.getWorkspaceId(),
                entity.getTitle(),
                entity.getStatus().name(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    private String resolveUserId(String userId) {
        return userId == null || userId.isBlank()
                ? "user_anon_" + UUID.randomUUID()
                : userId;
    }

    private String resolveSessionId(String sessionId) {
        return sessionId == null || sessionId.isBlank()
                ? "sess_" + UUID.randomUUID()
                : sessionId;
    }

    private String resolveWorkspaceId(String workspaceId) {
        return workspaceId == null || workspaceId.isBlank()
                ? "workspace_" + UUID.randomUUID()
                : workspaceId;
    }
}
