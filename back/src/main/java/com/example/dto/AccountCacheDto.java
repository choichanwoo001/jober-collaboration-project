package com.example.dto;

import com.example.entity.Account;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

/**
 * Account 캐싱을 위한 경량 DTO
 * JwtAuthenticationFilter에서 실제로 사용하는 필드만 포함합니다.
 * - id: 계정 ID
 * - userName: 사용자 이름 (SecurityContext에 설정)
 * - email: 이메일 (UserDto 변환 시 필요)
 * - role: 권한 (SecurityContext에 설정)
 * - status: 계정 상태 (ACTIVE 체크용)
 * 
 * Redis 메모리 사용량을 최소화하고 직렬화/역직렬화 성능을 향상시킵니다.
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AccountCacheDto implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    private Long id;
    private String userName;
    private String email;
    private String role;
    private String status;
    
    /**
     * Account 엔티티에서 필요한 필드만 추출하여 AccountCacheDto로 변환
     */
    public static AccountCacheDto fromEntity(Account account) {
        if (account == null) {
            return null;
        }
        
        return AccountCacheDto.builder()
                .id(account.getId())
                .userName(account.getUserName())
                .email(account.getEmail())
                .role(account.getRole())
                .status(account.getStatus())
                .build();
    }
    
    /**
     * AccountCacheDto를 Account 엔티티로 변환
     * 주의: 필요한 필드만 설정되므로 완전한 Account 엔티티가 아닙니다.
     * JwtAuthenticationFilter에서만 사용하는 용도입니다.
     */
    public Account toEntity() {
        Account account = new Account();
        account.setId(this.id);
        account.setUserName(this.userName);
        account.setEmail(this.email);
        account.setRole(this.role);
        account.setStatus(this.status);
        return account;
    }
}
