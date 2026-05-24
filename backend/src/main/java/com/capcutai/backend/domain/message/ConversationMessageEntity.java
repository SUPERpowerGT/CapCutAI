package com.capcutai.backend.domain.message;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;

import java.time.OffsetDateTime;

@Entity
@Table(name = "conversation_messages")
public class ConversationMessageEntity {

    @Id
    @Column(name = "message_id", nullable = false, updatable = false, length = 64)
    private String messageId;

    @Column(name = "conversation_id", nullable = false, length = 64)
    private String conversationId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private MessageRole role;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private MessageStatus status;

    @Column(name = "trace_json", columnDefinition = "TEXT")
    private String traceJson;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    void onCreate() {
        createdAt = OffsetDateTime.now();
    }

    public String getMessageId() {
        return messageId;
    }

    public void setMessageId(String messageId) {
        this.messageId = messageId;
    }

    public String getConversationId() {
        return conversationId;
    }

    public void setConversationId(String conversationId) {
        this.conversationId = conversationId;
    }

    public MessageRole getRole() {
        return role;
    }

    public void setRole(MessageRole role) {
        this.role = role;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public MessageStatus getStatus() {
        return status;
    }

    public void setStatus(MessageStatus status) {
        this.status = status;
    }

    public String getTraceJson() {
        return traceJson;
    }

    public void setTraceJson(String traceJson) {
        this.traceJson = traceJson;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
