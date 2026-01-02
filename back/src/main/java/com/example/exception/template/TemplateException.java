package com.example.exception.template;
import com.example.exception.base.BusinessException;

public class TemplateException extends BusinessException {

    public TemplateException(TemplateErrorCode errorCode) {
        super(errorCode);
    }
}
