package com.capcutai.backend.infrastructure.agent;

import com.capcutai.backend.infrastructure.agent.dto.AgentRespondRequest;
import com.capcutai.backend.infrastructure.agent.dto.AgentRespondResponse;
import com.capcutai.backend.shared.error.ExternalServiceException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@Component
public class AiServiceClient {

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final String baseUrl;

    public AiServiceClient(
            ObjectMapper objectMapper,
            AiServiceProperties properties
    ) {
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .build();
        this.objectMapper = objectMapper;
        this.baseUrl = properties.baseUrl();
    }

    public AgentRespondResponse respond(AgentRespondRequest request) {
        try {
            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/internal/agent/respond"))
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(request)))
                    .build();

            HttpResponse<String> response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 400) {
                throw new ExternalServiceException(
                        "ai-service",
                        "request failed: " + response.statusCode() + " " + response.body()
                );
            }

            return objectMapper.readValue(response.body(), AgentRespondResponse.class);
        } catch (JsonProcessingException exception) {
            throw new ExternalServiceException("ai-service", "failed to serialize or parse payload");
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new ExternalServiceException("ai-service", "request interrupted");
        } catch (IOException exception) {
            throw new ExternalServiceException("ai-service", "request failed");
        }
    }
}
