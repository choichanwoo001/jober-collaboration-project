package com.example.service;

import com.example.config.JwtTokenProvider;
import com.example.entity.Account;
import com.example.exception.user.UserErrorCode;
import com.example.exception.user.UserException;
import com.example.repository.AccountRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
@Slf4j
public class TokenService {

    private final JwtTokenProvider jwtTokenProvider;
    private final AccountRepository accountRepository;
    private final RedisTemplate<String, String> redisTemplate;

    private static final String REFRESH_TOKEN_PREFIX = "refresh_token:";
    private static final String BLACKLIST_PREFIX = "blacklist:";

    /**
     * 토큰 쌍 생성 및 Redis에 Refresh Token 저장
     */
    public Map<String, String> generateTokenPair(Account account) {
        String accessToken = jwtTokenProvider.createAccessToken(
            account.getEmail(), account.getRole(), account.getId(), 
            account.getUserName());
        String refreshToken = jwtTokenProvider.createRefreshToken(
            account.getEmail(), account.getId());

        // Refresh Token을 Redis에 저장 (7일)
        String redisKey = REFRESH_TOKEN_PREFIX + account.getId();
        redisTemplate.opsForValue().set(redisKey, refreshToken, 7, TimeUnit.DAYS);

        Map<String, String> tokens = new HashMap<>();
        tokens.put("accessToken", accessToken);
        tokens.put("refreshToken", refreshToken);
        tokens.put("userId", account.getId().toString());
        tokens.put("role", account.getRole());
        tokens.put("userName", account.getUserName());
        return tokens;
    }

    /**
     * Refresh Token으로 새로운 Access Token 발급
     */
    public Map<String, String> refreshAccessToken(String refreshToken) {
        // Refresh Token 유효성 검사
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            log.info("[TOKEN] Invalid refresh token signature or claims.");
            throw new UserException(UserErrorCode.INVALID_TOKEN);
        }

        // 토큰 타입 확인
        String tokenType = jwtTokenProvider.getTokenType(refreshToken);
        if (!"refresh".equals(tokenType)) {
            log.warn("[TOKEN] Invalid token type. expected=refresh, actual={}", tokenType);
            throw new UserException(UserErrorCode.INVALID_TOKEN);
        }

        // 계정 ID 추출
        Long accountId = jwtTokenProvider.getAccountId(refreshToken);
        if (accountId == null) {
            log.error("[TOKEN] Account ID not found in refresh token claims.");
            throw new UserException(UserErrorCode.TOKEN_MISMATCH);
        }

        // Redis에서 Refresh Token 확인
        String redisKey = REFRESH_TOKEN_PREFIX + accountId;
        String storedRefreshToken = redisTemplate.opsForValue().get(redisKey);
        if (storedRefreshToken == null || !storedRefreshToken.equals(refreshToken)) {
            log.warn("[TOKEN] Refresh token not found in Redis. It may have expired or been logged out. accountId={}", accountId);
            throw new UserException(UserErrorCode.INVALID_TOKEN);
        }

        // 사용자 정보 조회
        Account account = accountRepository.findById(accountId)
            .orElseThrow(() -> {
                log.error("[TOKEN] User not found for accountId in token. The user may have been deleted. accountId={}", accountId);
                return new UserException(UserErrorCode.USER_NOT_FOUND);
            });

        // 새로운 Access Token 생성
        String newAccessToken = jwtTokenProvider.createAccessToken(
            account.getEmail(), account.getRole(), account.getId(),
            account.getUserName());

        Map<String, String> result = new HashMap<>();
        result.put("accessToken", newAccessToken);
        result.put("userId", account.getId().toString());
        result.put("role", account.getRole());
        result.put("userName", account.getUserName());
        return result;
    }

    /**
     * 로그아웃 - Refresh Token 삭제 및 Access Token 블랙리스트 추가
     */
    public void logout(String accessToken, String refreshToken) {
        // Refresh Token 삭제
        if (refreshToken != null && jwtTokenProvider.validateToken(refreshToken)) {
            Long accountId = jwtTokenProvider.getAccountId(refreshToken);
            if (accountId != null) {
                String redisKey = REFRESH_TOKEN_PREFIX + accountId;
                redisTemplate.delete(redisKey);
            }
        }

        // Access Token을 블랙리스트에 추가
        if (accessToken != null && jwtTokenProvider.validateToken(accessToken)) {
            String tokenId = jwtTokenProvider.getEmail(accessToken) + ":" + System.currentTimeMillis();
            String blacklistKey = BLACKLIST_PREFIX + tokenId;
            // Access Token의 남은 유효시간만큼 블랙리스트에 저장
            redisTemplate.opsForValue().set(blacklistKey, accessToken, 1, TimeUnit.HOURS);
        }
    }

    /**
     * 토큰이 블랙리스트에 있는지 확인
     */
    public boolean isTokenBlacklisted(String token) {
        // 간단한 구현: 토큰의 이메일로 블랙리스트 검색
        String email = jwtTokenProvider.getEmail(token);
        if (email == null) return false;

        // 실제로는 더 정교한 블랙리스트 관리가 필요
        return false; // 현재는 단순화
    }
}
