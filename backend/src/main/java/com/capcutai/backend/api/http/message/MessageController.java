package com.capcutai.backend.api.http.message;

import com.capcutai.backend.api.http.common.ApiResponse;
import com.capcutai.backend.api.http.message.dto.MessageHttpResponse;
import com.capcutai.backend.api.http.message.dto.SendMessageHttpRequest;
import com.capcutai.backend.api.http.message.dto.SendMessageHttpResponse;
import com.capcutai.backend.application.conversation.ConversationService;
import com.capcutai.backend.application.message.MessageQueryService;
import com.capcutai.backend.application.message.SendMessageUseCase;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/conversations/{conversationId}/messages")
public class MessageController {

    private final ConversationService conversationService;
    private final MessageQueryService messageQueryService;
    private final SendMessageUseCase sendMessageUseCase;

    public MessageController(
            ConversationService conversationService,
            MessageQueryService messageQueryService,
            SendMessageUseCase sendMessageUseCase
    ) {
        this.conversationService = conversationService;
        this.messageQueryService = messageQueryService;
        this.sendMessageUseCase = sendMessageUseCase;
    }

    @GetMapping
    public ApiResponse<List<MessageHttpResponse>> listMessages(@PathVariable String conversationId) {
        conversationService.requireConversation(conversationId);
        return ApiResponse.success(
                MessageHttpMapper.toHttpResponseList(messageQueryService.listMessages(conversationId))
        );
    }

    @PostMapping
    public ApiResponse<SendMessageHttpResponse> sendMessage(
            @PathVariable String conversationId,
            @Valid @RequestBody SendMessageHttpRequest request
    ) {
        return ApiResponse.success(
                MessageHttpMapper.toHttpResponse(
                        sendMessageUseCase.execute(conversationId, request.content())
                )
        );
    }
}
