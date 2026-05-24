package com.capcutai.backend.api.http.conversation;

import com.capcutai.backend.api.http.conversation.dto.ConversationHttpResponse;
import com.capcutai.backend.api.http.conversation.dto.CreateConversationHttpRequest;
import com.capcutai.backend.application.conversation.dto.ConversationView;
import com.capcutai.backend.application.conversation.dto.CreateConversationRequest;

import java.util.List;

final class ConversationHttpMapper {

    private ConversationHttpMapper() {
    }

    static CreateConversationRequest toApplicationRequest(CreateConversationHttpRequest request) {
        if (request == null) {
            return new CreateConversationRequest(null, null, null);
        }
        return new CreateConversationRequest(
                request.userId(),
                request.sessionId(),
                request.title()
        );
    }

    static ConversationHttpResponse toHttpResponse(ConversationView view) {
        return new ConversationHttpResponse(
                view.conversationId(),
                view.userId(),
                view.sessionId(),
                view.title(),
                view.status(),
                view.createdAt(),
                view.updatedAt()
        );
    }

    static List<ConversationHttpResponse> toHttpResponseList(List<ConversationView> views) {
        return views.stream().map(ConversationHttpMapper::toHttpResponse).toList();
    }
}
