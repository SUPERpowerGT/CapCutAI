package com.capcutai.backend.api.http.conversation;

import com.capcutai.backend.api.http.common.ApiResponse;
import com.capcutai.backend.api.http.conversation.dto.ConversationHttpResponse;
import com.capcutai.backend.api.http.conversation.dto.CreateConversationHttpRequest;
import com.capcutai.backend.application.conversation.ConversationService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/conversations")
public class ConversationController {

    private final ConversationService conversationService;

    public ConversationController(ConversationService conversationService) {
        this.conversationService = conversationService;
    }

    @PostMapping
    public ApiResponse<ConversationHttpResponse> createConversation(
            @Valid @RequestBody(required = false) CreateConversationHttpRequest request
    ) {
        return ApiResponse.success(
                ConversationHttpMapper.toHttpResponse(
                        conversationService.createConversation(
                                ConversationHttpMapper.toApplicationRequest(request)
                        )
                )
        );
    }

    @GetMapping
    public ApiResponse<List<ConversationHttpResponse>> listConversations() {
        return ApiResponse.success(
                ConversationHttpMapper.toHttpResponseList(conversationService.listConversations())
        );
    }

    @DeleteMapping("/{conversationId}")
    public ApiResponse<Void> deleteConversation(@PathVariable String conversationId) {
        conversationService.deleteConversation(conversationId);
        return ApiResponse.success(null);
    }
}
