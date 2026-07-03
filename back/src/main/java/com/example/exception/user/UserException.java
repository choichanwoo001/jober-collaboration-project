package com.example.exception.user;

import com.example.exception.base.BusinessException;

public class UserException extends BusinessException {
    public UserException(UserErrorCode errorCode) {
        super(errorCode);
    }
}
