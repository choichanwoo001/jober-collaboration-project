package com.example.service.password;

/**
 * 비밀번호 처리 추상화 인터페이스
 * 비밀번호 암호화, 검증, 업그레이드 등의 기능
 */
public interface PasswordService {

    /**
     * 평문 비밀번호를 암호화합니다.
     *
     * @param rawPassword 평문 비밀번호
     * @return 암호화된 비밀번호
     * @throws IllegalArgumentException rawPassword가 null이거나 비어있는 경우
     */
    String encode(String rawPassword);

    /**
     * 평문 비밀번호와 암호화된 비밀번호가 일치하는지 검증합니다.
     *
     * @param rawPassword      평문 비밀번호
     * @param encodedPassword  암호화된 비밀번호
     * @return 일치하면 true, 그렇지 않으면 false
     */
    boolean matches(String rawPassword, String encodedPassword);
}

