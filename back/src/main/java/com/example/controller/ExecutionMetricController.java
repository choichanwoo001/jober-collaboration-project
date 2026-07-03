package com.example.controller;

import com.example.dto.ExecutionMetricSnapshot;
import com.example.service.ExecutionMetricService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/metrics")
@RequiredArgsConstructor
public class ExecutionMetricController {

    private final ExecutionMetricService metricService;

    @GetMapping("/api")
    public ExecutionMetricSnapshot getApiMetrics() {
        return metricService.getApiMetrics();
    }

    @GetMapping("/db")
    public ExecutionMetricSnapshot getDbMetrics() {
        return metricService.getDbMetrics();
    }
}

