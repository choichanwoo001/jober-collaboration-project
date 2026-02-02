package com.example.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 템플릿 변수를 표현하는 DTO
 * variableKey 또는 name 필드에서 변수명을 추출할 수 있음
 */
public record VariableDto(
    @JsonProperty("variableKey") String variableKey,
    @JsonProperty("name") String name,
    @JsonProperty("type") String type,
    @JsonProperty("description") String description
) {
    /**
     * 변수명을 추출합니다.
     * variableKey가 있으면 우선 사용하고, 없으면 name을 사용합니다.
     * 둘 다 없거나 비어있으면 null을 반환합니다.
     */
    public String key() {
        if (variableKey != null && !variableKey.isBlank()) {
            return variableKey.trim();
        }
        if (name != null && !name.isBlank()) {
            return name.trim();
        }
        return null;
    }
}
