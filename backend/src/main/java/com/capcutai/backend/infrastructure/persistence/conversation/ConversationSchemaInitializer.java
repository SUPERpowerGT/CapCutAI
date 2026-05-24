package com.capcutai.backend.infrastructure.persistence.conversation;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class ConversationSchemaInitializer implements ApplicationRunner {

    private final JdbcTemplate jdbcTemplate;

    public ConversationSchemaInitializer(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void run(ApplicationArguments args) {
        jdbcTemplate.execute("""
                ALTER TABLE conversations
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(64)
                """);
        jdbcTemplate.execute("""
                ALTER TABLE conversations
                ADD COLUMN IF NOT EXISTS session_id VARCHAR(64)
                """);
        jdbcTemplate.execute("""
                UPDATE conversations
                SET user_id = COALESCE(user_id, 'user_legacy_unknown'),
                    session_id = COALESCE(session_id, 'sess_legacy_unknown')
                WHERE user_id IS NULL OR session_id IS NULL
                """);
    }
}
