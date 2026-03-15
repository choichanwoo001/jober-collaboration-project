package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * 비동기 실행용 스레드 풀 설정.
 * 카테고리 사용량 증가 등에서 동시 DB 호출 수를 제한해 커넥션 풀 고갈을 방지.
 */
@Configuration
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(8);
        executor.setMaxPoolSize(32);
        executor.setQueueCapacity(2000);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}
