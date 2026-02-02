package com.example.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ExecutionMetricSnapshot {
    private long count;
    private long avgMs;
    private long p95Ms;
    private long slowCount;
}