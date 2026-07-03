package com.example.exception.user;

import com.example.exception.base.ErrorCode;

public enum UserErrorCode implements ErrorCode {

    // === USER ===
    USER_NOT_FOUND("USER_001", "사용자를 찾을 수 없습니다.", 404),
    USER_ALREADY_EXISTS("USER_002", "이미 존재하는 사용자입니다.", 409),
    EMAIL_DUPLICATED("USER_003", "이미 존재하는 이메일입니다.", 409),
    INVALID_EMAIL_PASSWORD("USER_004", "이메일 또는 비밀번호가 올바르지 않습니다.", 400),

    // === TOKEN ===
    INVALID_TOKEN("USER_101", "유효하지 않은 토큰입니다.", 401),
    TOKEN_MISMATCH("USER_203", "토큰 정보가 일치하지 않습니다.", 401),
    EXPIRED_TOKEN("USER_102", "토큰이 만료되었습니다.", 401);

    private final String code;
    private final String message;
    private final int status;

    UserErrorCode(String code, String message, int status) {
        this.code = code;
        this.message = message;
        this.status = status;
    }

    @Override
    public String getCode() { return code; }

    @Override
    public String getMessage() { return message; }

    @Override
    public int getStatus() { return status; }
}

