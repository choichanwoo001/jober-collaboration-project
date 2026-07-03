package com.example.exception.external;

import com.example.exception.base.ErrorCode;

public enum ExternalErrorCode implements ErrorCode {

    AI_SERVER_TIMEOUT("EXT_001", "AI 서버 응답이 지연되고 있습니다.", 504),
    AI_SERVER_ERROR("EXT_002", "AI 서버 처리 중 오류가 발생했습니다.", 502),
    AI_RESPONSE_INVALID("EXT_003", "AI 서버 응답 형식이 올바르지 않습니다.", 502);

    private final String code;
    private final String message;
    private final int status;

    ExternalErrorCode(String code, String message, int status) {
        this.code = code;
        this.message = message;
        this.status = status;
    }

    @Override public String getCode() { return code; }
    @Override public String getMessage() { return message; }
    @Override public int getStatus() { return status; }
}

