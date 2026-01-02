package com.example.exception;

import com.example.dto.ErrorResponse;
import com.example.exception.base.BusinessException;
import com.example.exception.base.ErrorCode;
import com.example.exception.template.TemplateException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Object> handleBusinessException(BusinessException e) {

        ErrorCode code = e.getErrorCode();

        ErrorResponse body = new ErrorResponse(
                code.getCode(),
                code.getMessage()
        );

        return ResponseEntity.status(code.getStatus()).body(body);
    }

    @ExceptionHandler(TemplateException.class)
    public ResponseEntity<ErrorResponse> handleTemplateException(TemplateException e) {

        ErrorCode code = e.getErrorCode();

        ErrorResponse body = new ErrorResponse(
                code.getCode(),
                code.getMessage()
        );

        return ResponseEntity.status(code.getStatus()).body(body);
    }

}

