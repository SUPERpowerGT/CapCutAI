package com.capcutai.backend.infrastructure.http;

import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.http")
public class HttpAccessProperties {

    private List<String> allowedOriginPatterns = new ArrayList<>(
            List.of(
                    "http://localhost:*",
                    "http://127.0.0.1:*",
                    "http://tauri.localhost",
                    "https://tauri.localhost",
                    "tauri://localhost"
            )
    );

    public List<String> getAllowedOriginPatterns() {
        return allowedOriginPatterns;
    }

    public void setAllowedOriginPatterns(List<String> allowedOriginPatterns) {
        this.allowedOriginPatterns = allowedOriginPatterns;
    }
}
