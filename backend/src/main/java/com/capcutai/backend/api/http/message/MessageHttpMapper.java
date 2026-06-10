package com.capcutai.backend.api.http.message;

import com.capcutai.backend.api.http.message.dto.MessageHttpResponse;
import com.capcutai.backend.api.http.message.dto.SendMessageHttpResponse;
import com.capcutai.backend.application.message.dto.MessageView;
import com.capcutai.backend.application.message.dto.SendMessageResult;

import java.util.List;

final class MessageHttpMapper {

    private MessageHttpMapper() {
    }

    static MessageHttpResponse toHttpResponse(MessageView view) {
        return new MessageHttpResponse(
                view.messageId(),
                view.conversationId(),
                view.role(),
                view.content(),
                view.status(),
                view.trace(),
                view.createdAt()
        );
    }

    static List<MessageHttpResponse> toHttpResponseList(List<MessageView> views) {
        return views.stream().map(MessageHttpMapper::toHttpResponse).toList();
    }

    static SendMessageHttpResponse toHttpResponse(SendMessageResult result) {
        return new SendMessageHttpResponse(
                result.conversationId(),
                toHttpResponse(result.userMessage()),
                toHttpResponse(result.assistantMessage()),
                result.agentStatus(),
                result.artifacts()
        );
    }
}
