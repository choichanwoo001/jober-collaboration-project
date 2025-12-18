/**
 * 실제 인증/회원가입 로직
 */
package com.example.service;

import com.example.dto.LoginRequest;
import com.example.dto.SignupRequest;
import com.example.entity.Account;
import com.example.exception.user.UserErrorCode;
import com.example.exception.user.UserException;
import com.example.repository.AccountRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final AccountRepository accountRepository;
    private final PasswordEncoder passwordEncoder;
    private final TokenService tokenService;

    /**
     * 회원가입
     */
    @Transactional
    public Account registerUser(SignupRequest request) {
        if (accountRepository.existsByEmail(request.getEmail())) {
            throw new UserException(UserErrorCode.EMAIL_DUPLICATED);
        }
        if (accountRepository.existsByUserName(request.getUsername())) {
            throw new UserException(UserErrorCode.USER_ALREADY_EXISTS);
        }

        Account account = new Account();
        account.setUserName(request.getUsername());
        account.setEmail(request.getEmail());
        account.setPasswordHash(passwordEncoder.encode(request.getPassword()));

        // 기본값 세팅
        account.setRole("USER");
        account.setStatus("ACTIVE");

        return accountRepository.save(account);
    }

    /**
     * 로그인 - JWT 사용
     */
    @Transactional(readOnly = true)
    public Map<String, String> login(LoginRequest request) {
        Account account = accountRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new UserException(UserErrorCode.INVALID_EMAIL_PASSWORD));

        if (!passwordEncoder.matches(request.getPassword(), account.getPasswordHash())) {
            throw new UserException(UserErrorCode.INVALID_EMAIL_PASSWORD);
        }

        // TokenService를 통해 토큰 쌍 생성
        return tokenService.generateTokenPair(account);
    }
}
