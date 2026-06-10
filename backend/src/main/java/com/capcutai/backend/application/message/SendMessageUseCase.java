package com.capcutai.backend.application.message;

import com.capcutai.backend.application.agent.AgentOrchestrationService;
import com.capcutai.backend.application.conversation.ConversationService;
import com.capcutai.backend.application.message.dto.MessageView;
import com.capcutai.backend.application.message.dto.SendMessageResult;
import com.capcutai.backend.domain.message.MessageStatus;
import com.capcutai.backend.infrastructure.agent.dto.AgentRespondResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;

@Service
public class SendMessageUseCase {

    private final ConversationService conversationService;
    private final MessageCommandService messageCommandService;
    private final MessageQueryService messageQueryService;
    private final AgentOrchestrationService agentOrchestrationService;

    public SendMessageUseCase(
            ConversationService conversationService,
            MessageCommandService messageCommandService,
            MessageQueryService messageQueryService,
            AgentOrchestrationService agentOrchestrationService
    ) {
        this.conversationService = conversationService;
        this.messageCommandService = messageCommandService;
        this.messageQueryService = messageQueryService;
        this.agentOrchestrationService = agentOrchestrationService;
    }

    @Transactional
    public SendMessageResult execute(
            String conversationId,
            String content,
            Map<String, Object> context
    ) {
        conversationService.requireConversation(conversationId);

        MessageView userMessage = messageCommandService.createUserMessage(conversationId, content);
        conversationService.touchConversation(conversationId);

        List<MessageView> messages = messageQueryService.listMessages(conversationId);
        AgentRespondResponse agentResponse = agentOrchestrationService.respond(
                conversationId,
                messages,
                context
        );

        MessageStatus assistantStatus = resolveAssistantStatus(agentResponse.status());
        MessageView assistantMessage = messageCommandService.createAssistantMessage(
                conversationId,
                agentResponse.reply().content(),
                assistantStatus,
                agentResponse.trace()
        );
        conversationService.touchConversation(conversationId);

        return new SendMessageResult(
                conversationId,
                userMessage,
                assistantMessage,
                agentResponse.status(),
                agentResponse.artifacts()
        );
    }

    private MessageStatus resolveAssistantStatus(String status) {
        try {
            return MessageStatus.valueOf(status);
        } catch (IllegalArgumentException | NullPointerException exception) {
            return MessageStatus.COMPLETED;
        }
    }
}
