package com.capcutai.backend.infrastructure.agent;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.ai-service")
public record AiServiceProperties(
        String baseUrl
) {
}
