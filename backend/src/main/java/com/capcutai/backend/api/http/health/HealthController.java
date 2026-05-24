package com.capcutai.backend.api.http.health;

import com.capcutai.backend.api.http.common.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class HealthController {

    @GetMapping("/health")
    public ApiResponse<Map<String, Object>> health() {
        return ApiResponse.success(Map.of(
                "service", "capcutai-backend",
                "status", "UP",
                "timestamp", OffsetDateTime.now().toString()
        ));
    }
}
