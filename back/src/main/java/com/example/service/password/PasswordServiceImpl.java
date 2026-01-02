package com.example.service.password;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

/**
 * 비밀번호 처리 서비스 구현체
 * PasswordEncoder를 내부적으로 사용하여 비밀번호 암호화 및 검증을 수행
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PasswordServiceImpl implements PasswordService {

    private final PasswordEncoder passwordEncoder;

    @Override
    public String encode(String rawPassword) {
        if (rawPassword == null || rawPassword.isBlank()) {
            throw new IllegalArgumentException("비밀번호는 비어 있을 수 없습니다.");
        }

        log.debug("비밀번호 암호화 수행");
        return passwordEncoder.encode(rawPassword);
    }

    @Override
    public boolean matches(String rawPassword, String encodedPassword) {
        if (rawPassword == null || encodedPassword == null) {
            log.warn("비밀번호 검증 실패: null 값이 포함되어 있습니다.");
            return false;
        }

        boolean matches = passwordEncoder.matches(rawPassword, encodedPassword);
        if (!matches) {
            log.debug("비밀번호 검증 실패");
        }
        return matches;
    }
}
