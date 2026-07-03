package com.example.service;

import com.example.dto.ForgotPasswordRequest;
import com.example.dto.ResetPasswordRequest;
import com.example.entity.Account;
import com.example.entity.PasswordResetToken;
import com.example.exception.user.UserErrorCode;
import com.example.exception.user.UserException;
import com.example.repository.AccountRepository;
import com.example.repository.PasswordResetTokenRepository;
import com.example.service.password.PasswordService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class PasswordResetService {

    private final AccountRepository accountRepository;
    private final PasswordResetTokenRepository tokenRepository;
    private final PasswordService passwordService;

    // 비밀번호 재설정 토큰 생성
    public String createPasswordResetToken(ForgotPasswordRequest request) {
        Account account = accountRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new UserException(UserErrorCode.USER_NOT_FOUND));

        String token = UUID.randomUUID().toString();
        PasswordResetToken resetToken = PasswordResetToken.builder()
                .account(account)
                .token(token)
                .expiryDate(LocalDateTime.now().plusMinutes(30)) // 30분 유효
                .build();

        tokenRepository.save(resetToken);

        // Postman 응답에서 확인 가능
        return token;
    }

    // 비밀번호 재설정
    @Transactional
    public void resetPassword(ResetPasswordRequest request) {
        PasswordResetToken resetToken = tokenRepository.findByToken(request.getToken())
                .orElseThrow(() -> new UserException(UserErrorCode.INVALID_TOKEN));

        if (resetToken.getExpiryDate().isBefore(LocalDateTime.now())) {
            throw new UserException(UserErrorCode.EXPIRED_TOKEN);
        }

        Account account = resetToken.getAccount();
        account.setPasswordHash(passwordService.encode(request.getNewPassword()));
        accountRepository.save(account);

        // 토큰은 한 번 쓰면 제거
        tokenRepository.delete(resetToken);
    }
}
