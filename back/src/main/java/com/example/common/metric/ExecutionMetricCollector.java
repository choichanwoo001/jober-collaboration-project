package com.example.common.metric;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Component
@Slf4j
public class ExecutionMetricCollector {

    private final List<ExecutionMetric> metrics = new CopyOnWriteArrayList<>();

    public void collect(ExecutionMetric metric) {
        metrics.add(metric);
    }
    public List<ExecutionMetric> getAll() {
        return List.copyOf(metrics);
    }
}