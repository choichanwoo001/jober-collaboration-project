package com.example.common.aspect;

import com.example.common.metric.ExecutionMetric;
import com.example.common.metric.ExecutionMetricCollector;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ApiExecutionTimeAspect {

    private static final long SLOW_API_THRESHOLD_MS = 500;

    private final ExecutionMetricCollector metricCollector;

    @Around("execution(* com.example..controller..*(..))")
    public Object measureApiTime(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        boolean success = false;

        try {
            Object result = joinPoint.proceed();
            success = true;
            return result;
        } finally {
            long elapsed = System.currentTimeMillis() - start;

            String target = joinPoint.getSignature().toShortString();

            metricCollector.collect(
                    new ExecutionMetric("API", target, elapsed, success)
            );

            if (elapsed >= SLOW_API_THRESHOLD_MS) {
                log.warn(
                        "[SLOW-API] {} took {} ms",
                        target,
                        elapsed
                );
            } else {
                log.info(
                        "[API] {} took {} ms",
                        target,
                        elapsed
                );
            }
        }
    }
}
