package com.example.exception.base;

public interface ErrorCode {
    String getCode();           // USER_001, TEMPLATE_003
    String getMessage();        // 사람이 읽을 메시지
    int getStatus();            // HTTP 상태코드
}
