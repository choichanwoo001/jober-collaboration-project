package com.example.common.aspect;

import com.example.common.metric.ExecutionMetric;
import com.example.common.metric.ExecutionMetricCollector;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Aspect
@Component
@Slf4j
@RequiredArgsConstructor
public class DbExecutionTimeAspect {
    // 기준값 (DB는 보통 API보다 훨씬 타이트하게 잡음)
    private static final long SLOW_DB_THRESHOLD_MS = 200;
    private final ExecutionMetricCollector metricCollector;
    /**
     * repository 패키지 이하의 모든 메소드 실행 시간 측정
     */
    @Around("execution(* com.example.repository..*(..))")
    public Object measureRepositoryTime(ProceedingJoinPoint joinPoint) throws Throwable {

        long startTime = System.currentTimeMillis();
        boolean success = false;

        try {
            // 실제 Repository 메소드 실행
            Object result = joinPoint.proceed();
            success = true;
            return result;
        } finally {
            long elapsedTime = System.currentTimeMillis() - startTime;

            String target = joinPoint.getSignature().getDeclaringTypeName() + "." + joinPoint.getSignature().getName();

            metricCollector.collect(new ExecutionMetric("DB", target, elapsedTime, success));

            if (elapsedTime >= SLOW_DB_THRESHOLD_MS) {
                log.warn(
                        "[SLOW-DB] {}. took {}ms",
                        target,           // 메소드
                        elapsedTime
                );
            } else {
                log.debug(
                        "[DB] {}. took {}ms",
                        target,
                        elapsedTime
                );
            }
        }
    }
}
