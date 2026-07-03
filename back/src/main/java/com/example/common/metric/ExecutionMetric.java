package com.example.common.metric;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ExecutionMetric {
    private final String layer;   // DB / API
    private final String target;  // 클래스.메소드
    private final long timeMs;
    private final boolean success;
}

