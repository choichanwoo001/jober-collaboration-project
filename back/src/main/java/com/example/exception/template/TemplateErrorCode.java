package com.example.exception.template;

import com.example.exception.base.ErrorCode;

public enum TemplateErrorCode implements ErrorCode {

    TEMPLATE_SAVE_FAIL(
            "TEMPLATE_001",
            "템플릿 저장에 실패했습니다.",
            500
    ),

    TEMPLATE_VALIDATE_FAIL(
            "TEMPLATE_002",
            "템플릿 검증 중 오류가 발생했습니다.",
            500
    ),

    CATEGORY_CREATE_FAILED(
            "TEMPLATE_003",
            "카테고리 생성 중 오류가 발생했습니다.",
            500
    ),

    CATEGORY_INVALID(
            "TEMPLATE_004",
            "카테고리 정보가 올바르지 않습니다.",
            400
    ),

    TEMPLATE_NOT_FOUND(
            "TEMPLATE_005",
            "템플릿을 찾을 수 없습니다.",
            404
    ),

    TEMPLATE_OWNERSHIP_MISMATCH(
            "TEMPLATE_006",
            "템플릿 소유자가 아닙니다.",
            403
    ),

    TEMPLATE_ID_REQUIRED(
            "TEMPLATE_007",
            "템플릿 ID가 필요합니다. 업데이트하려면 templateId를 제공해주세요.",
            400
    );

    private final String code;
    private final String message;
    private final int status;

    TemplateErrorCode(String code, String message, int status) {
        this.code = code;
        this.message = message;
        this.status = status;
    }

    @Override public String getCode() { return code; }
    @Override public String getMessage() { return message; }
    @Override public int getStatus() { return status; }
}


