package com.example.controller;

import com.example.service.KakaoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 카카오 소셜 로그인 컨트롤러
 */
@Slf4j
@RestController
@RequestMapping("/api/auth/kakao")
@RequiredArgsConstructor
public class KakaoController {
    
    private final KakaoService kakaoService;
    
    /**
     * 카카오 로그인 콜백 처리
     * 프론트엔드에서 카카오 인가코드를 받아온 후 호출하는 엔드포인트
     */
    @PostMapping("/login")
    public ResponseEntity<Map<String, String>> kakaoLogin(@RequestParam("code") String authorizationCode) {
        log.info("카카오 로그인 요청 수신. 인가코드: {}", authorizationCode);
        
        try {
            Map<String, String> tokens = kakaoService.processKakaoLogin(authorizationCode);
            log.info("카카오 로그인 성공. 사용자ID: {}", tokens.get("userId"));
            
            return ResponseEntity.ok(tokens);
        } catch (Exception e) {
            log.error("카카오 로그인 실패", e);
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "카카오 로그인 실패: " + e.getMessage()));
        }
    }
    
    /**
     * 카카오 로그인 URL 생성
     * 프론트엔드에서 카카오 로그인 버튼 클릭 시 리다이렉트할 URL 제공
     */
    @GetMapping("/url")
    public ResponseEntity<Map<String, String>> getKakaoLoginUrl() {
        String kakaoAuthUrl = "https://kauth.kakao.com/oauth/authorize" +
                "?client_id=${KAKAO_CLIENT_ID}" +
                "&redirect_uri=${KAKAO_REDIRECT_URI:http://localhost:3000/auth/kakao/callback}" +
                "&response_type=code" +
                "&scope=profile_nickname,account_email";
        
        return ResponseEntity.ok(Map.of("url", kakaoAuthUrl));
    }
    
    /**
     * 카카오 OAuth2 콜백 엔드포인트
     * 카카오에서 인가코드를 리다이렉트로 보내주는 엔드포인트
     * (실제 운영에서는 프론트엔드로 리다이렉트하여 처리)
     */
    @GetMapping("/callback")
    public ResponseEntity<Map<String, String>> kakaoCallback(
            @RequestParam("code") String authorizationCode,
            @RequestParam(value = "error", required = false) String error) {
        
        if (error != null) {
            log.error("카카오 OAuth2 에러: {}", error);
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "카카오 인증 실패: " + error));
        }
        
        log.info("카카오 콜백 수신. 인가코드: {}", authorizationCode);
        
        try {
            Map<String, String> tokens = kakaoService.processKakaoLogin(authorizationCode);
            log.info("카카오 콜백 처리 성공. 사용자ID: {}", tokens.get("userId"));
            
            // 실제 서비스에서는 프론트엔드로 리다이렉트하여 토큰 전달
            return ResponseEntity.ok(tokens);
        } catch (Exception e) {
            log.error("카카오 콜백 처리 실패", e);
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "카카오 로그인 실패: " + e.getMessage()));
        }
    }
}