package com.example.service;

import com.example.dto.VariableDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.stream.Collectors;

/**
 * 템플릿 변수 관련 로직을 처리하는 유틸리티 컴포넌트
 * 변수 추출, 정규화, 필터링 등의 책임을 가짐
 */
@Slf4j
@Component
public class TemplateVariableResolver {

    private static final Pattern VAR_PATTERN = Pattern.compile("\\{\\{([^}]+)\\}\\}");

    /**
     * 템플릿 내용에서 실제로 사용된 변수명을 추출합니다.
     * {{변수명}} 형태의 패턴으로 변수를 찾습니다.
     * 
     * @param templateContent 템플릿 내용
     * @return 템플릿에 실제로 사용된 변수명 Set (중복 제거됨)
     */
    public Set<String> extractActualVariables(String templateContent) {
        if (templateContent == null || templateContent.isBlank()) {
            return Set.of();
        }

        Set<String> variables = new HashSet<>();
        Matcher matcher = VAR_PATTERN.matcher(templateContent);

        while (matcher.find()) {
            String variableName = matcher.group(1).trim();
            if (!variableName.isEmpty()) {
                variables.add(variableName);
            }
        }

        log.debug("템플릿에서 추출된 변수: {}", variables);
        return variables;
    }

    /**
     * VariableDto 리스트에서 변수명(key)을 추출하고 정규화합니다.
     * null/blank 제거 및 중복 제거를 수행합니다.
     * 
     * @param variableList VariableDto 리스트
     * @return 정규화된 변수명 리스트 (순서 유지)
     */
    public List<String> resolveKeys(List<VariableDto> variableList) {
        if (variableList == null) {
            return List.of();
        }

        return variableList.stream()
                .map(VariableDto::key)
                .filter(Objects::nonNull)
                .filter(key -> !key.isBlank())
                .distinct()
                .collect(Collectors.toList());
    }

    /**
     * 요청된 변수명 중에서 실제로 템플릿에 사용된 변수만 필터링합니다.
     * 
     * @param keys 요청된 변수명 리스트
     * @param actualVars 템플릿에 실제로 사용된 변수 Set
     * @return 템플릿에 실제로 사용된 변수만 포함한 리스트
     */
    public List<String> filterOnlyUsed(List<String> keys, Set<String> actualVars) {
        if (keys == null) {
            return List.of();
        }
        return keys.stream()
                .filter(actualVars::contains)
                .collect(Collectors.toList());
    }
}
