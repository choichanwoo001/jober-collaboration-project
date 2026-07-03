package com.example.service;

import com.example.common.metric.ExecutionMetric;
import com.example.common.metric.ExecutionMetricCollector;
import com.example.dto.ExecutionMetricSnapshot;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ExecutionMetricService {

    private final ExecutionMetricCollector metricCollector;

    // API 메트릭 조회 (Slow 기준: 500ms)
    public ExecutionMetricSnapshot getApiMetrics() {
        List<ExecutionMetric> apiMetrics = metricCollector.getAll().stream()
                .filter(m -> "API".equals(m.getLayer()))
                .toList();
        return aggregate(apiMetrics, 500);
    }

    // DB 메트릭 조회 (Slow 기준: 200ms)
    public ExecutionMetricSnapshot getDbMetrics() {
        List<ExecutionMetric> dbMetrics = metricCollector.getAll().stream()
                .filter(m -> "DB".equals(m.getLayer()))
                .toList();
        return aggregate(dbMetrics, 200);
    }

    private ExecutionMetricSnapshot aggregate(List<ExecutionMetric> metrics, long slowThreshold) {
        if (metrics.isEmpty()) {
            return new ExecutionMetricSnapshot(0, 0, 0, 0);
        }

        long count = metrics.size();
        
        // 평균 계산
        long avg = (long) metrics.stream()
                .mapToLong(ExecutionMetric::getTimeMs)
                .average()
                .orElse(0);

        // P95 계산 (상위 95% 지점의 소요 시간)
        List<Long> sortedTimes = metrics.stream()
                .map(ExecutionMetric::getTimeMs)
                .sorted()
                .toList();
        
        int p95Index = (int) Math.ceil(count * 0.95) - 1;
        long p95 = sortedTimes.get(Math.max(p95Index, 0));

        // 느린 요청 개수 계산
        long slowCount = metrics.stream()
                .filter(m -> m.getTimeMs() >= slowThreshold)
                .count();

        return new ExecutionMetricSnapshot(count, avg, p95, slowCount);
    }
}
