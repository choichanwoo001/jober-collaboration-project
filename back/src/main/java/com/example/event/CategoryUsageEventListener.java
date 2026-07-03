package com.example.event;

import com.example.service.CategoryUsageService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Slf4j
@Component
@RequiredArgsConstructor
public class CategoryUsageEventListener {

    private final CategoryUsageService categoryUsageService;

    /**
     * 템플릿 저장 트랜잭션 커밋 이후에(AfterCommit) 별도로 카테고리 사용량을 증가시킵니다.
     * 비동기로 처리하여 API 응답 지연/타임아웃 가능성을 줄입니다.
     */
    @Async("categoryUsageExecutor")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onCategoryUsed(CategoryUsageIncrementEvent event) {
        if (event == null) {
            return;
        }
        categoryUsageService.incrementUsageBestEffort(event.categoryName());
    }
}

