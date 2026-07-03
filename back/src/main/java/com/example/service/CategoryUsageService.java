package com.example.service;

import com.example.repository.CategoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.CannotAcquireLockException;
import org.springframework.dao.DeadlockLoserDataAccessException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.concurrent.ThreadLocalRandom;

/**
 * 카테고리 사용량 증가는 "부가 지표" 성격이라,
 * 템플릿 저장 트랜잭션과 분리하여(best-effort) 데드락 영향도를 낮춥니다.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CategoryUsageService {

    private final CategoryRepository categoryRepository;

    /**
     * 데드락/락 경합 시 짧게 재시도합니다(지수 백오프 + jitter).
     * 실패해도 본 트랜잭션을 망치지 않도록 예외를 밖으로 던지지 않습니다.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void incrementUsageBestEffort(String categoryName) {
        if (categoryName == null || categoryName.trim().isEmpty()) {
            return;
        }

        final String trimmed = categoryName.trim();
        final int maxAttempts = 4;

        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                int updated = categoryRepository.incrementUsageCountByName(trimmed);
                if (updated == 0) {
                    // 카테고리가 없으면 증가 대상이 없음 (생성은 다른 로직에서 처리)
                    log.debug("Category usage increment skipped (not found): {}", trimmed);
                }
                return;
            } catch (DeadlockLoserDataAccessException | CannotAcquireLockException e) {
                if (attempt == maxAttempts) {
                    log.warn("Category usage increment failed after retries (ignored): {}", trimmed, e);
                    return;
                }

                // 지수 백오프(20ms, 40ms, 80ms...) + jitter(0~20ms)
                long baseMs = 20L * (1L << (attempt - 1));
                long jitterMs = ThreadLocalRandom.current().nextLong(0, 21);
                long sleepMs = baseMs + jitterMs;

                log.debug("Deadlock/lock on category usage increment. attempt={}/{} sleep={}ms name={}",
                        attempt, maxAttempts, sleepMs, trimmed);

                try {
                    Thread.sleep(sleepMs);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    return;
                }
            } catch (Exception e) {
                log.warn("Category usage increment error (ignored): {}", trimmed, e);
                return;
            }
        }
    }
}

