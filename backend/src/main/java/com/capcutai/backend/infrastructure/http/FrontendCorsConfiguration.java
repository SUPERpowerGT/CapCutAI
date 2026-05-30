package com.capcutai.backend.infrastructure.http;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@EnableConfigurationProperties(HttpAccessProperties.class)
public class FrontendCorsConfiguration implements WebMvcConfigurer {

    private final HttpAccessProperties httpAccessProperties;

    public FrontendCorsConfiguration(HttpAccessProperties httpAccessProperties) {
        this.httpAccessProperties = httpAccessProperties;
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOriginPatterns(httpAccessProperties.getAllowedOriginPatterns().toArray(String[]::new))
                .allowedMethods("GET", "POST", "DELETE", "OPTIONS")
                .allowedHeaders("*");
    }
}
