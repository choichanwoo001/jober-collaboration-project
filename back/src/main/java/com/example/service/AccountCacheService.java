package com.example.service;

import com.example.dto.AccountCacheDto;
import com.example.entity.Account;
import com.example.repository.AccountRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
@Slf4j
public class AccountCacheService {

    private final AccountRepository accountRepository;

    // DTO 전용 RedisTemplate
    private final RedisTemplate<String, AccountCacheDto> accountCacheRedisTemplate;

    private static final String ACCOUNT_CACHE_PREFIX = "account:";
    private static final long CACHE_TTL_MINUTES = 5;

    /**
     * Account 조회 (캐시 → DB fallback)
     */
    public Account getAccountById(Long accountId) {
        if (accountId == null) {
            return null;
        }

        String cacheKey = ACCOUNT_CACHE_PREFIX + accountId;

        try {
            // 1️⃣ 캐시 조회
            AccountCacheDto cachedDto =
                    accountCacheRedisTemplate.opsForValue().get(cacheKey);

            if (cachedDto != null) {
                log.debug("✅ Account 캐시 히트: accountId={}", accountId);
                return cachedDto.toEntity();
            }

            // 2️⃣ 캐시 미스 → DB 조회
            log.debug("❌ Account 캐시 미스: accountId={}, DB 조회", accountId);
            Account account = accountRepository.findById(accountId).orElse(null);

            if (account != null) {
                // 3️⃣ DTO 변환 후 캐싱
                AccountCacheDto dto = AccountCacheDto.fromEntity(account);
                accountCacheRedisTemplate.opsForValue().set(
                        cacheKey,
                        dto,
                        CACHE_TTL_MINUTES,
                        TimeUnit.MINUTES
                );

                log.debug("💾 Account 캐시 저장: accountId={}, TTL={}분",
                        accountId, CACHE_TTL_MINUTES);
            }

            return account;

        } catch (Exception e) {
            // 캐시 장애 시 DB fallback (중요)
            log.error("⚠️ Account 캐시 오류: accountId={}, DB fallback", accountId, e);
            return accountRepository.findById(accountId).orElse(null);
        }
    }

    /**
     * 캐시 무효화 (비밀번호 변경, 상태 변경 시)
     */
    public void evictAccountCache(Long accountId) {
        if (accountId == null) {
            return;
        }

        String cacheKey = ACCOUNT_CACHE_PREFIX + accountId;
        try {
            accountCacheRedisTemplate.delete(cacheKey);
            log.debug("Account 캐시 무효화: accountId={}", accountId);
        } catch (Exception e) {
            log.error("Account 캐시 무효화 실패: accountId={}", accountId, e);
        }
    }
}
